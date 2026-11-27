import importlib.machinery
import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "bin" / "steam-auto-ui"


def _load_ui_module():
    loader = importlib.machinery.SourceFileLoader("steam_auto_ui", str(UI))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class UiTests(unittest.TestCase):
    def test_help_and_check_mode(self):
        res_help = subprocess.run([str(UI), "--help"], text=True, capture_output=True, check=False)
        self.assertEqual(res_help.returncode, 0, res_help.stderr)
        self.assertIn("--gui", res_help.stdout)
        self.assertIn("--tui", res_help.stdout)
        self.assertIn("--check", res_help.stdout)

        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
            env["HOME"] = tmp
            env["XDG_CONFIG_HOME"] = f"{tmp}/.config"
            env["XDG_STATE_HOME"] = f"{tmp}/.local/state"
            res_check = subprocess.run(
                [str(UI), "--check"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_check.returncode, 0, res_check.stderr)
            payload = json.loads(res_check.stdout)
            self.assertEqual(payload["status"], "ok")
            self.assertTrue(payload["tc_parser_verified"])
            self.assertTrue(payload["mutual_exclusion_verified"])
            self.assertTrue(payload["curses_available"])

    def test_profile_validation_mutual_exclusion(self):
        ui = _load_ui_module()

        # FSR4 + vkBasalt -> disables vkBasalt
        norm, warns = ui.validate_profile({"USE_FSR4": "1", "USE_SHARPEN": "1"}, "standard")
        self.assertEqual(norm["USE_SHARPEN"], "0")
        self.assertTrue(any("vkBasalt" in w for w in warns))

        # OptiScaler + vkBasalt (even with FSR4=0) -> disables vkBasalt
        norm2, warns2 = ui.validate_profile({"USE_FSR4": "0", "USE_OPTISCALER": "1", "USE_SHARPEN": "1"}, "standard")
        self.assertEqual(norm2["USE_SHARPEN"], "0")
        self.assertTrue(warns2)

        # MLFG + VRR_CAP -> clears VRR_CAP
        norm3, warns3 = ui.validate_profile({"USE_MLFG": "1", "VRR_CAP": "165"}, "standard")
        self.assertEqual(norm3["VRR_CAP"], "")
        self.assertTrue(any("VRR_CAP" in w for w in warns3))

        # Anti-cheat disables MLFG, OptiScaler, vkBasalt
        norm4, warns4 = ui.validate_profile(
            {"USE_FSR4": "0", "USE_MLFG": "1", "USE_OPTISCALER": "1", "USE_SHARPEN": "1"},
            "competitive-anticheat",
        )
        self.assertEqual(norm4["USE_MLFG"], "0")
        self.assertEqual(norm4["USE_OPTISCALER"], "0")
        self.assertEqual(norm4["USE_SHARPEN"], "0")
        self.assertGreaterEqual(len(warns4), 3)

    def test_backend_profile_safe_mode_and_log_parsing(self):
        ui = _load_ui_module()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            orig_cfg = os.environ.get("XDG_CONFIG_HOME")
            orig_state = os.environ.get("XDG_STATE_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
            os.environ["XDG_STATE_HOME"] = str(home / ".local" / "state")
            try:
                backend = ui.ProfilerBackend(home=home)
                path, _ = backend.save_profile("361420", {"USE_FSR4": "0", "USE_SHARPEN": "1", "USE_SDL": "1"})
                self.assertTrue(path.is_file())
                loaded = backend.load_profile("361420")
                self.assertEqual(loaded["USE_FSR4"], "0")
                self.assertEqual(loaded["USE_SHARPEN"], "1")
                self.assertEqual(loaded["USE_SDL"], "1")

                # Safe mode sets XWayland + SafeDX12 while preserving USE_SDL
                backend.apply_safe_mode("361420")
                safe = backend.load_profile("361420")
                self.assertEqual(safe["USE_XWAYLAND"], "1")
                self.assertEqual(safe["USE_SAFEDX12"], "1")
                self.assertEqual(safe["USE_SDL"], "1")

                # Log parsing extracts appid + crash_hint
                backend.state_dir.mkdir(parents=True, exist_ok=True)
                log_file = backend.state_dir / "last-361420.log"
                log_file.write_text(
                    "appid=361420\n"
                    "duration_sec=4\n"
                    "exit_code=1\n"
                    "crash_hint=fast_crash_detected duration=4s exit_code=1 suggested_safe_mode=USE_XWAYLAND=1,USE_SAFEDX12=1\n",
                    encoding="utf-8",
                )
                logs = backend.list_logs()
                self.assertEqual(len(logs), 1)
                parsed_log = backend.read_log(logs[0])
                self.assertEqual(parsed_log["appid"], "361420")
                self.assertIn("fast_crash_detected", parsed_log["crash_hint"])

                backend.reset_profile("361420")
                self.assertFalse(path.exists())
            finally:
                if orig_cfg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = orig_cfg
                if orig_state is None:
                    os.environ.pop("XDG_STATE_HOME", None)
                else:
                    os.environ["XDG_STATE_HOME"] = orig_state

    def test_tc_qdisc_lan_wan_parser(self):
        ui = _load_ui_module()
        raw = (
            "qdisc htb 1: root refcnt 2 r2q 10 default 0x20\n"
            " Sent 2000 bytes 20 pkt (dropped 0, overlimits 0 requeues 0)\n"
            "qdisc cake 10: parent 1:10 bandwidth unlimited diffserv4\n"
            " Sent 1000 bytes 10 pkt (dropped 0, overlimits 0 requeues 0)\n"
            "  av_delay        15us        9us        3us        1us\n"
            "qdisc cake 20: parent 1:20 bandwidth 450Mbit diffserv4\n"
            " Sent 4096 bytes 40 pkt (dropped 2, overlimits 0 requeues 0)\n"
            "  av_delay       920us      310us      120us       50us\n"
        )
        parsed = ui.parse_tc_qdisc_stats(raw)
        self.assertEqual(parsed["lan"]["handle"], "10:")
        self.assertEqual(parsed["lan"]["sent_bytes"], 1000)
        self.assertEqual(parsed["lan"]["av_delay"][0], "15us")
        self.assertEqual(parsed["wan"]["handle"], "20:")
        self.assertEqual(parsed["wan"]["dropped"], 2)
        self.assertEqual(parsed["wan"]["av_delay"][0], "920us")

    def test_shortcuts_vdf_parser_and_profile_editing(self):
        import struct

        ui = _load_ui_module()

        def pack_str(k: str, v: str) -> bytes:
            return b"\x01" + k.encode() + b"\x00" + v.encode() + b"\x00"

        def pack_u32(k: str, v: int) -> bytes:
            return b"\x02" + k.encode() + b"\x00" + struct.pack("<I", v)

        vdf_bytes = (
            b"\x00shortcuts\x00"
            + b"\x000\x00"
            + pack_u32("appid", 3333333333)
            + pack_str("AppName", "Modded VR Title")
            + pack_str("Exe", '"/opt/mod/game.exe"')
            + pack_str("StartDir", '"/opt/mod"')
            + pack_str("LaunchOptions", "vr-run %command% -vr")
            + b"\x08"
            + b"\x08"
        )
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            vdf = home / ".local" / "share" / "Steam" / "userdata" / "100" / "config" / "shortcuts.vdf"
            vdf.parent.mkdir(parents=True)
            (home / ".local" / "share" / "Steam" / "steamapps").mkdir(parents=True)
            vdf.write_bytes(vdf_bytes)

            parsed = ui.parse_shortcuts_vdf(vdf)
            self.assertEqual(len(parsed), 1)
            self.assertEqual(parsed[0]["appid"], "3333333333")
            self.assertEqual(parsed[0]["name"], "Modded VR Title")
            self.assertEqual(parsed[0]["source"], "shortcut")

            # Truncated binary VDF must not crash
            broken = home / "broken.vdf"
            broken.write_bytes(b"\x00shortcuts\x00\x000\x00\x02appid\x00\x01")
            self.assertIsInstance(ui.parse_shortcuts_vdf(broken), list)

            orig_cfg = os.environ.get("XDG_CONFIG_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
            try:
                backend = ui.ProfilerBackend(home=home)
                games = backend.discover_games()
                self.assertEqual(len(games), 1)
                self.assertEqual(games[0]["source"], "shortcut")
                self.assertEqual(games[0]["synced"], "VR")
                backend.save_profile("3333333333", {"AUTO_HDR_SWITCH": "1", "USE_FSR4": "1"})
                self.assertEqual(backend.load_profile("3333333333")["AUTO_HDR_SWITCH"], "1")
                self.assertEqual(vdf.read_bytes(), vdf_bytes)
            finally:
                if orig_cfg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = orig_cfg

    def test_benchmarks_and_stack_watchdog(self):
        ui = _load_ui_module()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            orig_cfg = os.environ.get("XDG_CONFIG_HOME")
            orig_cache = os.environ.get("XDG_CACHE_HOME")
            os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
            os.environ["XDG_CACHE_HOME"] = str(home / ".cache")
            try:
                backend = ui.ProfilerBackend(home=home)
                backend.benchmark_dir.mkdir(parents=True, exist_ok=True)
                (backend.benchmark_dir / "361420.json").write_text(
                    json.dumps([
                        {
                            "timestamp": "2026-11-27T10:00:00+00:00",
                            "appid": "361420",
                            "avg_fps": 142.5,
                            "low_1pct_fps": 98.2,
                            "p99_frametime_ms": 10.4,
                            "samples": 6000,
                            "fsr4": True,
                            "mlfg": False,
                            "xwayland": False,
                            "safedx12": False,
                            "vrr_cap": 240,
                        }
                    ]),
                    encoding="utf-8",
                )
                runs = backend.list_benchmarks("361420")
                self.assertEqual(len(runs), 1)
                table_txt = backend.format_benchmarks_text(runs)
                self.assertIn("142.5", table_txt)
                self.assertIn("98.2", table_txt)
                self.assertIn("10.40", table_txt)

                # Shader cache usage measurement
                sc_dir = home / ".cache" / "mesa_shader_cache_sf"
                sc_dir.mkdir(parents=True)
                (sc_dir / "foz_cache.foz").write_bytes(b"x" * 2048)
                cache_info = backend.measure_shader_cache()
                self.assertEqual(cache_info["total_bytes"], 2048)
                self.assertEqual(cache_info["file_count"], 1)

                # Pacman downgrade & git revision regression watchdog
                paclog = home / "pacman.log"
                paclog.write_text(
                    "[2026-11-26T12:00:00+0200] [ALPM] downgraded mesa-git (27.0.0_devel.235000.aaa-1 -> 27.0.0_devel.234800.bbb-1)\n"
                    "[2026-11-26T12:05:00+0200] [ALPM] upgraded xrizer-git (0.6.r12.gabc-1 -> 0.6.r8.gdef-1)\n",
                    encoding="utf-8",
                )
                warns = ui.detect_pacman_downgrades(paclog)
                self.assertEqual(len(warns), 2)
                self.assertIn("mesa-git", warns[0])
                self.assertIn("xrizer-git", warns[1])
            finally:
                if orig_cfg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = orig_cfg
                if orig_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = orig_cache


if __name__ == "__main__":
    unittest.main()
