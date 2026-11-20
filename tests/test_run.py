import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "bin" / "steam-auto-run"
DETECT = ROOT / "bin" / "steam-auto-detect"


class RunTests(unittest.TestCase):
    def test_load_profile_safe_rejects_command_injection(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            marker = home / "injected"
            backtick_marker = home / "backtick_injected"
            (profile_dir / "361420.env").write_text(
                f"USE_SHARPEN=$(touch {marker})\n"
                f"USE_SDL=`touch {backtick_marker}`\n"
                "USE_MLFG=1\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "GAMEID": "361420",
            })
            result = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(marker.exists())
            self.assertFalse(backtick_marker.exists())
            self.assertIn("PROTON_MLFG_UPGRADE=1", result.stdout)

    def test_load_profile_safe_handles_crlf_and_legacy_rcas(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "361420.env").write_text(
                "USE_RCAS=1\r\n"
                "USE_SHARPEN=0\r\n"
                "VRR_CAP=120\r\n",
                encoding="utf-8",
                newline="",
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "GAMEID": "361420",
                "GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0",
            })
            result = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ENABLE_VKBASALT=1", result.stdout)
            self.assertIn("DXVK_FRAME_RATE=120", result.stdout)

    def test_gamescope_skips_redundant_vrr_cap_unless_explicit(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({
                "HOME": temp,
                "XDG_CONFIG_HOME": f"{temp}/.config",
                "NO_GUI": "1",
                "GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0",
                "GAMEID": "361420",
            })
            implicit = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(implicit.returncode, 0, implicit.stderr)
            self.assertNotIn("DXVK_FRAME_RATE=", implicit.stdout)
            self.assertNotIn("VKD3D_FRAME_RATE=", implicit.stdout)

            explicit = env.copy()
            explicit["VRR_CAP"] = "144"
            explicit_result = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=explicit,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(explicit_result.returncode, 0, explicit_result.stderr)
            self.assertIn("DXVK_FRAME_RATE=144", explicit_result.stdout)
            self.assertIn("VKD3D_FRAME_RATE=144", explicit_result.stdout)

    def test_native_linux_title_does_not_export_compat_variables(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            steam = home / ".local/share/Steam"
            apps = steam / "steamapps"
            common = apps / "common/Native_Game"
            common.mkdir(parents=True)
            (common / "native").touch()
            (apps / "appmanifest_361420.acf").write_text(
                '"AppState"\n{\n\t"appid"\t\t"361420"\n\t'
                '"installdir"\t\t"Native_Game"\n\t'
                '"name"\t\t"Native Game"\n}\n',
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "GAMEID": "361420",
            })
            result = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            exported = result.stdout.splitlines()
            self.assertFalse(any(
                line.startswith(("PROTON_", "DXVK_", "VKD3D_"))
                for line in exported
            ))

    def test_last_log_lists_saved_launch_log(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({
                "HOME": temp,
                "XDG_STATE_HOME": f"{temp}/.local/state",
                "XDG_CONFIG_HOME": f"{temp}/.config",
                "NO_GUI": "1",
                "GAMEID": "361420",
            })
            launched = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(launched.returncode, 0, launched.stderr)
            result = subprocess.run(
                [str(RUN), "--last-log", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("appid=361420", result.stdout)
            self.assertIn("exit_code=0", result.stdout)

    def test_list_profiles_lists_saved_profile(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "361420.env").write_text(
                "USE_SHARPEN=1\nUSE_MLFG=1\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
            })
            result = subprocess.run(
                [str(RUN), "--list-profiles"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("361420", result.stdout)
            self.assertIn("USE_SHARPEN=1", result.stdout)
            self.assertIn("USE_MLFG=1", result.stdout)
    def test_doctor_report(self):
        result = subprocess.run(
            [str(RUN), "--doctor"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Steam Auto-Profiler: CachyOS System Doctor", result.stdout)
        self.assertIn("Kernel:", result.stdout)
        self.assertIn("vm.max_map_count=", result.stdout)
        self.assertIn("/usr/share/steam/compatibilitytools.d", RUN.read_text(encoding="utf-8"))

    def test_configure_without_command_exits_successfully(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({
                "HOME": temp,
                "XDG_CONFIG_HOME": f"{temp}/.config",
                "NO_GUI": "1",
            })
            result = subprocess.run(
                [str(RUN), "--configure", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                "Configuration completed for AppID 361420 "
                f"({temp}/.config/steam-auto-profiler/profiles/361420.env).",
                result.stdout,
            )
            self.assertNotIn("Error: No command to launch", result.stderr)
            self.assertTrue(
                (Path(temp) / ".config/steam-auto-profiler/profiles/361420.env").is_file()
            )

    def test_dry_run_without_command_exits_successfully(self):
        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.update({
                "HOME": temp,
                "XDG_CONFIG_HOME": f"{temp}/.config",
                "NO_GUI": "1",
            })
            result = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Steam Auto-Profiler dry run", result.stdout)
            self.assertIn("AppID: 361420", result.stdout)
            self.assertIn("Class:", result.stdout)
            self.assertIn("PROTON_", result.stdout)
            self.assertNotIn("empty launch command", result.stderr)

    def test_legacy_rcas_profile_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "361420.env").write_text(
                "USE_RCAS=1\n"
                "AUTO_PRESET='standard'\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "NO_GUI": "1",
                "GAMEID": "361420",
            })
            result = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ENABLE_VKBASALT=1", result.stdout)

    def test_gameid_resolves_to_appid(self):
        env = os.environ.copy()
        env["GAMEID"] = "umu-2357570"
        result = subprocess.run(
            [str(DETECT), "--json"],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        self.assertIn('"app_id": "2357570"', result.stdout)

    def test_no_ntsync_and_no_decoration(self):
        env = os.environ.copy()
        env.update({
            "NO_GUI": "1",
            "NO_NTSYNC": "1",
            "NO_DECORATION": "1",
            "GAMEID": "361420",
        })
        result = subprocess.run(
            [str(RUN), "/usr/bin/env"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PROTON_NO_NTSYNC=1", result.stdout)
        self.assertIn("PROTON_NO_WM_DECORATION=1", result.stdout)
        self.assertIn("WINE_NO_WM_DECORATION=1", result.stdout)

    def test_fsr_hud_exports_cross_fork_watermark(self):
        env = os.environ.copy()
        env.update({
            "NO_GUI": "1",
            "GAMEID": "361420",
            "USE_FSR_HUD": "1",
        })
        result = subprocess.run(
            [str(RUN), "/usr/bin/env"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PROTON_FSR4_INDICATOR=1", result.stdout)
        self.assertIn("FSR_WATERMARK=1", result.stdout)

    def test_fsr_hud_and_mlfg_export_frame_generation_watermark(self):
        env = os.environ.copy()
        env.update({
            "NO_GUI": "1",
            "GAMEID": "361420",
            "USE_FSR_HUD": "1",
            "USE_MLFG": "1",
        })
        result = subprocess.run(
            [str(RUN), "/usr/bin/env"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("FSR_WATERMARK=1", result.stdout)
        self.assertIn("FSR_FG_WATERMARK=1", result.stdout)

    def test_competitive_profile_keeps_wayland_shortcuts_and_decorations(self):
        env = os.environ.copy()
        env.update({
            "NO_GUI": "1",
            "GAMEID": "umu-2357570",
        })
        result = subprocess.run(
            [str(RUN), "/usr/bin/env"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("WAYLANDDRV_SHORTCUT_INHIBIT=0", result.stdout)
        self.assertIn("PROTON_NO_WM_DECORATION=0", result.stdout)
        self.assertIn("WINE_NO_WM_DECORATION=0", result.stdout)

    def test_partial_profile_inherits_detector_defaults(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "361420.env").write_text(
                "USE_VULKAN=1\nPARTIAL_PROFILE=1\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "NO_GUI": "1",
                "GAMEID": "361420",
            })
            result = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("USE_SHARPEN=1", result.stdout)
            self.assertIn("USE_NET_OPT=0", result.stdout)


if __name__ == "__main__":
    unittest.main()
