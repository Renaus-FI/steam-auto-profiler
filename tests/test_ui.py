import importlib.machinery
import importlib.util
import json
import os
import signal
import subprocess
import sys
import tempfile
import threading
import time
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

        # Anti-cheat disables MLFG, OptiScaler, vkBasalt, Reflex -> Anti-Lag 2 (preserves Native Anti-Lag & Transfer Queue)
        norm4, warns4 = ui.validate_profile(
            {
                "USE_FSR4": "0",
                "USE_MLFG": "1",
                "USE_OPTISCALER": "1",
                "USE_SHARPEN": "1",
                "USE_REFLEX_LAYER": "1",
                "USE_NATIVE_ANTILAG": "1",
                "USE_TRANSFER_QUEUE": "1",
            },
            "competitive-anticheat",
        )
        self.assertEqual(norm4["USE_MLFG"], "0")
        self.assertEqual(norm4["USE_OPTISCALER"], "0")
        self.assertEqual(norm4["USE_SHARPEN"], "0")
        self.assertEqual(norm4["USE_REFLEX_LAYER"], "0")
        self.assertEqual(norm4["USE_NATIVE_ANTILAG"], "1")
        self.assertEqual(norm4["USE_TRANSFER_QUEUE"], "1")
        self.assertGreaterEqual(len(warns4), 4)

        # MLFG + Reflex -> Anti-Lag 2 disables USE_REFLEX_LAYER
        norm5, warns5 = ui.validate_profile(
            {"USE_MLFG": "1", "USE_REFLEX_LAYER": "1", "USE_TRANSFER_QUEUE": "1"},
            "standard",
        )
        self.assertEqual(norm5["USE_REFLEX_LAYER"], "0")
        self.assertEqual(norm5["USE_TRANSFER_QUEUE"], "1")
        self.assertTrue(any("Reflex" in w for w in warns5))

        # Verify all Mesa 27 / Proton 11 / Bleeding-Edge / Steam Controller toggles exist in PROFILE_TOGGLES and all 27 languages
        toggle_keys = {k for k, _ in ui.PROFILE_TOGGLES}
        for new_key in (
            "USE_TRANSFER_QUEUE",
            "USE_NATIVE_ANTILAG",
            "USE_REFLEX_LAYER",
            "USE_VK_VIDEO_DECODE",
            "USE_BLEEDING_EDGE",
            "USE_STEAM_CONTROLLER",
        ):
            self.assertIn(new_key, toggle_keys)
            for lang_code, _ in ui.SUPPORTED_LANGUAGES:
                label = ui.tr(lang_code, f"toggle_{new_key}")
                self.assertNotEqual(label, f"toggle_{new_key}")
                self.assertTrue(label.strip())

        # Ultra Bleeding-Edge disables vkBasalt on standard titles and is blocked on competitive-anticheat
        be_std, be_warns = ui.validate_profile(
            {"USE_BLEEDING_EDGE": "1", "USE_FSR4": "0", "USE_SHARPEN": "1", "USE_STEAM_CONTROLLER": "1"},
            "standard",
        )
        self.assertEqual(be_std["USE_BLEEDING_EDGE"], "1")
        self.assertEqual(be_std["USE_SHARPEN"], "0")
        self.assertEqual(be_std["USE_STEAM_CONTROLLER"], "wayland-hdr")
        self.assertTrue(any("vkBasalt" in w for w in be_warns))

        # 4-mode Steam Controller 2026 normalization + legacy 1/0 compatibility
        for raw_val, expected in (
            ("auto", "auto"),
            ("wayland-hdr", "wayland-hdr"),
            ("xwayland", "xwayland"),
            ("off", "off"),
            ("1", "wayland-hdr"),
            ("0", "off"),
        ):
            sc_norm, _ = ui.validate_profile({"USE_STEAM_CONTROLLER": raw_val}, "standard")
            self.assertEqual(sc_norm["USE_STEAM_CONTROLLER"], expected)

        # Verify all 4 Steam Controller mode labels exist in all 27 UI languages
        for sc_key in ("sc_mode_auto", "sc_mode_wayland_hdr", "sc_mode_xwayland", "sc_mode_off"):
            for lang_code, _ in ui.SUPPORTED_LANGUAGES:
                val = ui.tr(lang_code, sc_key)
                self.assertNotEqual(val, sc_key)
                self.assertTrue(val.strip())

        be_ac, be_ac_warns = ui.validate_profile({"USE_BLEEDING_EDGE": "1"}, "competitive-anticheat")
        self.assertEqual(be_ac["USE_BLEEDING_EDGE"], "0")
        self.assertTrue(any("Bleeding-Edge" in w for w in be_ac_warns))

        # AppID 594650 (Hunt: Showdown 1896) enforces safe CryEngine/EAC profile
        hunt_norm, hunt_warns = ui.validate_profile(
            {"USE_XWAYLAND": "0", "USE_SAFEDX12": "0", "USE_MLFG": "1", "USE_BLEEDING_EDGE": "1"},
            "standard",
            appid="594650",
        )
        self.assertEqual(hunt_norm["USE_XWAYLAND"], "1")
        self.assertEqual(hunt_norm["USE_SAFEDX12"], "1")
        self.assertEqual(hunt_norm["USE_MLFG"], "0")
        self.assertEqual(hunt_norm["USE_BLEEDING_EDGE"], "0")
        self.assertEqual(hunt_norm["USE_NET_OPT"], "1")
        self.assertTrue(any("594650" in w for w in hunt_warns))

        # v2.4.0: AFMF mutual exclusion with MLFG and hard locks on competitive-anticheat, 594650, and VR
        afmf_mlfg, afmf_mlfg_warns = ui.validate_profile({"USE_MLFG": "1", "USE_AFMF": "1"}, "standard")
        self.assertEqual(afmf_mlfg["USE_MLFG"], "1")
        self.assertEqual(afmf_mlfg["USE_AFMF"], "0")
        self.assertTrue(any("AFMF" in w for w in afmf_mlfg_warns))

        afmf_ac, afmf_ac_warns = ui.validate_profile({"USE_AFMF": "1"}, "competitive-anticheat")
        self.assertEqual(afmf_ac["USE_AFMF"], "0")
        self.assertTrue(any("AFMF" in w for w in afmf_ac_warns))

        afmf_hunt, _ = ui.validate_profile({"USE_AFMF": "1"}, "standard", appid="594650")
        self.assertEqual(afmf_hunt["USE_AFMF"], "0")

        afmf_vr, afmf_vr_warns = ui.validate_profile({"USE_AFMF": "1", "USE_MLFG": "1"}, "vr")
        self.assertEqual(afmf_vr["USE_AFMF"], "0")
        self.assertEqual(afmf_vr["USE_MLFG"], "0")
        self.assertGreaterEqual(len(afmf_vr_warns), 2)

    def test_v24_afmf_smart_defaults_reset_and_safe_mode_in_ui_backend(self):
        ui = _load_ui_module()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            layer_dir = home / "vk-layers"
            layer_dir.mkdir()
            fake_so = home / "libafmf-linux.so"
            fake_so.write_bytes(b"\x7fELF")
            (layer_dir / "afmf-linux.json").write_text(
                json.dumps({
                    "file_format_version": "1.0.0",
                    "layer": {
                        "name": "VK_LAYER_AFMF",
                        "type": "GLOBAL",
                        "library_path": str(fake_so),
                        "enable_environment": {"AFMF_ENABLE": "1"},
                    },
                }),
                encoding="utf-8",
            )
            empty_dir = home / "vk-empty"
            empty_dir.mkdir()

            steamapps = home / ".local/share/Steam/steamapps"
            gdir = steamapps / "common/AFMF_Test_Game"
            gdir.mkdir(parents=True)
            (gdir / "game.exe").touch()
            (gdir / "d3d12.dll").touch()
            (steamapps / "appmanifest_991001.acf").write_text(
                '"AppState"\n{\n\t"appid"\t\t"991001"\n\t"installdir"\t\t"AFMF_Test_Game"\n\t"name"\t\t"AFMF Test Game"\n}\n',
                encoding="utf-8",
            )

            orig_env = {k: os.environ.get(k) for k in ("XDG_CONFIG_HOME", "XDG_STATE_HOME", "SAP_AFMF_LAYER_DIRS")}
            os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
            os.environ["XDG_STATE_HOME"] = str(home / ".local" / "state")
            os.environ["SAP_AFMF_LAYER_DIRS"] = str(layer_dir)
            try:
                backend = ui.ProfilerBackend(home=home)
                # Installed afmf-linux -> USE_AFMF=1 on standard 3D title
                prof_on = backend.load_profile("991001")
                self.assertEqual(prof_on["USE_AFMF"], "1")

                # Explicit save USE_AFMF=0 wins, and Reset Profile restores USE_AFMF=1
                backend.save_profile("991001", {"USE_AFMF": "0"}, "standard")
                self.assertEqual(backend.load_profile("991001")["USE_AFMF"], "0")
                backend.reset_profile("991001")
                self.assertEqual(backend.load_profile("991001")["USE_AFMF"], "1")

                # Safe mode disables USE_AFMF
                backend.apply_safe_mode("991001")
                self.assertEqual(backend.load_profile("991001")["USE_AFMF"], "0")

                # Anti-cheat (594650 / 2357570) stays USE_AFMF=0
                self.assertEqual(backend.load_profile("594650")["USE_AFMF"], "0")
                self.assertEqual(backend.load_profile("2357570")["USE_AFMF"], "0")

                # Absent afmf-linux -> USE_AFMF=0 on reset
                backend.reset_profile("991001")
                os.environ["SAP_AFMF_LAYER_DIRS"] = str(empty_dir)
                self.assertEqual(backend.load_profile("991001")["USE_AFMF"], "0")
            finally:
                for k, v in orig_env.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

    def test_hunt_compat_tool_diagnostic_in_ui_backend(self):
        ui = _load_ui_module()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            cfg_vdf = home / ".local" / "share" / "Steam" / "config" / "config.vdf"
            cfg_vdf.parent.mkdir(parents=True)
            backend = ui.ProfilerBackend(home=home)

            # Unset 594650 -> warning
            cfg_vdf.write_text(
                '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
                '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t\t"0"\n\t\t\t\t\t{\n'
                '\t\t\t\t\t\t"name"\t\t"proton-cachyos-slr"\n\t\t\t\t\t}\n\t\t\t\t}\n'
                '\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            res_unset = backend.check_hunt_compat_tool()
            self.assertTrue(res_unset["found"])
            self.assertIsNotNone(res_unset["warning"])
            self.assertIn("Proton 11.0-2", res_unset["warning"])

            # proton-cachyos-slr -> warning
            cfg_vdf.write_text(
                '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
                '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t\t"594650"\n\t\t\t\t\t{\n'
                '\t\t\t\t\t\t"name"\t\t"proton-cachyos-slr"\n\t\t\t\t\t}\n\t\t\t\t}\n'
                '\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            res_cachy = backend.check_hunt_compat_tool()
            self.assertEqual(res_cachy["tool"], "proton-cachyos-slr")
            self.assertIsNotNone(res_cachy["warning"])
            self.assertIn("Proton Hotfix", res_cachy["warning"])

            # Valve Proton 11 -> no warning
            cfg_vdf.write_text(
                '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
                '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t\t"594650"\n\t\t\t\t\t{\n'
                '\t\t\t\t\t\t"name"\t\t"proton_11"\n\t\t\t\t\t}\n\t\t\t\t}\n'
                '\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            res_ok = backend.check_hunt_compat_tool()
            self.assertEqual(res_ok["tool"], "proton_11")
            self.assertIsNone(res_ok["warning"])

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

                # Safe mode sets XWayland + SafeDX12 and disables bleeding-edge/experimental flags while preserving USE_SDL
                backend.apply_safe_mode("361420")
                safe = backend.load_profile("361420")
                self.assertEqual(safe["USE_XWAYLAND"], "1")
                self.assertEqual(safe["USE_SAFEDX12"], "1")
                self.assertEqual(safe["USE_BLEEDING_EDGE"], "0")
                self.assertEqual(safe["USE_TRANSFER_QUEUE"], "0")
                self.assertEqual(safe["USE_REFLEX_LAYER"], "0")
                self.assertEqual(safe["USE_VK_VIDEO_DECODE"], "0")
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

    def test_load_profile_smart_defaults_inheritance_and_reset(self):
        ui = _load_ui_module()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            drm = home / "drm-rdna4"
            dev = drm / "card0" / "device"
            dev.mkdir(parents=True)
            (dev / "vendor").write_text("0x1002\n", encoding="utf-8")
            (dev / "device").write_text("0x7550\n", encoding="utf-8")
            (dev / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

            steamapps = home / ".local/share/Steam/steamapps"
            fh_dir = steamapps / "common/Forza_Horizon_6"
            fh_dir.mkdir(parents=True)
            (fh_dir / "ForzaHorizon6.exe").touch()
            (fh_dir / "sl.reflex.dll").touch()
            (fh_dir / "amd_fidelityfx_upscaler_dx12.dll").touch()
            (steamapps / "appmanifest_990001.acf").write_text(
                '"AppState"\n{\n\t"appid"\t\t"990001"\n\t"installdir"\t\t"Forza_Horizon_6"\n\t"name"\t\t"Forza Horizon 6"\n}\n',
                encoding="utf-8",
            )

            orig_env = {k: os.environ.get(k) for k in ("XDG_CONFIG_HOME", "SAP_DRM_DIR")}
            os.environ["XDG_CONFIG_HOME"] = str(home / ".config")
            os.environ["SAP_DRM_DIR"] = str(drm)
            try:
                backend = ui.ProfilerBackend(home=home)

                # Non-anticheat RDNA 4 title with Reflex DLL loads smart defaults ON
                fh_prof = backend.load_profile("990001")
                self.assertEqual(fh_prof["USE_BLEEDING_EDGE"], "1")
                self.assertEqual(fh_prof["USE_TRANSFER_QUEUE"], "1")
                self.assertEqual(fh_prof["USE_NATIVE_ANTILAG"], "1")
                self.assertEqual(fh_prof["USE_VK_VIDEO_DECODE"], "1")
                self.assertEqual(fh_prof["USE_REFLEX_LAYER"], "1")
                self.assertEqual(fh_prof["USE_MLFG"], "0")
                self.assertEqual(fh_prof["USE_OPTISCALER"], "0")

                # Competitive anti-cheat titles (Hunt 594650, Overwatch 2357570) disable BLEEDING_EDGE & REFLEX_LAYER
                hunt_prof = backend.load_profile("594650")
                self.assertEqual(hunt_prof["USE_BLEEDING_EDGE"], "0")
                self.assertEqual(hunt_prof["USE_REFLEX_LAYER"], "0")
                self.assertEqual(hunt_prof["USE_XWAYLAND"], "1")
                self.assertEqual(hunt_prof["USE_SAFEDX12"], "1")
                self.assertEqual(hunt_prof["USE_TRANSFER_QUEUE"], "1")
                self.assertEqual(hunt_prof["USE_NATIVE_ANTILAG"], "1")
                self.assertEqual(hunt_prof["USE_VK_VIDEO_DECODE"], "1")

                ow_prof = backend.load_profile("2357570")
                self.assertEqual(ow_prof["USE_BLEEDING_EDGE"], "0")
                self.assertEqual(ow_prof["USE_REFLEX_LAYER"], "0")
                self.assertEqual(ow_prof["USE_TRANSFER_QUEUE"], "1")
                self.assertEqual(ow_prof["USE_NATIVE_ANTILAG"], "1")
                self.assertEqual(ow_prof["USE_VK_VIDEO_DECODE"], "1")

                # Forza Horizon 6 (2483190) RDNA 4 stability guard keeps Wayland/FSR4/Native Anti-Lag while disabling compute-ring hang flags
                fh6_prof = backend.load_profile("2483190")
                self.assertEqual(fh6_prof["USE_BLEEDING_EDGE"], "0")
                self.assertEqual(fh6_prof["USE_TRANSFER_QUEUE"], "0")
                self.assertEqual(fh6_prof["USE_REFLEX_LAYER"], "0")
                self.assertEqual(fh6_prof["USE_VK_VIDEO_DECODE"], "0")
                self.assertEqual(fh6_prof["USE_AFMF"], "0")
                self.assertEqual(fh6_prof["USE_OPTISCALER"], "0")
                self.assertEqual(fh6_prof["USE_NATIVE_ANTILAG"], "1")
                fh6_norm, fh6_warns = ui.validate_profile(
                    {"USE_BLEEDING_EDGE": "1", "USE_TRANSFER_QUEUE": "1", "USE_REFLEX_LAYER": "1", "USE_VK_VIDEO_DECODE": "1"},
                    game_class="native-fsr4",
                    appid="2483190",
                )
                self.assertEqual(fh6_norm["USE_BLEEDING_EDGE"], "0")
                self.assertEqual(fh6_norm["USE_TRANSFER_QUEUE"], "0")
                self.assertEqual(fh6_norm["USE_REFLEX_LAYER"], "0")
                self.assertEqual(fh6_norm["USE_VK_VIDEO_DECODE"], "0")
                self.assertTrue(any("2483190" in w for w in fh6_warns))

                # Legacy .env missing new keys inherits smart defaults; explicit =0 overrides them
                backend.profile_dir.mkdir(parents=True, exist_ok=True)
                (backend.profile_dir / "990001.env").write_text("USE_SDL=1\n", encoding="utf-8")
                inherited = backend.load_profile("990001")
                self.assertEqual(inherited["USE_SDL"], "1")
                self.assertEqual(inherited["USE_BLEEDING_EDGE"], "1")
                self.assertEqual(inherited["USE_TRANSFER_QUEUE"], "1")
                self.assertEqual(inherited["USE_VK_VIDEO_DECODE"], "1")

                (backend.profile_dir / "990001.env").write_text("USE_BLEEDING_EDGE=0\nUSE_TRANSFER_QUEUE=0\n", encoding="utf-8")
                overridden = backend.load_profile("990001")
                self.assertEqual(overridden["USE_BLEEDING_EDGE"], "0")
                self.assertEqual(overridden["USE_TRANSFER_QUEUE"], "0")
                self.assertEqual(overridden["USE_NATIVE_ANTILAG"], "1")

                # Reset Profile restores smart defaults immediately
                backend.reset_profile("990001")
                reloaded = backend.load_profile("990001")
                self.assertEqual(reloaded["USE_BLEEDING_EDGE"], "1")
                self.assertEqual(reloaded["USE_TRANSFER_QUEUE"], "1")

                # discover_games() populates smart_defaults for fast zero-subprocess load_profile(appid, game=...)
                games = backend.discover_games()
                self.assertEqual(len(games), 1)
                from_game = backend.load_profile("990001", game=games[0])
                self.assertEqual(from_game["USE_BLEEDING_EDGE"], "1")
                self.assertEqual(from_game["USE_REFLEX_LAYER"], "1")
                self.assertEqual(from_game["USE_VK_VIDEO_DECODE"], "1")

                # v2.3.0: Legacy-upscaler RDNA 4 title loads USE_OPTISCALER=1 & AUTO_HDR_SWITCH=1 on Wayland+kscreen-doctor
                leg_dir = steamapps / "common/Legacy_DLSS_Game"
                leg_dir.mkdir(parents=True)
                (leg_dir / "game.exe").touch()
                (leg_dir / "nvngx_dlss.dll").touch()
                (steamapps / "appmanifest_990002.acf").write_text(
                    '"AppState"\n{\n\t"appid"\t\t"990002"\n\t"installdir"\t\t"Legacy_DLSS_Game"\n\t"name"\t\t"Legacy DLSS Game"\n}\n',
                    encoding="utf-8",
                )
                mock_ks_bin = home / "mock-ks-bin"
                mock_ks_bin.mkdir()
                ks = mock_ks_bin / "kscreen-doctor"
                ks.write_text("#!/bin/sh\necho 'Output: 1 DP-1'\n", encoding="utf-8")
                ks.chmod(0o755)
                orig_wl = os.environ.get("WAYLAND_DISPLAY")
                orig_path = os.environ.get("PATH", "")
                orig_nohdr = os.environ.get("DXVK_NO_HDR")
                os.environ["WAYLAND_DISPLAY"] = "wayland-0"
                os.environ["PATH"] = f"{mock_ks_bin}:{orig_path}"
                os.environ.pop("DXVK_NO_HDR", None)
                try:
                    leg_prof = backend.load_profile("990002")
                    self.assertEqual(leg_prof["USE_OPTISCALER"], "1")
                    self.assertEqual(leg_prof["AUTO_HDR_SWITCH"], "1")
                    # Explicit saved overrides win, and Reset Profile restores smart defaults + clears recovery state
                    backend.save_profile("990002", {"USE_OPTISCALER": "0", "AUTO_HDR_SWITCH": "0"}, "legacy-upscaler")
                    saved_leg = backend.load_profile("990002")
                    self.assertEqual(saved_leg["USE_OPTISCALER"], "0")
                    self.assertEqual(saved_leg["AUTO_HDR_SWITCH"], "0")
                    backend.state_dir.mkdir(parents=True, exist_ok=True)
                    rec_file = backend.state_dir / "recovery-990002.state"
                    rec_file.write_text("RECOVERY_STAGE=2\n", encoding="utf-8")
                    backend.reset_profile("990002")
                    self.assertFalse(rec_file.exists())
                    reset_leg = backend.load_profile("990002")
                    self.assertEqual(reset_leg["USE_OPTISCALER"], "1")
                    self.assertEqual(reset_leg["AUTO_HDR_SWITCH"], "1")
                    # Hunt 594650 keeps USE_OPTISCALER=0 and AUTO_HDR_SWITCH=0
                    hunt_v23 = backend.load_profile("594650")
                    self.assertEqual(hunt_v23["USE_OPTISCALER"], "0")
                    self.assertEqual(hunt_v23["AUTO_HDR_SWITCH"], "0")
                finally:
                    if orig_wl is None:
                        os.environ.pop("WAYLAND_DISPLAY", None)
                    else:
                        os.environ["WAYLAND_DISPLAY"] = orig_wl
                    os.environ["PATH"] = orig_path
                    if orig_nohdr is not None:
                        os.environ["DXVK_NO_HDR"] = orig_nohdr
            finally:
                for k, v in orig_env.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v

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
                # Second call within 30s returns cached results cleanly
                warns_cached = ui.detect_pacman_downgrades(paclog)
                self.assertEqual(warns_cached, warns)

                # Batched pacman -Q query runs in a single subprocess invocation
                mock_bin = home / "mock-bin"
                mock_bin.mkdir()
                call_log = home / "pacman.calls"
                pacman_mock = mock_bin / "pacman"
                pacman_mock.write_text(
                    "#!/bin/sh\n"
                    f'echo "$*" >> "{call_log}"\n'
                    'echo "mesa-git 27.0.0_devel.234834-1"\n'
                    'echo "mesa-git 27.0.0_devel.234834-1"\n'
                    'echo "mangohud 0.8.4-1.1"\n'
                    'echo "error: package \'xrizer\' was not found" >&2\n'
                    "exit 1\n",
                    encoding="utf-8",
                )
                pacman_mock.chmod(0o755)
                orig_path = os.environ.get("PATH", "")
                os.environ["PATH"] = f"{mock_bin}:{orig_path}"
                try:
                    versions = backend.collect_stack_versions()
                finally:
                    os.environ["PATH"] = orig_path
                self.assertEqual(len(call_log.read_text(encoding="utf-8").splitlines()), 1)
                self.assertEqual(
                    versions,
                    [("mesa-git", "27.0.0_devel.234834-1"), ("mangohud", "0.8.4-1.1")],
                )
            finally:
                if orig_cfg is None:
                    os.environ.pop("XDG_CONFIG_HOME", None)
                else:
                    os.environ["XDG_CONFIG_HOME"] = orig_cfg
                if orig_cache is None:
                    os.environ.pop("XDG_CACHE_HOME", None)
                else:
                    os.environ["XDG_CACHE_HOME"] = orig_cache

    def test_backend_cancellation_stops_pending_work_and_subprocesses(self):
        ui = _load_ui_module()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steamapps = home / ".local" / "share" / "Steam" / "steamapps"
            steamapps.mkdir(parents=True)
            for i in range(8):
                appid = 900000 + i
                (steamapps / f"appmanifest_{appid}.acf").write_text(
                    f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t"Slow Game {i}"\n}}\n',
                    encoding="utf-8",
                )

            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            calls_file = home / "detect.calls"
            detect_mock = mock_bin / "steam-auto-detect"
            detect_mock.write_text(
                "#!/bin/sh\n"
                f'echo "$*" >> "{calls_file}"\n'
                "sleep 20\n"
                'echo \'{"class":"standard","is_vr":false}\'\n',
                encoding="utf-8",
            )
            detect_mock.chmod(0o755)

            run_mock = mock_bin / "steam-auto-run"
            run_mock.write_text(
                "#!/bin/sh\n"
                "sleep 20\n"
                'echo "doctor ok"\n',
                encoding="utf-8",
            )
            run_mock.chmod(0o755)

            backend = ui.ProfilerBackend(home=home)
            backend.script_dir = mock_bin

            games_result: list[list[dict]] = []
            telemetry_result: list[dict] = []

            t_games = threading.Thread(
                target=lambda: games_result.append(backend.discover_games()),
                daemon=True,
            )
            t_tel = threading.Thread(
                target=lambda: telemetry_result.append(backend.collect_telemetry()),
                daemon=True,
            )
            t_games.start()
            t_tel.start()

            # Wait until slow child processes have actually spawned
            deadline = time.monotonic() + 3.0
            while time.monotonic() < deadline:
                if calls_file.is_file() and calls_file.read_text(encoding="utf-8").strip():
                    with backend._proc_lock:
                        if backend._active_procs:
                            break
                time.sleep(0.02)

            start_cancel = time.monotonic()
            backend.cancel()
            t_games.join(timeout=2.0)
            t_tel.join(timeout=2.0)
            elapsed = time.monotonic() - start_cancel

            self.assertFalse(t_games.is_alive(), "discover_games did not stop promptly after cancel()")
            self.assertFalse(t_tel.is_alive(), "collect_telemetry did not stop promptly after cancel()")
            self.assertLess(elapsed, 2.0)
            self.assertTrue(backend.is_cancelled())
            self.assertEqual(games_result, [[]])
            self.assertEqual(len(telemetry_result), 1)
            with backend._proc_lock:
                self.assertEqual(len(backend._active_procs), 0)
            invocations = calls_file.read_text(encoding="utf-8").splitlines()
            self.assertGreaterEqual(len(invocations), 1)
            self.assertLess(len(invocations), 8)

    def test_qt_gui_exits_promptly_on_window_close_and_sigint(self):
        ui = _load_ui_module()
        binding, _ = ui.detect_qt_binding()
        if binding is None:
            self.skipTest("Neither PySide6 nor PyQt6 is installed")

        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            steamapps = home / ".local" / "share" / "Steam" / "steamapps"
            steamapps.mkdir(parents=True)
            for i in range(6):
                appid = 910000 + i
                (steamapps / f"appmanifest_{appid}.acf").write_text(
                    f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"name"\t\t"Slow GUI Game {i}"\n}}\n',
                    encoding="utf-8",
                )

            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            for tool in ("steam-auto-detect", "steam-auto-run"):
                script = mock_bin / tool
                script.write_text("#!/bin/sh\nsleep 30\n", encoding="utf-8")
                script.chmod(0o755)

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["XDG_CONFIG_HOME"] = str(home / ".config")
            env["XDG_STATE_HOME"] = str(home / ".local" / "state")
            env["XDG_CACHE_HOME"] = str(home / ".cache")
            env["QT_QPA_PLATFORM"] = "offscreen"

            # 1) Closing the main window terminates background scans and exits promptly without hanging
            close_driver = (
                "import importlib.machinery, importlib.util, sys\n"
                "from pathlib import Path\n"
                f"loader = importlib.machinery.SourceFileLoader('steam_auto_ui', {str(UI)!r})\n"
                "spec = importlib.util.spec_from_loader(loader.name, loader)\n"
                "mod = importlib.util.module_from_spec(spec)\n"
                "spec.loader.exec_module(mod)\n"
                "_, (QtWidgets, QtCore) = mod.detect_qt_binding()\n"
                f"backend = mod.ProfilerBackend(home=Path({str(home)!r}))\n"
                f"backend.script_dir = Path({str(mock_bin)!r})\n"
                "app = QtWidgets.QApplication(sys.argv)\n"
                "def _close_main():\n"
                "    for w in app.topLevelWidgets():\n"
                "        if isinstance(w, QtWidgets.QMainWindow):\n"
                "            w.close()\n"
                "            return\n"
                "    app.quit()\n"
                "QtCore.QTimer.singleShot(250, _close_main)\n"
                "sys.exit(mod.run_qt_gui(backend))\n"
            )
            t0 = time.monotonic()
            res = subprocess.run(
                [sys.executable, "-c", close_driver],
                env=env,
                text=True,
                capture_output=True,
                timeout=8,
                check=False,
            )
            elapsed = time.monotonic() - t0
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertNotIn("Traceback", res.stderr)
            self.assertNotIn("QThread", res.stderr)
            self.assertLess(elapsed, 4.0)

            # 2) SIGINT (Ctrl+C) exits with status 0 and zero traceback
            sigint_driver = (
                "import importlib.machinery, importlib.util, sys\n"
                "from pathlib import Path\n"
                f"loader = importlib.machinery.SourceFileLoader('steam_auto_ui', {str(UI)!r})\n"
                "spec = importlib.util.spec_from_loader(loader.name, loader)\n"
                "mod = importlib.util.module_from_spec(spec)\n"
                "spec.loader.exec_module(mod)\n"
                "_, (QtWidgets, QtCore) = mod.detect_qt_binding()\n"
                f"backend = mod.ProfilerBackend(home=Path({str(home)!r}))\n"
                f"backend.script_dir = Path({str(mock_bin)!r})\n"
                "app = QtWidgets.QApplication(sys.argv)\n"
                "QtCore.QTimer.singleShot(150, lambda: print('GUI_READY', flush=True))\n"
                "sys.exit(mod.run_qt_gui(backend))\n"
            )
            proc = subprocess.Popen(
                [sys.executable, "-c", sigint_driver],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            try:
                assert proc.stdout is not None
                ready_line = proc.stdout.readline().strip()
                self.assertEqual(ready_line, "GUI_READY")
                t_sig = time.monotonic()
                proc.send_signal(signal.SIGINT)
                _, stderr = proc.communicate(timeout=5)
                sig_elapsed = time.monotonic() - t_sig
            finally:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()
            self.assertEqual(proc.returncode, 0, stderr)
            self.assertNotIn("Traceback", stderr)
            self.assertNotIn("KeyboardInterrupt", stderr)
            self.assertNotIn("QThread", stderr)
            self.assertLess(sig_elapsed, 3.0)

    def test_i18n_catalog_locale_detection_and_cli_lang_flag(self):
        ui = _load_ui_module()
        expected_langs = {
            "en", "fi",
            "ru", "uk", "be", "kk", "uz", "hy", "az", "ky", "tg",
            "pl", "cs", "sk", "bg", "sr", "hr", "sl",
            "de", "fr", "es", "pt", "it", "ja", "ko", "zh-CN", "tr",
        }
        supported_codes = {code for code, _ in ui.SUPPORTED_LANGUAGES}
        self.assertEqual(supported_codes, expected_langs)

        en_keys = set(ui.TRANSLATIONS["en"].keys())
        self.assertEqual(en_keys, set(ui._I18N_KEYS))
        for code in expected_langs:
            self.assertIn(code, ui.TRANSLATIONS)
            self.assertEqual(set(ui.TRANSLATIONS[code].keys()), en_keys, f"Key mismatch in {code}")
            for k, val in ui.TRANSLATIONS[code].items():
                self.assertTrue(isinstance(val, str) and val.strip(), f"Empty translation {code}.{k}")
            # Verify fallback for unknown key gracefully returns key itself
            self.assertEqual(ui.tr(code, "__nonexistent_key__"), "__nonexistent_key__")
            # v2.4.0: Verify AFMF toggle and locked tooltip exist in all 27 languages
            for afmf_key in ("toggle_USE_AFMF", "tip_afmf_locked"):
                self.assertNotEqual(ui.tr(code, afmf_key), afmf_key)
                self.assertTrue(ui.tr(code, afmf_key).strip())

        # Locale normalization & env precedence
        self.assertEqual(ui.normalize_lang("zh_CN.UTF-8"), "zh-CN")
        self.assertEqual(ui.normalize_lang("fi_FI.UTF-8"), "fi")
        self.assertEqual(ui.normalize_lang("uk_UA.UTF-8"), "uk")
        self.assertEqual(ui.normalize_lang("pt_BR.UTF-8"), "pt")
        self.assertEqual(ui.normalize_lang("C.UTF-8"), "en")
        self.assertEqual(ui.normalize_lang("xx_YY"), "en")
        self.assertEqual(ui.detect_system_lang({"LC_ALL": "fi_FI.UTF-8", "LANG": "ru_RU.UTF-8"}), "fi")
        self.assertEqual(ui.detect_system_lang({"LC_MESSAGES": "uk_UA.UTF-8", "LANG": "de_DE.UTF-8"}), "uk")
        self.assertEqual(ui.detect_system_lang({"LANG": "ja_JP.UTF-8"}), "ja")
        self.assertEqual(ui.detect_system_lang({"LANG": "POSIX"}), "en")

        # CLI --lang and LC_ALL check
        with tempfile.TemporaryDirectory() as tmp:
            env = os.environ.copy()
            env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
            env["HOME"] = tmp
            env["XDG_CONFIG_HOME"] = f"{tmp}/.config"
            env["XDG_STATE_HOME"] = f"{tmp}/.local/state"
            env["LC_ALL"] = "uk_UA.UTF-8"

            res_auto = subprocess.run([str(UI), "--check"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_auto.returncode, 0, res_auto.stderr)
            payload_auto = json.loads(res_auto.stdout)
            self.assertEqual(payload_auto["language"], "uk")
            self.assertTrue(payload_auto["i18n_verified"])
            self.assertEqual(set(payload_auto["supported_languages"]), expected_langs)

            res_explicit = subprocess.run(
                [str(UI), "--check", "--lang", "fi"], env=env, text=True, capture_output=True, check=False
            )
            self.assertEqual(res_explicit.returncode, 0, res_explicit.stderr)
            payload_fi = json.loads(res_explicit.stdout)
            self.assertEqual(payload_fi["language"], "fi")

    def test_multilingual_docs_completeness_links_and_privacy(self):
        import re

        expected_guides = [
            ROOT / "docs" / "USER_GUIDE.md",
            ROOT / "docs" / "ARCHITECTURE.md",
            ROOT / "docs" / "i18n" / "nordic" / "USER_GUIDE.fi.md",
            *[ROOT / "docs" / "i18n" / "cis" / f"USER_GUIDE.{c}.md" for c in ("ru", "uk", "be", "kk", "uz", "hy", "az", "ky", "tg")],
            *[ROOT / "docs" / "i18n" / "slavic" / f"USER_GUIDE.{c}.md" for c in ("pl", "cs", "sk", "bg", "sr", "hr", "sl")],
            *[ROOT / "docs" / "i18n" / "global" / f"USER_GUIDE.{c}.md" for c in ("es", "de", "fr", "pt", "it", "ja", "ko", "zh-CN", "tr")],
        ]
        for guide in expected_guides:
            self.assertTrue(guide.is_file(), f"Missing doc: {guide}")
            content = guide.read_text(encoding="utf-8")
            self.assertGreaterEqual(len(content.splitlines()), 100, f"Guide looks like a stub: {guide}")
            for token in (
                "steam-auto-run", "vr-run", "steam-auto-ui", "PROTON_ADD_CONFIG",
                "AUTO_HDR_SWITCH=1", "BENCH=1", "BLEEDING_EDGE=1", "USE_STEAM_CONTROLLER=",
                "594650", "forceinputappid", "--with-steam-controller",
            ):
                self.assertIn(token, content, f"Missing token {token} in {guide}")

        # Verify all relative markdown links in README and i18n index files resolve cleanly
        index_files = [
            ROOT / "README.md",
            ROOT / "docs" / "i18n" / "README.md",
            ROOT / "docs" / "i18n" / "nordic" / "README.md",
            ROOT / "docs" / "i18n" / "cis" / "README.md",
            ROOT / "docs" / "i18n" / "slavic" / "README.md",
            ROOT / "docs" / "i18n" / "global" / "README.md",
        ]
        link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
        for idx_file in index_files:
            self.assertTrue(idx_file.is_file(), f"Missing index: {idx_file}")
            text = idx_file.read_text(encoding="utf-8")
            for target in link_re.findall(text):
                if target.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target_path = (idx_file.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(target_path.exists(), f"Broken link '{target}' in {idx_file}")

        # Ensure zero hardcoded personal home paths in repo source/docs/tests
        home_re = re.compile(r"/home/(?!user\b)[a-z_][a-z0-9_-]{2,}\b")
        for scan_root in (ROOT / "bin", ROOT / "docs", ROOT / "tests", ROOT / "install.sh", ROOT / "README.md"):
            paths = [scan_root] if scan_root.is_file() else [p for p in scan_root.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
            for p in paths:
                self.assertIsNone(
                    home_re.search(p.read_text(encoding="utf-8", errors="ignore")),
                    f"Hardcoded personal path found in {p}",
                )


if __name__ == "__main__":
    unittest.main()
