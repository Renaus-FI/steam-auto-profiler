import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "bin" / "steam-auto-run"
DETECT = ROOT / "bin" / "steam-auto-detect"


class RunTests(unittest.TestCase):
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
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "GAMEID": "361420",
                "FSR4": "0",
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
            self.assertIn("USE_SHARPEN=1", result.stdout)
            self.assertIn("USE_NET_OPT=0", result.stdout)

    def test_load_profile_safe_reads_last_key_without_trailing_newline(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "361420.env").write_text(
                "USE_XWAYLAND=1\nUSE_MLFG=1",
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
            self.assertIn("PROTON_ENABLE_WAYLAND=0", result.stdout)
            self.assertIn("PROTON_MLFG_UPGRADE=1", result.stdout)
            self.assertIn("MLFG_UPGRADE=1", result.stdout)

    def test_fsr4_and_optiscaler_disable_vkbasalt(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            base_env = os.environ.copy()
            base_env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "GAMEID": "361420",
                "SHARPEN": "1",
            })
            base_env.pop("FSR4", None)
            base_env.pop("OPTISCALER", None)

            # FSR4 enabled (default) must force ENABLE_VKBASALT=0
            res_fsr4 = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "FSR4": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_fsr4.returncode, 0, res_fsr4.stderr)
            self.assertIn("ENABLE_VKBASALT=0", res_fsr4.stdout)

            # OptiScaler enabled (even with FSR4=0) must force ENABLE_VKBASALT=0
            res_opti = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "FSR4": "0", "OPTISCALER": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_opti.returncode, 0, res_opti.stderr)
            self.assertIn("PROTON_USE_OPTISCALER=1", res_opti.stdout)
            self.assertIn("ENABLE_VKBASALT=0", res_opti.stdout)

            # Both disabled allows vkBasalt sharpening
            res_sharpen = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "FSR4": "0", "OPTISCALER": "0"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_sharpen.returncode, 0, res_sharpen.stderr)
            self.assertIn("ENABLE_VKBASALT=1", res_sharpen.stdout)

    def test_mlfg_mutual_exclusion_guard(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "MLFG": "1",
                "VRR_CAP": "165",
                "DXVK_FRAME_RATE": "165",
                "VKD3D_FRAME_RATE": "165",
                "DXVK_FRAME_PACE": "low-latency-vrr",
                "ENABLE_LAYER_MESA_ANTI_LAG": "1",
            })
            result = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PROTON_MLFG_UPGRADE=1", result.stdout)
            self.assertIn("MLFG_UPGRADE=1", result.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", result.stdout)
            self.assertIn("PROTON_DXVK_LOWLATENCY=0", result.stdout)
            self.assertIn("PROTON_VKD3D_LOWLATENCY=0", result.stdout)
            self.assertNotIn("DXVK_FRAME_RATE=", result.stdout)
            self.assertNotIn("VKD3D_FRAME_RATE=", result.stdout)
            self.assertNotIn("DXVK_FRAME_PACE=", result.stdout)

    def test_vrr_active_exports_dxvk_frame_pace(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = os.environ.copy()
            for key in ("MLFG", "USE_MLFG", "GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "DXVK_FRAME_PACE"):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "VRR_CAP": "144",
            })
            res_active = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_active.returncode, 0, res_active.stderr)
            self.assertIn("DXVK_FRAME_PACE=low-latency-vrr", res_active.stdout)
            self.assertIn("DXVK_FRAME_RATE=144", res_active.stdout)
            self.assertIn("VKD3D_FRAME_RATE=144", res_active.stdout)

            res_disabled = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "VRR_CAP": "0"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_disabled.returncode, 0, res_disabled.stderr)
            self.assertNotIn("DXVK_FRAME_PACE=", res_disabled.stdout)
            self.assertNotIn("DXVK_FRAME_RATE=", res_disabled.stdout)
            self.assertNotIn("VKD3D_FRAME_RATE=", res_disabled.stdout)

    def test_vkd3d_config_and_safedx12_bypass(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            env = os.environ.copy()
            env.pop("VKD3D_CONFIG", None)
            env.pop("SAFEDX12", None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
            })
            res_default = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_default.returncode, 0, res_default.stderr)
            self.assertIn(
                "VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer",
                res_default.stdout,
            )

            res_safe = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "SAFEDX12": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_safe.returncode, 0, res_safe.stderr)
            self.assertNotIn("VKD3D_CONFIG=", res_safe.stdout)
            self.assertNotIn("vkd3dbindlesstb", res_safe.stdout)

    def test_wayland_shortcut_inhibit_default_and_profile_override(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True)
            env = os.environ.copy()
            env.pop("WAYLANDDRV_SHORTCUT_INHIBIT", None)
            env.pop("GAMESCOPE_WAYLAND_DISPLAY", None)
            env.pop("XDG_CURRENT_DESKTOP", None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
            })
            # Base Wayland default is 0
            res_default = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_default.returncode, 0, res_default.stderr)
            self.assertIn("WAYLANDDRV_SHORTCUT_INHIBIT=0", res_default.stdout)

            # Per-profile override enables 1 even in competitive-anticheat
            (profile_dir / "2357570.env").write_text(
                "WAYLANDDRV_SHORTCUT_INHIBIT=1\n",
                encoding="utf-8",
            )
            res_profile = subprocess.run(
                [str(RUN), "--dry-run", "2357570"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_profile.returncode, 0, res_profile.stderr)
            self.assertIn("WAYLANDDRV_SHORTCUT_INHIBIT=1", res_profile.stdout)

    def test_doctor_detects_root_cake_and_htb_cake(self):
        cases = (
            (
                "root_cake",
                "qdisc cake 8001: root refcnt 2 bandwidth 500Mbit diffserv4 triple-isolate\n",
                "[OK] sch_cake active on eth0",
            ),
            (
                "htb_leaf_cake",
                "qdisc htb 1: root refcnt 2 r2q 10 default 0x20\n"
                "qdisc fq_codel 10: parent 1:10 limit 10240p\n"
                "qdisc cake 20: parent 1:20 bandwidth 450Mbit diffserv4\n",
                "[OK] sch_cake active on eth0 (HTB hierarchy)",
            ),
            (
                "fq_codel_only",
                "qdisc fq_codel 0: root refcnt 2 limit 10240p\n",
                "[INFO] No active sch_cake qdisc detected on eth0",
            ),
        )
        for name, tc_output, expected in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temp:
                mock_bin = Path(temp) / "bin"
                mock_bin.mkdir()
                ip_mock = mock_bin / "ip"
                ip_mock.write_text(
                    "#!/bin/sh\necho 'default via 192.0.2.1 dev eth0 proto dhcp'\n",
                    encoding="utf-8",
                )
                ip_mock.chmod(0o755)
                tc_mock = mock_bin / "tc"
                tc_mock.write_text(
                    f"#!/bin/sh\ncat <<'EOF'\n{tc_output}EOF\n",
                    encoding="utf-8",
                )
                tc_mock.chmod(0o755)
                env = os.environ.copy()
                env["PATH"] = f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}"
                res = subprocess.run(
                    [str(RUN), "--doctor"],
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(res.returncode, 0, res.stderr)
                self.assertIn(expected, res.stdout)

    def test_steamvr_and_vr_flag_bypass(self):
        env = os.environ.copy()
        env["SteamAppId"] = "250820"
        res_steamvr = subprocess.run(
            [str(RUN), "/bin/echo", "steamvr-direct"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(res_steamvr.returncode, 0, res_steamvr.stderr)
        self.assertEqual(res_steamvr.stdout.strip(), "steamvr-direct")

        env.pop("SteamAppId", None)
        res_flag = subprocess.run(
            [str(RUN), "/bin/echo", "-vr", "vr-direct"],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(res_flag.returncode, 0, res_flag.stderr)
        self.assertEqual(res_flag.stdout.strip(), "-vr vr-direct")

    def test_fast_crash_logs_hint_and_offers_safe_mode_prompt(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            state_dir = home / ".local" / "state" / "steam-auto-profiler"
            profile_dir = home / ".config" / "steam-auto-profiler" / "profiles"
            env = os.environ.copy()
            env.pop("SAFEDX12", None)
            env.pop("XWAYLAND", None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "NO_GUI": "1",
                "GAMEID": "361420",
            })

            # Headless fast crash records duration_sec and crash_hint in logs
            res_crash = subprocess.run(
                [str(RUN), "/bin/false"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(res_crash.returncode, 0)
            last_log = (state_dir / "last-launch.log").read_text(encoding="utf-8")
            self.assertIn("duration_sec=", last_log)
            self.assertIn("crash_hint=fast_crash_detected", last_log)
            self.assertIn("USE_XWAYLAND=1,USE_SAFEDX12=1", last_log)

            # With GUI enabled (mock kdialog accepting Safe Mode), saves USE_XWAYLAND=1 & USE_SAFEDX12=1
            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            kdialog = mock_bin / "kdialog"
            kdialog.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            kdialog.chmod(0o755)
            # Pre-create profile so pre-launch checklist is skipped and only crash prompt fires
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "361420.env").write_text("USE_SDL=1\n", encoding="utf-8")

            gui_env = {
                **env,
                "NO_GUI": "0",
                "WAYLAND_DISPLAY": "wayland-0",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            }
            res_gui = subprocess.run(
                [str(RUN), "/bin/false"],
                env=gui_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(res_gui.returncode, 0)
            saved_profile = (profile_dir / "361420.env").read_text(encoding="utf-8")
            self.assertIn("USE_XWAYLAND=1", saved_profile)
            self.assertIn("USE_SAFEDX12=1", saved_profile)
            self.assertIn("USE_SDL=1", saved_profile)
            gui_log = (state_dir / "last-361420.log").read_text(encoding="utf-8")
            self.assertIn("crash_recovery=safe_mode_saved", gui_log)

    def test_profile_use_fsr4_zero_disables_fsr4(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            profile_dir = home / ".config" / "steam-auto-profiler" / "profiles"
            profile_dir.mkdir(parents=True)
            (profile_dir / "361420.env").write_text(
                "USE_FSR4=0\nUSE_SHARPEN=1\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.pop("FSR4", None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
            })
            res = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("PROTON_FSR4_UPGRADE=0", res.stdout)
            self.assertIn("ENABLE_VKBASALT=1", res.stdout)

    def test_ui_flag_delegates_to_steam_auto_ui(self):
        import json as _json

        with tempfile.TemporaryDirectory() as temp:
            env = os.environ.copy()
            env.pop("DISPLAY", None)
            env.pop("WAYLAND_DISPLAY", None)
            env.update({
                "HOME": temp,
                "XDG_CONFIG_HOME": f"{temp}/.config",
                "XDG_STATE_HOME": f"{temp}/.local/state",
            })
            res = subprocess.run(
                [str(RUN), "--ui", "--check"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            payload = _json.loads(res.stdout)
            self.assertEqual(payload["status"], "ok")

    def test_auto_hdr_switch_dry_run_and_trap_restore(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            ks_log = home / "kscreen.log"
            hdr_state_file = home / "hdr.state"
            hdr_state_file.write_text("disabled\n", encoding="utf-8")

            kscreen = mock_bin / "kscreen-doctor"
            kscreen.write_text(
                "#!/bin/sh\n"
                f'if [ "$1" = "-o" ]; then\n'
                f'  state="$(cat "{hdr_state_file}")"\n'
                '  printf "Output: 1 DP-1 uuid-1\\n\\tenabled\\n\\tconnected\\n\\tpriority 1\\n\\tHDR: %s\\n" "$state"\n'
                "else\n"
                f'  echo "$*" >> "{ks_log}"\n'
                "fi\n",
                encoding="utf-8",
            )
            kscreen.chmod(0o755)

            env = os.environ.copy()
            for k in ("GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XWAYLAND", "DXVK_NO_HDR"):
                env.pop(k, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "NO_GUI": "1",
                "GAMEID": "361420",
                "AUTO_HDR_SWITCH": "1",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })

            # Dry-run inspects primary output without toggling HDR
            res_dry = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_dry.returncode, 0, res_dry.stderr)
            self.assertIn("HDR auto-switch: DP-1 (state=disabled)", res_dry.stdout)
            self.assertFalse(ks_log.exists())

            # Real launch enables HDR before launch and disables via trap on exit
            res_run = subprocess.run(
                [str(RUN), "/bin/true"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_run.returncode, 0, res_run.stderr)
            calls = ks_log.read_text(encoding="utf-8").splitlines()
            self.assertEqual(calls, ["output.DP-1.hdr.enable", "output.DP-1.hdr.disable"])

            # When HDR is already enabled on desktop, do not toggle or disable on exit
            ks_log.unlink()
            hdr_state_file.write_text("enabled\n", encoding="utf-8")
            res_already = subprocess.run(
                [str(RUN), "/bin/true"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_already.returncode, 0, res_already.stderr)
            self.assertFalse(ks_log.exists())

    def test_bench_mode_parses_mangohud_csv_metrics(self):
        import json as _json

        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            mh = mock_bin / "mangohud"
            mh.write_text("#!/bin/sh\nexec \"$@\"\n", encoding="utf-8")
            mh.chmod(0o755)

            mock_game = home / "mock-game.py"
            mock_game.write_text(
                "#!/usr/bin/env python3\n"
                "import os, re\n"
                "from pathlib import Path\n"
                "cfg = os.environ.get('MANGOHUD_CONFIG', '')\n"
                "assert 'no_display' in cfg and 'log_duration=30' in cfg and 'permit_upload=0' in cfg, cfg\n"
                "m = re.search(r'output_folder=([^,]+)', cfg)\n"
                "assert m, cfg\n"
                "out = Path(m.group(1)) / 'run.csv'\n"
                "rows = ['os,cpu,gpu', 'Linux,AMD,RDNA4', 'fps,frametime,cpu_load']\n"
                "rows.extend(['100.0,10.0,20'] * 98)\n"
                "rows.extend(['40.0,25.0,45'] * 2)\n"
                "out.write_text('\\n'.join(rows) + '\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            mock_game.chmod(0o755)

            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "NO_GUI": "1",
                "GAMEID": "361420",
                "BENCH": "1",
                "BENCH_DURATION": "30",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })
            res = subprocess.run(
                [str(RUN), str(mock_game)],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)

            bench_file = home / ".config" / "steam-auto-profiler" / "benchmarks" / "361420.json"
            self.assertTrue(bench_file.is_file(), "Benchmark JSON was not created")
            records = _json.loads(bench_file.read_text(encoding="utf-8"))
            self.assertEqual(len(records), 1)
            rec = records[0]
            self.assertEqual(rec["samples"], 100)
            self.assertAlmostEqual(rec["avg_fps"], 97.09, places=1)
            self.assertAlmostEqual(rec["low_1pct_fps"], 40.0, places=1)
            self.assertAlmostEqual(rec["p99_frametime_ms"], 25.0, places=1)

    @staticmethod
    def _make_mock_drm(base: Path, vendor: str, device: str, vram_bytes: int = 17179869184) -> Path:
        drm = base / "drm"
        dev = drm / "card0" / "device"
        dev.mkdir(parents=True, exist_ok=True)
        (dev / "vendor").write_text(f"{vendor}\n", encoding="utf-8")
        (dev / "device").write_text(f"{device}\n", encoding="utf-8")
        (dev / "mem_info_vram_total").write_text(f"{vram_bytes}\n", encoding="utf-8")
        (dev / "boot_vga").write_text("0\n", encoding="utf-8")
        v_short = vendor.lower().removeprefix("0x").upper()
        d_short = device.lower().removeprefix("0x").upper()
        (dev / "uevent").write_text(f"PCI_ID={v_short}:{d_short}\n", encoding="utf-8")
        return drm

    def test_transfer_queue_rdna4_and_default_sam(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            rdna2_drm = self._make_mock_drm(home / "rdna2", "0x1002", "0x73bf")
            base_env = os.environ.copy()
            for key in ("RADV_PERFTEST", "TRANSFER_QUEUE", "USE_TRANSFER_QUEUE"):
                base_env.pop(key, None)
            base_env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
            })

            # Default keeps RADV_PERFTEST=sam without transfer_queue
            res_default = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=base_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_default.returncode, 0, res_default.stderr)
            self.assertIn("RADV_PERFTEST=sam\n", res_default.stdout)
            self.assertNotIn("transfer_queue", res_default.stdout)

            # Env override TRANSFER_QUEUE=1 appends transfer_queue on RDNA 4
            res_env = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "TRANSFER_QUEUE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_env.returncode, 0, res_env.stderr)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue", res_env.stdout)

            # Profile USE_TRANSFER_QUEUE=1 appends transfer_queue on RDNA 4
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "361420.env").write_text("USE_TRANSFER_QUEUE=1\n", encoding="utf-8")
            res_prof = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=base_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_prof.returncode, 0, res_prof.stderr)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue", res_prof.stdout)

            # Older non-RDNA3/4 AMD GPU does not append transfer_queue
            res_old = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "SAP_DRM_DIR": str(rdna2_drm)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_old.returncode, 0, res_old.stderr)
            self.assertIn("RADV_PERFTEST=sam\n", res_old.stdout)
            self.assertNotIn("transfer_queue", res_old.stdout)

    def test_native_antilag_disables_legacy_layer_and_respects_mlfg(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            env = os.environ.copy()
            for key in ("MLFG", "USE_MLFG", "REFLEX_LAYER", "USE_REFLEX_LAYER", "NATIVE_ANTILAG", "USE_NATIVE_ANTILAG"):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
                "ENABLE_LAYER_MESA_ANTI_LAG": "1",
            })

            res_native = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "NATIVE_ANTILAG": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_native.returncode, 0, res_native.stderr)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_native.stdout)
            self.assertIn("PROTON_DXVK_LOWLATENCY=1", res_native.stdout)
            self.assertIn("PROTON_VKD3D_LOWLATENCY=1", res_native.stdout)

            # MLFG still disables low-latency pacing when USE_NATIVE_ANTILAG=1
            res_mlfg = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "USE_NATIVE_ANTILAG": "1", "USE_MLFG": "1", "VRR_CAP": "240"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_mlfg.returncode, 0, res_mlfg.stderr)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_mlfg.stdout)
            self.assertIn("PROTON_DXVK_LOWLATENCY=0", res_mlfg.stdout)
            self.assertIn("PROTON_VKD3D_LOWLATENCY=0", res_mlfg.stdout)
            self.assertNotIn("DXVK_FRAME_RATE=", res_mlfg.stdout)

    def test_reflex_layer_exports_and_mutual_exclusion_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            env = os.environ.copy()
            for key in (
                "MLFG", "USE_MLFG", "REFLEX_LAYER", "USE_REFLEX_LAYER",
                "LOW_LATENCY_LAYER", "LOW_LATENCY_LAYER_REFLEX",
            ):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
                "ENABLE_LAYER_MESA_ANTI_LAG": "1",
            })

            # Standard title with USE_REFLEX_LAYER=1 enables LOW_LATENCY_LAYER + REFLEX and disables Mesa Anti-Lag layer
            res_std = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "USE_REFLEX_LAYER": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_std.returncode, 0, res_std.stderr)
            self.assertIn("LOW_LATENCY_LAYER=1", res_std.stdout)
            self.assertIn("LOW_LATENCY_LAYER_REFLEX=1", res_std.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_std.stdout)
            self.assertIn("lowlatencylayer", res_std.stdout)

            # MLFG=1 disables Reflex layer and omits lowlatencylayer token
            res_mlfg = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "USE_REFLEX_LAYER": "1", "MLFG": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_mlfg.returncode, 0, res_mlfg.stderr)
            self.assertIn("LOW_LATENCY_LAYER=0", res_mlfg.stdout)
            self.assertIn("LOW_LATENCY_LAYER_REFLEX=0", res_mlfg.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_mlfg.stdout)
            self.assertNotIn("lowlatencylayer", res_mlfg.stdout)

            # competitive-anticheat (2357570) hard-blocks LOW_LATENCY_LAYER and LOW_LATENCY_LAYER_REFLEX
            res_ac = subprocess.run(
                [str(RUN), "--dry-run", "2357570"],
                env={
                    **env,
                    "REFLEX_LAYER": "1",
                    "USE_REFLEX_LAYER": "1",
                    "LOW_LATENCY_LAYER": "1",
                    "LOW_LATENCY_LAYER_REFLEX": "1",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_ac.returncode, 0, res_ac.stderr)
            self.assertIn("LOW_LATENCY_LAYER=0", res_ac.stdout)
            self.assertIn("LOW_LATENCY_LAYER_REFLEX=0", res_ac.stdout)
            self.assertNotIn("lowlatencylayer", res_ac.stdout)

    def test_vk_video_decode_experimental_and_retired_proton_flag_purge(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            env = os.environ.copy()
            for key in ("RADV_PERFTEST", "RADV_EXPERIMENTAL", "VK_VIDEO_DECODE", "USE_VK_VIDEO_DECODE"):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
                "PROTON_ENABLE_HDR": "1",
                "PROTON_VKREFLEX": "1",
                "PROTON_MEDIA_USE_GST": "1",
                "PROTON_FSR3_UPGRADE": "1",
                "PROTON_VKD3D_HEAP": "1",
                "WINEPULSE_FAST_POLLING": "1",
            })

            res_vid = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "USE_VK_VIDEO_DECODE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_vid.returncode, 0, res_vid.stderr)
            self.assertIn("RADV_EXPERIMENTAL=video_decode", res_vid.stdout)
            self.assertIn("RADV_PERFTEST=sam\n", res_vid.stdout)
            for retired in (
                "PROTON_ENABLE_HDR=",
                "PROTON_VKREFLEX=",
                "PROTON_MEDIA_USE_GST=",
                "PROTON_FSR3_UPGRADE=",
                "PROTON_VKD3D_HEAP=",
                "WINEPULSE_FAST_POLLING=",
            ):
                self.assertNotIn(retired, res_vid.stdout)

            # Legacy RADV_PERFTEST=sam,video_decode is migrated to RADV_EXPERIMENTAL=video_decode
            res_mig = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "RADV_PERFTEST": "sam,video_decode"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_mig.returncode, 0, res_mig.stderr)
            self.assertIn("RADV_EXPERIMENTAL=video_decode", res_mig.stdout)
            self.assertIn("RADV_PERFTEST=sam\n", res_mig.stdout)


if __name__ == "__main__":
    unittest.main()


_SAP_TEST_STATE_DIR = None
_SAP_TEST_CONFIG_DIR = None
_SAP_ORIG_XDG_ENV = {}


def setUpModule():
    import os as _os
    import tempfile as _tempfile
    global _SAP_TEST_STATE_DIR, _SAP_TEST_CONFIG_DIR, _SAP_ORIG_XDG_ENV
    _SAP_ORIG_XDG_ENV = {
        k: _os.environ.get(k)
        for k in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME")
    }
    _os.environ.pop("XDG_CONFIG_HOME", None)
    _os.environ.pop("XDG_DATA_HOME", None)
    _SAP_TEST_STATE_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-state-")
    _SAP_TEST_CONFIG_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-config-")
    _os.environ["XDG_CONFIG_HOME"] = _SAP_TEST_CONFIG_DIR.name
    _os.environ["XDG_STATE_HOME"] = _SAP_TEST_STATE_DIR.name


def tearDownModule():
    import os as _os
    global _SAP_TEST_STATE_DIR, _SAP_TEST_CONFIG_DIR, _SAP_ORIG_XDG_ENV
    for k, val in _SAP_ORIG_XDG_ENV.items():
        if val is None:
            _os.environ.pop(k, None)
        else:
            _os.environ[k] = val
    _SAP_ORIG_XDG_ENV = {}
    if _SAP_TEST_STATE_DIR is not None:
        _SAP_TEST_STATE_DIR.cleanup()
        _SAP_TEST_STATE_DIR = None
    if _SAP_TEST_CONFIG_DIR is not None:
        _SAP_TEST_CONFIG_DIR.cleanup()
        _SAP_TEST_CONFIG_DIR = None
