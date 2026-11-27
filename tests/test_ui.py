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


if __name__ == "__main__":
    unittest.main()
