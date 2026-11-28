import json
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

    def test_fast_crash_silent_two_stage_self_healing_and_reset(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4-crash", "0x1002", "0x7550")
            state_dir = home / ".local" / "state" / "steam-auto-profiler"
            profile_dir = home / ".config" / "steam-auto-profiler" / "profiles"
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "361420.env").write_text("USE_SDL=1\n", encoding="utf-8")

            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            kd_log = home / "kdialog.calls"
            kdialog = mock_bin / "kdialog"
            kdialog.write_text(f'#!/bin/sh\necho "$*" >> "{kd_log}"\nexit 0\n', encoding="utf-8")
            kdialog.chmod(0o755)

            notify_log = home / "notify.calls"
            notify_mock = mock_bin / "notify-send"
            notify_mock.write_text(f'#!/bin/sh\necho "$*" >> "{notify_log}"\n', encoding="utf-8")
            notify_mock.chmod(0o755)

            env = os.environ.copy()
            for key in (
                "SAFEDX12", "XWAYLAND", "NO_GUI", "FORCE_GUI", "CONSERVATIVE",
                "BLEEDING_EDGE", "TRANSFER_QUEUE", "REFLEX_LAYER", "VK_VIDEO_DECODE", "OPTISCALER",
                "RADV_EXPERIMENTAL", "AFMF", "USE_AFMF", "AFMF_ENABLE", "DISABLE_AFMF",
            ):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "SAP_DRM_DIR": str(rdna4_drm),
                "WAYLAND_DISPLAY": "wayland-0",
                "GAMEID": "361420",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })

            # Crash 1: experimental flags active -> Stage 1 silently disables experimental flags (NO kdialog popup!)
            res_stage1 = subprocess.run(
                [str(RUN), "/bin/false"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(res_stage1.returncode, 0)
            self.assertFalse(kd_log.exists(), "Fast crash recovery must be non-blocking with zero kdialog popups")
            self.assertTrue(notify_log.is_file(), "Optional non-blocking notify-send should fire")
            self.assertIn("Stage 1", notify_log.read_text(encoding="utf-8"))

            saved1 = (profile_dir / "361420.env").read_text(encoding="utf-8")
            self.assertIn("USE_AFMF=0", saved1)
            self.assertIn("USE_OPTISCALER=0", saved1)
            self.assertIn("USE_BLEEDING_EDGE=0", saved1)
            self.assertIn("USE_REFLEX_LAYER=0", saved1)
            self.assertIn("USE_TRANSFER_QUEUE=0", saved1)
            self.assertIn("USE_VK_VIDEO_DECODE=0", saved1)
            self.assertIn("USE_SDL=1", saved1)
            self.assertNotIn("USE_SAFEDX12=1", saved1)
            self.assertNotIn("USE_XWAYLAND=1", saved1)
            self.assertEqual((state_dir / "recovery-361420.state").read_text(encoding="utf-8").strip(), "RECOVERY_STAGE=1")
            log1 = (state_dir / "last-361420.log").read_text(encoding="utf-8")
            self.assertIn("crash_hint=fast_crash_detected stage=1", log1)
            self.assertIn("crash_recovery=stage1_experimental_disabled", log1)

            # Verify Stage 1 dry-run uses stable baseline (experimental off, still native Wayland + DX12)
            res_dry1 = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_dry1.returncode, 0, res_dry1.stderr)
            self.assertIn("PROTON_ENABLE_WAYLAND=1", res_dry1.stdout)
            self.assertIn("VKD3D_CONFIG=", res_dry1.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_dry1.stdout)
            self.assertNotIn("transfer_queue", res_dry1.stdout)
            self.assertNotIn("RADV_EXPERIMENTAL=video_decode", res_dry1.stdout)

            # Crash 2: still fast-crashes after Stage 1 -> Stage 2 escalates to USE_SAFEDX12=1 & USE_XWAYLAND=1
            res_stage2 = subprocess.run(
                [str(RUN), "/bin/false"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(res_stage2.returncode, 0)
            self.assertFalse(kd_log.exists(), "Stage 2 recovery must remain silent with zero kdialog popups")
            self.assertIn("Stage 2", notify_log.read_text(encoding="utf-8"))

            saved2 = (profile_dir / "361420.env").read_text(encoding="utf-8")
            self.assertIn("USE_SAFEDX12=1", saved2)
            self.assertIn("USE_XWAYLAND=1", saved2)
            self.assertIn("USE_OPTISCALER=0", saved2)
            self.assertIn("USE_BLEEDING_EDGE=0", saved2)
            self.assertIn("USE_SDL=1", saved2)
            self.assertEqual((state_dir / "recovery-361420.state").read_text(encoding="utf-8").strip(), "RECOVERY_STAGE=2")
            log2 = (state_dir / "last-361420.log").read_text(encoding="utf-8")
            self.assertIn("crash_hint=fast_crash_detected stage=2", log2)
            self.assertIn("crash_recovery=stage2_safe_mode_saved", log2)

            # Verify Stage 2 dry-run applies XWayland + SafeDX12 + both SDL x11 variables
            res_dry2 = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "SDL_VIDEO_DRIVER": "wayland"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_dry2.returncode, 0, res_dry2.stderr)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_dry2.stdout)
            self.assertIn("SDL_VIDEODRIVER=x11", res_dry2.stdout)
            self.assertIn("SDL_VIDEO_DRIVER=x11", res_dry2.stdout)
            self.assertNotIn("VKD3D_CONFIG=", res_dry2.stdout)
            self.assertNotIn("VKD3D_FEATURE_LEVEL=", res_dry2.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_dry2.stdout)

            # Healthy run (>= threshold) resets the recovery state marker cleanly
            res_healthy = subprocess.run(
                [str(RUN), "/bin/true"],
                env={**env, "SAP_CRASH_THRESHOLD_SEC": "0"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_healthy.returncode, 0, res_healthy.stderr)
            self.assertFalse((state_dir / "recovery-361420.state").exists())

            # --reset removes both the .env profile and any recovery state marker
            (state_dir / "recovery-361420.state").write_text("RECOVERY_STAGE=2\n", encoding="utf-8")
            res_reset = subprocess.run(
                [str(RUN), "--reset", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_reset.returncode, 0, res_reset.stderr)
            self.assertFalse((profile_dir / "361420.env").exists())
            self.assertFalse((state_dir / "recovery-361420.state").exists())

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
            for key in ("RADV_PERFTEST", "TRANSFER_QUEUE", "USE_TRANSFER_QUEUE", "CONSERVATIVE", "USE_CONSERVATIVE"):
                base_env.pop(key, None)
            base_env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
            })

            # v2.2.0: RDNA 4 defaults to RADV_PERFTEST=sam,transfer_queue automatically
            res_default = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=base_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_default.returncode, 0, res_default.stderr)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue\n", res_default.stdout)

            # Explicit env opt-out TRANSFER_QUEUE=0 reverts to RADV_PERFTEST=sam
            res_optout = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "TRANSFER_QUEUE": "0"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_optout.returncode, 0, res_optout.stderr)
            self.assertIn("RADV_PERFTEST=sam\n", res_optout.stdout)
            self.assertNotIn("transfer_queue", res_optout.stdout)

            # Profile USE_TRANSFER_QUEUE=0 overrides smart default on RDNA 4
            profile_dir = home / ".config/steam-auto-profiler/profiles"
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "361420.env").write_text("USE_TRANSFER_QUEUE=0\n", encoding="utf-8")
            res_prof = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env=base_env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_prof.returncode, 0, res_prof.stderr)
            self.assertIn("RADV_PERFTEST=sam\n", res_prof.stdout)
            self.assertNotIn("transfer_queue", res_prof.stdout)

            # Older non-RDNA3/4 AMD GPU does not append transfer_queue
            res_old = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "SAP_DRM_DIR": str(rdna2_drm), "TRANSFER_QUEUE": "1"},
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
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_vid.returncode, 0, res_vid.stderr)
            self.assertIn("RADV_EXPERIMENTAL=video_decode", res_vid.stdout)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue\n", res_vid.stdout)
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
            self.assertIn("RADV_PERFTEST=sam,transfer_queue\n", res_mig.stdout)

            # Explicit VK_VIDEO_DECODE=0 disables RADV_EXPERIMENTAL=video_decode
            res_off = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "VK_VIDEO_DECODE": "0"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_off.returncode, 0, res_off.stderr)
            self.assertNotIn("RADV_EXPERIMENTAL=video_decode", res_off.stdout)

    def test_bleeding_edge_mode_exports_and_guards(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            empty_usb = home / "usb-empty"
            empty_usb.mkdir()
            env = os.environ.copy()
            for key in (
                "RADV_PERFTEST", "RADV_EXPERIMENTAL", "VKD3D_CONFIG",
                "VKD3D_FEATURE_LEVEL", "VKD3D_SHADER_MODEL", "PROTON_USE_WOW64",
                "PROTON_MEDIA_FORCE_GST", "WAYLANDDRV_RAWINPUT", "BLEEDING_EDGE",
                "USE_BLEEDING_EDGE", "MLFG", "USE_MLFG", "XWAYLAND", "SAFEDX12",
                "GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP",
            ):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
                "SAP_USB_DIR": str(empty_usb),
            })

            # v2.2.0: Non-anticheat RDNA 4 title activates full experimental stack BY DEFAULT & disables vkBasalt
            res = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "SHARPEN": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue", res.stdout)
            self.assertIn("RADV_EXPERIMENTAL=video_decode", res.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res.stdout)
            self.assertIn("VKD3D_CONFIG=descriptor_heap,dxr12,force_bindless_texel_buffer", res.stdout)
            self.assertIn("VKD3D_FEATURE_LEVEL=12_2", res.stdout)
            self.assertIn("VKD3D_SHADER_MODEL=6_8", res.stdout)
            self.assertIn("PROTON_FSR4_UPGRADE=1", res.stdout)
            self.assertIn("PROTON_NATIVE_AGS=1", res.stdout)
            self.assertIn("PROTON_USE_WOW64=1", res.stdout)
            self.assertIn("PROTON_MEDIA_FORCE_GST=1", res.stdout)
            self.assertIn("WAYLANDDRV_RAWINPUT=1", res.stdout)
            self.assertIn("ENABLE_VKBASALT=0", res.stdout)
            self.assertIn("wow64", res.stdout)

            # RDNA 3 defaults to PROTON_FSR4_RDNA3_UPGRADE=1 + transfer_queue + bleeding-edge
            rdna3_drm = self._make_mock_drm(home / "rdna3", "0x1002", "0x744c")
            res_rdna3 = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "SAP_DRM_DIR": str(rdna3_drm)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_rdna3.returncode, 0, res_rdna3.stderr)
            self.assertIn("PROTON_FSR4_RDNA3_UPGRADE=1", res_rdna3.stdout)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue", res_rdna3.stdout)
            self.assertIn("PROTON_USE_WOW64=1", res_rdna3.stdout)

            # With XWAYLAND=1, WAYLANDDRV_RAWINPUT is explicitly unset/omitted even if pre-set
            res_xway = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "USE_BLEEDING_EDGE": "1", "XWAYLAND": "1", "WAYLANDDRV_RAWINPUT": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_xway.returncode, 0, res_xway.stderr)
            self.assertNotIn("WAYLANDDRV_RAWINPUT=", res_xway.stdout)
            self.assertIn("PROTON_USE_WOW64=1", res_xway.stdout)

            # Under Gamescope, WAYLANDDRV_RAWINPUT is also explicitly unset/omitted even if pre-set
            res_gs = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={
                    **env,
                    "USE_BLEEDING_EDGE": "1",
                    "GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0",
                    "WAYLANDDRV_RAWINPUT": "1",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_gs.returncode, 0, res_gs.stderr)
            self.assertNotIn("WAYLANDDRV_RAWINPUT=", res_gs.stdout)

            # Pre-set RADV_PERFTEST and RADV_EXPERIMENTAL tokens are cleanly deduplicated
            res_dedupe = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={
                    **env,
                    "USE_BLEEDING_EDGE": "1",
                    "RADV_PERFTEST": "sam,transfer_queue,sam,gpl,transfer_queue",
                    "RADV_EXPERIMENTAL": "video_decode,video_decode",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_dedupe.returncode, 0, res_dedupe.stderr)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue,gpl\n", res_dedupe.stdout)
            self.assertIn("RADV_EXPERIMENTAL=video_decode\n", res_dedupe.stdout)

            # With MLFG=1 also active, FPS caps and Anti-Lag remain disabled
            res_mlfg = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**env, "USE_BLEEDING_EDGE": "1", "USE_MLFG": "1", "VRR_CAP": "240"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_mlfg.returncode, 0, res_mlfg.stderr)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_mlfg.stdout)
            self.assertNotIn("DXVK_FRAME_RATE=", res_mlfg.stdout)
            self.assertNotIn("VKD3D_FRAME_RATE=", res_mlfg.stdout)

            # competitive-anticheat (2357570) keeps driver-level RDNA 4 defaults safe while hard-blocking bleeding-edge hooks
            res_ac = subprocess.run(
                [str(RUN), "--dry-run", "2357570"],
                env={**env, "USE_BLEEDING_EDGE": "1", "BLEEDING_EDGE": "1", "MLFG": "1", "OPTISCALER": "1", "REFLEX_LAYER": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_ac.returncode, 0, res_ac.stderr)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue", res_ac.stdout)
            self.assertIn("RADV_EXPERIMENTAL=video_decode", res_ac.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_ac.stdout)
            self.assertIn("LOW_LATENCY_LAYER=0", res_ac.stdout)
            self.assertIn("PROTON_MLFG_UPGRADE=0", res_ac.stdout)
            self.assertIn("PROTON_USE_OPTISCALER=0", res_ac.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_ac.stdout)
            self.assertNotIn("PROTON_MEDIA_FORCE_GST=", res_ac.stdout)
            self.assertNotIn("VKD3D_FEATURE_LEVEL=", res_ac.stdout)
            self.assertNotIn("VKD3D_SHADER_MODEL=", res_ac.stdout)
            self.assertNotIn("WAYLANDDRV_RAWINPUT=", res_ac.stdout)
            self.assertNotIn("lowlatencylayer", res_ac.stdout)
            self.assertNotIn("wow64", res_ac.stdout)

    def test_smart_reflex_auto_activation_opt_outs_conservative_and_inheritance(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            empty_usb = home / "usb-empty"
            empty_usb.mkdir()
            steamapps = home / ".local/share/Steam/steamapps"
            common = steamapps / "common"

            def add_game(appid: str, name: str, files: tuple[str, ...]) -> None:
                gdir = common / name.replace(" ", "_")
                gdir.mkdir(parents=True, exist_ok=True)
                for rel in files:
                    p = gdir / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.touch()
                (steamapps / f"appmanifest_{appid}.acf").write_text(
                    f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"installdir"\t\t"{gdir.name}"\n\t"name"\t\t"{name}"\n}}\n',
                    encoding="utf-8",
                )

            add_game("4101", "Reflex AAA", ("game.exe", "sl.reflex.dll", "nvngx_dlss.dll"))
            add_game("4102", "AC Reflex", ("game.exe", "sl.reflex.dll", "EasyAntiCheat/EasyAntiCheat.exe"))
            add_game("4103", "Native Linux Game", ("game.x86_64",))

            env = os.environ.copy()
            for key in (
                "RADV_PERFTEST", "RADV_EXPERIMENTAL", "BLEEDING_EDGE", "USE_BLEEDING_EDGE",
                "TRANSFER_QUEUE", "USE_TRANSFER_QUEUE", "NATIVE_ANTILAG", "USE_NATIVE_ANTILAG",
                "REFLEX_LAYER", "USE_REFLEX_LAYER", "VK_VIDEO_DECODE", "USE_VK_VIDEO_DECODE",
                "CONSERVATIVE", "USE_CONSERVATIVE", "MLFG", "USE_MLFG", "ENABLE_LAYER_MESA_ANTI_LAG",
                "GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP",
            ):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
                "SAP_USB_DIR": str(empty_usb),
                "WAYLAND_DISPLAY": "wayland-0",
            })

            # 1) Smart Reflex -> Anti-Lag 2 auto-activation on AMD non-anticheat title with sl.reflex.dll
            res_rx = subprocess.run([str(RUN), "--dry-run", "4101"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_rx.returncode, 0, res_rx.stderr)
            self.assertIn("LOW_LATENCY_LAYER=1", res_rx.stdout)
            self.assertIn("LOW_LATENCY_LAYER_REFLEX=1", res_rx.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_rx.stdout)
            self.assertIn("lowlatencylayer", res_rx.stdout)
            self.assertIn("PROTON_USE_WOW64=1", res_rx.stdout)

            # 2) MLFG=1 disables auto-activated Reflex layer
            res_mlfg = subprocess.run([str(RUN), "--dry-run", "4101"], env={**env, "MLFG": "1"}, text=True, capture_output=True, check=False)
            self.assertEqual(res_mlfg.returncode, 0, res_mlfg.stderr)
            self.assertIn("LOW_LATENCY_LAYER=0", res_mlfg.stdout)
            self.assertNotIn("lowlatencylayer", res_mlfg.stdout)

            # 3) Anti-cheat title with sl.reflex.dll hard-blocks Reflex layer and Bleeding-Edge
            res_ac = subprocess.run([str(RUN), "--dry-run", "4102"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_ac.returncode, 0, res_ac.stderr)
            self.assertIn("LOW_LATENCY_LAYER=0", res_ac.stdout)
            self.assertNotIn("lowlatencylayer", res_ac.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_ac.stdout)

            # 4) Explicit env =0 opt-outs override smart =1 defaults independently
            res_opt0 = subprocess.run(
                [str(RUN), "--dry-run", "4101"],
                env={
                    **env,
                    "BLEEDING_EDGE": "0",
                    "TRANSFER_QUEUE": "0",
                    "NATIVE_ANTILAG": "0",
                    "REFLEX_LAYER": "0",
                    "VK_VIDEO_DECODE": "0",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_opt0.returncode, 0, res_opt0.stderr)
            self.assertIn("RADV_PERFTEST=sam\n", res_opt0.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=1", res_opt0.stdout)
            self.assertNotIn("LOW_LATENCY_LAYER=1", res_opt0.stdout)
            self.assertNotIn("RADV_EXPERIMENTAL=video_decode", res_opt0.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_opt0.stdout)
            self.assertNotIn("VKD3D_FEATURE_LEVEL=", res_opt0.stdout)
            self.assertNotIn("WAYLANDDRV_RAWINPUT=", res_opt0.stdout)

            # 5) CONSERVATIVE=1 disables all 5 experimental defaults at once
            res_cons = subprocess.run(
                [str(RUN), "--dry-run", "4101"],
                env={**env, "CONSERVATIVE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_cons.returncode, 0, res_cons.stderr)
            self.assertIn("Conservative: enabled", res_cons.stdout)
            self.assertIn("RADV_PERFTEST=sam\n", res_cons.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=1", res_cons.stdout)
            self.assertNotIn("LOW_LATENCY_LAYER=1", res_cons.stdout)
            self.assertNotIn("RADV_EXPERIMENTAL=video_decode", res_cons.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_cons.stdout)
            self.assertNotIn("VKD3D_FEATURE_LEVEL=", res_cons.stdout)

            # 6) Legacy .env missing v2.2 keys inherits smart defaults; explicit .env =0 overrides them
            profiles = home / ".config/steam-auto-profiler/profiles"
            profiles.mkdir(parents=True, exist_ok=True)
            (profiles / "4101.env").write_text("USE_SDL=1\n", encoding="utf-8")
            res_inherit = subprocess.run([str(RUN), "--dry-run", "4101"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_inherit.returncode, 0, res_inherit.stderr)
            self.assertIn("PROTON_USE_SDL=1", res_inherit.stdout)
            self.assertIn("PROTON_USE_WOW64=1", res_inherit.stdout)
            self.assertIn("RADV_PERFTEST=sam,transfer_queue", res_inherit.stdout)
            self.assertIn("LOW_LATENCY_LAYER=1", res_inherit.stdout)

            (profiles / "4101.env").write_text(
                "USE_BLEEDING_EDGE=0\nUSE_TRANSFER_QUEUE=0\nUSE_NATIVE_ANTILAG=0\nUSE_REFLEX_LAYER=0\nUSE_VK_VIDEO_DECODE=0\n",
                encoding="utf-8",
            )
            res_env0 = subprocess.run([str(RUN), "--dry-run", "4101"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_env0.returncode, 0, res_env0.stderr)
            self.assertIn("RADV_PERFTEST=sam\n", res_env0.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=1", res_env0.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_env0.stdout)
            self.assertNotIn("LOW_LATENCY_LAYER=1", res_env0.stdout)
            self.assertNotIn("RADV_EXPERIMENTAL=video_decode", res_env0.stdout)

            # 7) Native Linux game hard-blocks bleeding-edge even if BLEEDING_EDGE=1
            res_nat = subprocess.run(
                [str(RUN), "--dry-run", "4103"],
                env={**env, "BLEEDING_EDGE": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_nat.returncode, 0, res_nat.stderr)
            self.assertNotIn("Bleeding-edge: enabled", res_nat.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_nat.stdout)

    def test_hunt_showdown_594650_safe_overrides_and_doctor_compat_warning(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            empty_usb = home / "usb-empty"
            empty_usb.mkdir()
            env = os.environ.copy()
            for key in ("VKD3D_CONFIG", "PROTON_NATIVE_AGS", "LOW_LATENCY_LAYER", "GAMESCOPE_WAYLAND_DISPLAY"):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "NO_GUI": "1",
                "SAP_DRM_DIR": str(rdna4_drm),
                "SAP_USB_DIR": str(empty_usb),
                "BLEEDING_EDGE": "1",
                "MLFG": "1",
                "REFLEX_LAYER": "1",
                "PROTON_NATIVE_AGS": "1",
                "VKD3D_CONFIG": "descriptor_heap,dxr12",
            })

            res = subprocess.run(
                [str(RUN), "--dry-run", "594650"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("Class: competitive-anticheat", res.stdout)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res.stdout)
            self.assertIn("SDL_VIDEODRIVER=x11", res.stdout)
            self.assertIn("PROTON_NATIVE_AGS=0", res.stdout)
            self.assertIn("LOW_LATENCY_LAYER=0", res.stdout)
            self.assertIn("PROTON_MLFG_UPGRADE=0", res.stdout)
            self.assertNotIn("VKD3D_CONFIG=", res.stdout)
            self.assertNotIn("VKD3D_FEATURE_LEVEL=", res.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res.stdout)
            self.assertNotIn("vkd3dbindlesstb", res.stdout)
            self.assertNotIn("nativeags", res.stdout)

            # Verify --doctor CompatToolMapping checks in config/config.vdf
            cfg_vdf = home / ".local" / "share" / "Steam" / "config" / "config.vdf"
            cfg_vdf.parent.mkdir(parents=True)

            # 1) Unset 594650 -> [WARN]
            cfg_vdf.write_text(
                '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
                '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t\t"0"\n\t\t\t\t\t{\n'
                '\t\t\t\t\t\t"name"\t\t"proton-cachyos-slr"\n\t\t\t\t\t}\n\t\t\t\t}\n'
                '\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            doc_unset = subprocess.run([str(RUN), "--doctor"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(doc_unset.returncode, 0, doc_unset.stderr)
            self.assertIn("[WARN] Hunt: Showdown 1896 (AppID 594650)", doc_unset.stdout)
            self.assertIn("Proton 11.0-2", doc_unset.stdout)
            self.assertIn("Proton Hotfix", doc_unset.stdout)

            # 2) Mapped to proton-cachyos-slr -> [WARN]
            cfg_vdf.write_text(
                '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
                '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t\t"594650"\n\t\t\t\t\t{\n'
                '\t\t\t\t\t\t"name"\t\t"proton-cachyos-slr"\n\t\t\t\t\t}\n\t\t\t\t}\n'
                '\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            doc_cachy = subprocess.run([str(RUN), "--doctor"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(doc_cachy.returncode, 0, doc_cachy.stderr)
            self.assertIn("[WARN] Hunt: Showdown 1896 (AppID 594650)", doc_cachy.stdout)
            self.assertIn("proton-cachyos-slr", doc_cachy.stdout)

            # 3) Mapped to Valve Proton 11 -> [OK]
            cfg_vdf.write_text(
                '"InstallConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n\t\t\t"Steam"\n\t\t\t{\n'
                '\t\t\t\t"CompatToolMapping"\n\t\t\t\t{\n\t\t\t\t\t"594650"\n\t\t\t\t\t{\n'
                '\t\t\t\t\t\t"name"\t\t"proton_11"\n\t\t\t\t\t}\n\t\t\t\t}\n'
                '\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            doc_ok = subprocess.run([str(RUN), "--doctor"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(doc_ok.returncode, 0, doc_ok.stderr)
            self.assertIn("[OK] Hunt: Showdown 1896 (AppID 594650) CompatToolMapping: proton_11", doc_ok.stdout)

    def test_steam_controller_2026_usb_auto_detection_and_doctor(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            base_env = os.environ.copy()
            for key in (
                "XWAYLAND", "SDL", "USE_SDL", "PROTON_USE_SDL", "PROTON_PREFER_SDL",
                "PROTON_NO_STEAMINPUT", "USE_STEAM_CONTROLLER", "STEAM_CONTROLLER",
                "GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XDG_SESSION_TYPE",
                "WAYLAND_DISPLAY", "PROTON_ADD_CONFIG", "STEAM_COMPAT_CONFIG",
                "KEEP_OVERLAY", "USE_KEEP_OVERLAY",
            ):
                base_env.pop(key, None)
            base_env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "NO_GUI": "1",
            })

            # On Wayland, auto mode selects wayland-hdr for all 4 Valve 2026 USB PIDs
            for pid in ("1304", "1302", "1005", "1007"):
                with self.subTest(usb_pid=pid):
                    usb_dir = home / f"usb-{pid}"
                    dev_dir = usb_dir / "3-2"
                    (dev_dir / "power").mkdir(parents=True)
                    (dev_dir / "idVendor").write_text("28de\n", encoding="utf-8")
                    (dev_dir / "idProduct").write_text(f"{pid}\n", encoding="utf-8")
                    (dev_dir / "power" / "control").write_text("auto\n", encoding="utf-8")

                    res_auto = subprocess.run(
                        [str(RUN), "--dry-run", "361420"],
                        env={
                            **base_env,
                            "WAYLAND_DISPLAY": "wayland-0",
                            "SAP_USB_DIR": str(usb_dir),
                            "PROTON_ADD_CONFIG": "sdlinput",
                        },
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(res_auto.returncode, 0, res_auto.stderr)
                    self.assertIn("Steam Controller 2026: wayland-hdr", res_auto.stdout)
                    self.assertIn("steam://forceinputappid/361420", res_auto.stdout)
                    self.assertIn("steam://forceinputappid/0", res_auto.stdout)
                    self.assertIn("PROTON_ENABLE_WAYLAND=1", res_auto.stdout)
                    self.assertIn("DXVK_HDR=1", res_auto.stdout)
                    self.assertIn("PROTON_USE_SDL=0", res_auto.stdout)
                    self.assertIn("PROTON_PREFER_SDL=0", res_auto.stdout)
                    self.assertIn("PROTON_NO_STEAMINPUT=0", res_auto.stdout)
                    self.assertNotIn("sdlinput", res_auto.stdout)

            # On non-Wayland (X11), auto mode falls back to xwayland
            usb_1304 = home / "usb-1304"
            res_x11_auto = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={**base_env, "DISPLAY": ":0", "SAP_USB_DIR": str(usb_1304)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_x11_auto.returncode, 0, res_x11_auto.stderr)
            self.assertIn("Steam Controller 2026: xwayland", res_x11_auto.stdout)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_x11_auto.stdout)
            self.assertIn("PROTON_USE_SDL=0", res_x11_auto.stdout)
            self.assertIn("PROTON_NO_STEAMINPUT=0", res_x11_auto.stdout)
            self.assertNotIn("sdlinput", res_x11_auto.stdout)

            # Explicit xwayland mode forces XWayland + LD_PRELOAD preservation + Steam Input
            empty_usb = home / "usb-empty"
            empty_usb.mkdir()
            res_xway = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env={
                    **base_env,
                    "WAYLAND_DISPLAY": "wayland-0",
                    "SAP_USB_DIR": str(empty_usb),
                    "GAMEID": "361420",
                    "USE_STEAM_CONTROLLER": "xwayland",
                    "LD_PRELOAD": "/tmp/mock_overlay.so",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_xway.returncode, 0, res_xway.stderr)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_xway.stdout)
            self.assertIn("PROTON_USE_SDL=0", res_xway.stdout)
            self.assertIn("PROTON_NO_STEAMINPUT=0", res_xway.stdout)
            self.assertIn("LD_PRELOAD=/tmp/mock_overlay.so", res_xway.stdout)
            self.assertNotIn("sdlinput", res_xway.stdout)

            # wayland-hdr does NOT force LD_PRELOAD unless KEEP_OVERLAY=1
            res_whdr_ld = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env={
                    **base_env,
                    "WAYLAND_DISPLAY": "wayland-0",
                    "SAP_USB_DIR": str(empty_usb),
                    "GAMEID": "361420",
                    "USE_STEAM_CONTROLLER": "wayland-hdr",
                    "LD_PRELOAD": "/tmp/mock_overlay.so",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_whdr_ld.returncode, 0, res_whdr_ld.stderr)
            self.assertIn("PROTON_ENABLE_WAYLAND=1", res_whdr_ld.stdout)
            self.assertIn("DXVK_HDR=1", res_whdr_ld.stdout)
            self.assertIn("LD_PRELOAD=\n", res_whdr_ld.stdout)

            # USE_STEAM_CONTROLLER=off (and 0) disables all Steam Controller overrides
            for off_val in ("off", "0"):
                res_off = subprocess.run(
                    [str(RUN), "--dry-run", "361420"],
                    env={
                        **base_env,
                        "WAYLAND_DISPLAY": "wayland-0",
                        "SAP_USB_DIR": str(usb_1304),
                        "USE_STEAM_CONTROLLER": off_val,
                    },
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(res_off.returncode, 0, res_off.stderr)
                self.assertIn("PROTON_ENABLE_WAYLAND=1", res_off.stdout)
                self.assertNotIn("Steam Controller 2026:", res_off.stdout)
                self.assertNotIn("PROTON_USE_SDL=0", res_off.stdout)

            # Legacy USE_STEAM_CONTROLLER=1 maps to wayland-hdr on Wayland and xwayland on X11
            res_leg_wl = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={
                    **base_env,
                    "WAYLAND_DISPLAY": "wayland-0",
                    "SAP_USB_DIR": str(empty_usb),
                    "USE_STEAM_CONTROLLER": "1",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_leg_wl.returncode, 0, res_leg_wl.stderr)
            self.assertIn("Steam Controller 2026: wayland-hdr", res_leg_wl.stdout)
            self.assertIn("PROTON_ENABLE_WAYLAND=1", res_leg_wl.stdout)

            res_leg_x11 = subprocess.run(
                [str(RUN), "--dry-run", "361420"],
                env={
                    **base_env,
                    "DISPLAY": ":0",
                    "SAP_USB_DIR": str(empty_usb),
                    "USE_STEAM_CONTROLLER": "1",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_leg_x11.returncode, 0, res_leg_x11.stderr)
            self.assertIn("Steam Controller 2026: xwayland", res_leg_x11.stdout)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_leg_x11.stdout)

            # AppID 594650 (Hunt: Showdown 1896) keeps CryEngine/EAC precedence over wayland-hdr
            res_hunt = subprocess.run(
                [str(RUN), "--dry-run", "594650"],
                env={
                    **base_env,
                    "WAYLAND_DISPLAY": "wayland-0",
                    "SAP_USB_DIR": str(usb_1304),
                    "USE_STEAM_CONTROLLER": "wayland-hdr",
                    "BLEEDING_EDGE": "1",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_hunt.returncode, 0, res_hunt.stderr)
            self.assertIn("Class: competitive-anticheat", res_hunt.stdout)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_hunt.stdout)
            self.assertIn("PROTON_NATIVE_AGS=0", res_hunt.stdout)
            self.assertIn("LOW_LATENCY_LAYER=0", res_hunt.stdout)
            self.assertIn("PROTON_MLFG_UPGRADE=0", res_hunt.stdout)
            self.assertNotIn("VKD3D_CONFIG=", res_hunt.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res_hunt.stdout)

            # Doctor checks udev rule presence, USB power/control, ModemManager ignore, and Vulkan RADV
            udev_dir = home / "udev"
            udev_dir.mkdir()
            doc_warn = subprocess.run(
                [str(RUN), "--doctor"],
                env={**base_env, "SAP_USB_DIR": str(usb_1304), "SAP_UDEV_RULES_DIR": str(udev_dir)},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(doc_warn.returncode, 0, doc_warn.stderr)
            self.assertIn("Steam Controller 2026 / Puck detected: 28de:1304", doc_warn.stdout)
            self.assertIn("[WARN] Steam Controller 2026 USB power/control=auto", doc_warn.stdout)
            self.assertIn("[WARN] Steam Controller 2026 udev rules", doc_warn.stdout)

            (usb_1304 / "3-2" / "power" / "control").write_text("on\n", encoding="utf-8")
            (udev_dir / "61-steam-controller-2026.rules").write_text(
                'SUBSYSTEM=="tty", ENV{ID_MM_DEVICE_IGNORE}="1", ATTR{power/control}="on"\n',
                encoding="utf-8",
            )
            mock_vk_bin = home / "vk-bin"
            mock_vk_bin.mkdir()
            vk_mock = mock_vk_bin / "vulkaninfo"
            vk_mock.write_text(
                "#!/bin/sh\necho VK_AMD_anti_lag\necho VK_EXT_descriptor_heap\necho VK_KHR_maintenance12\n",
                encoding="utf-8",
            )
            vk_mock.chmod(0o755)
            doc_ok = subprocess.run(
                [str(RUN), "--doctor"],
                env={
                    **base_env,
                    "SAP_USB_DIR": str(usb_1304),
                    "SAP_UDEV_RULES_DIR": str(udev_dir),
                    "PATH": f"{mock_vk_bin}:{base_env.get('PATH', '/usr/bin:/bin')}",
                },
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(doc_ok.returncode, 0, doc_ok.stderr)
            self.assertIn("[OK] Steam Controller 2026 USB selective suspend disabled", doc_ok.stdout)
            self.assertIn("[OK] Steam Controller 2026 udev rules installed", doc_ok.stdout)
            self.assertIn("[OK] ModemManager safely ignored for Steam Controller 2026", doc_ok.stdout)
            self.assertIn("[OK] Vulkan RADV readiness: VK_AMD_anti_lag VK_EXT_descriptor_heap VK_KHR_maintenance12", doc_ok.stdout)

    def test_steam_controller_wayland_hdr_forceinputappid_watcher_reconnect_and_reapply(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            steam_log = home / "steam.log"

            pgrep_mock = mock_bin / "pgrep"
            pgrep_mock.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "-x" ] && [ "$2" = "steam" ]; then exit 0; fi\n'
                "exit 1\n",
                encoding="utf-8",
            )
            pgrep_mock.chmod(0o755)

            steam_mock = mock_bin / "steam"
            steam_mock.write_text(
                "#!/bin/sh\n"
                f'echo "$*" >> "{steam_log}"\n',
                encoding="utf-8",
            )
            steam_mock.chmod(0o755)

            udevadm_mock = mock_bin / "udevadm"
            udevadm_mock.write_text(
                "#!/bin/sh\n"
                "sleep 0.2\n"
                "echo 'UDEV  [100.1] add      /devices/pci0000:00/usb3/3-2/0003:28DE:1304.0002/hidraw/hidraw4 (hidraw)'\n"
                "echo 'UDEV  [100.2] change   /devices/pci0000:00/usb3/3-2/0003:28DE:1304.0002/hidraw/hidraw4 (hidraw)'\n"
                "sleep 10\n",
                encoding="utf-8",
            )
            udevadm_mock.chmod(0o755)

            mock_game = home / "mock-game.sh"
            mock_game.write_text("#!/bin/sh\nsleep 0.6\n", encoding="utf-8")
            mock_game.chmod(0o755)

            env = os.environ.copy()
            for key in ("GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "XWAYLAND"):
                env.pop(key, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "NO_GUI": "1",
                "WAYLAND_DISPLAY": "wayland-0",
                "GAMEID": "361420",
                "USE_STEAM_CONTROLLER": "wayland-hdr",
                "SAP_FORCE_INPUT_DELAY1": "0",
                "SAP_FORCE_INPUT_DELAY2": "0",
                "SAP_FORCE_INPUT_DEBOUNCE": "2",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })

            res = subprocess.run(
                [str(RUN), str(mock_game)],
                env=env,
                text=True,
                capture_output=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            calls = steam_log.read_text(encoding="utf-8").splitlines()
            # Expect initial launch trigger + debounced reconnect trigger + exit reset to 0
            self.assertGreaterEqual(calls.count("steam://forceinputappid/361420"), 2, calls)
            # Burst of 2 udev events within 2s debounce must NOT trigger 2 extra calls
            self.assertEqual(calls.count("steam://forceinputappid/361420"), 2, calls)
            self.assertEqual(calls[-1], "steam://forceinputappid/0", calls)

            # Test manual --reapply-input <APPID> and --reapply-input 0
            steam_log.unlink()
            res_app = subprocess.run(
                [str(RUN), "--reapply-input", "361420"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_app.returncode, 0, res_app.stderr)
            self.assertIn("steam://forceinputappid/361420", res_app.stdout)

            res_reset = subprocess.run(
                [str(RUN), "--reapply-input", "0"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_reset.returncode, 0, res_reset.stderr)
            self.assertIn("steam://forceinputappid/0", res_reset.stdout)
            self.assertEqual(
                steam_log.read_text(encoding="utf-8").splitlines(),
                ["steam://forceinputappid/361420", "steam://forceinputappid/0"],
            )

    def test_v23_silent_launch_default_vs_force_gui_and_sdl_video_driver_x11(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            kd_log = home / "kdialog.calls"
            kdialog = mock_bin / "kdialog"
            kdialog.write_text(f'#!/bin/sh\necho "$*" >> "{kd_log}"\necho "xwayland"\nexit 0\n', encoding="utf-8")
            kdialog.chmod(0o755)

            env = os.environ.copy()
            for k in ("NO_GUI", "FORCE_GUI", "XWAYLAND", "USE_XWAYLAND", "GAMESCOPE_WAYLAND_DISPLAY"):
                env.pop(k, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "WAYLAND_DISPLAY": "wayland-0",
                "GAMEID": "361420",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })

            # 1) Default launch with no saved .env runs silently without invoking kdialog
            res_silent = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_silent.returncode, 0, res_silent.stderr)
            self.assertFalse(kd_log.exists(), "Default launch must be silent (NO_GUI=1 by default)")
            self.assertIn("PROTON_ENABLE_WAYLAND=1", res_silent.stdout)

            # 2) FORCE_GUI=1 opens interactive kdialog on demand
            res_force = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env={**env, "FORCE_GUI": "1"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_force.returncode, 0, res_force.stderr)
            self.assertTrue(kd_log.is_file(), "FORCE_GUI=1 must open pre-launch checklist dialog")
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_force.stdout)
            self.assertIn("SDL_VIDEODRIVER=x11", res_force.stdout)
            self.assertIn("SDL_VIDEO_DRIVER=x11", res_force.stdout)

            # 3) Inherited SDL_VIDEO_DRIVER=wayland from environment.d is overridden to x11 under XWayland / Hunt 594650
            res_hunt = subprocess.run(
                [str(RUN), "--dry-run", "594650"],
                env={**env, "SDL_VIDEO_DRIVER": "wayland", "SDL_VIDEODRIVER": "wayland"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_hunt.returncode, 0, res_hunt.stderr)
            self.assertIn("PROTON_ENABLE_WAYLAND=0", res_hunt.stdout)
            self.assertIn("SDL_VIDEODRIVER=x11", res_hunt.stdout)
            self.assertIn("SDL_VIDEO_DRIVER=x11", res_hunt.stdout)

    def test_v23_auto_optiscaler_and_auto_hdr_smart_defaults_and_opt_outs(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            steamapps = home / ".local/share/Steam/steamapps"
            common = steamapps / "common"

            def add_game(appid: str, name: str, files: tuple[str, ...]) -> None:
                gdir = common / name.replace(" ", "_")
                gdir.mkdir(parents=True, exist_ok=True)
                for rel in files:
                    p = gdir / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.touch()
                (steamapps / f"appmanifest_{appid}.acf").write_text(
                    f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"installdir"\t\t"{gdir.name}"\n\t"name"\t\t"{name}"\n}}\n',
                    encoding="utf-8",
                )

            add_game("5101", "Legacy DLSS Game", ("game.exe", "nvngx_dlss.dll"))
            add_game("5102", "AC Legacy DLSS", ("game.exe", "nvngx_dlss.dll", "EasyAntiCheat/EasyAntiCheat.exe"))

            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            ks_log = home / "kscreen.log"
            hdr_state = home / "hdr.state"
            hdr_state.write_text("disabled\n", encoding="utf-8")
            kscreen = mock_bin / "kscreen-doctor"
            kscreen.write_text(
                "#!/bin/sh\n"
                'if [ "$1" = "-o" ]; then\n'
                f'  state="$(cat "{hdr_state}")"\n'
                '  printf "Output: 1 DP-1 uuid-1\\n\\tenabled\\n\\tconnected\\n\\tpriority 1\\n\\tHDR: %s\\n" "$state"\n'
                "else\n"
                f'  echo "$*" >> "{ks_log}"\n'
                "fi\n",
                encoding="utf-8",
            )
            kscreen.chmod(0o755)

            env = os.environ.copy()
            for k in (
                "OPTISCALER", "USE_OPTISCALER", "CONSERVATIVE", "USE_CONSERVATIVE",
                "AUTO_HDR_SWITCH", "DXVK_NO_HDR", "XWAYLAND", "GAMESCOPE_WAYLAND_DISPLAY",
                "XDG_CURRENT_DESKTOP", "SHARPEN", "NO_GUI",
            ):
                env.pop(k, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "SAP_DRM_DIR": str(rdna4_drm),
                "WAYLAND_DISPLAY": "wayland-0",
                "GAMEID": "5101",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })

            # 1) Legacy upscaler on RDNA 4 auto-enables OptiScaler + Auto HDR Switch by default
            res_auto = subprocess.run([str(RUN), "--dry-run", "5101"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_auto.returncode, 0, res_auto.stderr)
            self.assertIn("PROTON_USE_OPTISCALER=1", res_auto.stdout)
            self.assertIn("PROTON_OPTISCALER_STREAMLINE=1", res_auto.stdout)
            self.assertIn("ENABLE_VKBASALT=0", res_auto.stdout)
            self.assertIn("HDR auto-switch: DP-1 (state=disabled)", res_auto.stdout)

            # Real launch without AUTO_HDR_SWITCH env var auto-enables HDR from SDR and restores on exit
            res_hdr_sdr = subprocess.run([str(RUN), "/bin/true"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_hdr_sdr.returncode, 0, res_hdr_sdr.stderr)
            self.assertEqual(ks_log.read_text(encoding="utf-8").splitlines(), ["output.DP-1.hdr.enable", "output.DP-1.hdr.disable"])

            # When desktop HDR is already enabled, auto-HDR is a zero-flicker no-op
            ks_log.unlink()
            hdr_state.write_text("enabled\n", encoding="utf-8")
            res_hdr_on = subprocess.run([str(RUN), "/bin/true"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_hdr_on.returncode, 0, res_hdr_on.stderr)
            self.assertFalse(ks_log.exists())

            # Explicit AUTO_HDR_SWITCH=0 and DXVK_NO_HDR=1 disable Auto HDR Switch even when desktop is SDR
            hdr_state.write_text("disabled\n", encoding="utf-8")
            for disable_env in ({"AUTO_HDR_SWITCH": "0"}, {"DXVK_NO_HDR": "1"}):
                res_off = subprocess.run([str(RUN), "/bin/true"], env={**env, **disable_env}, text=True, capture_output=True, check=False)
                self.assertEqual(res_off.returncode, 0, res_off.stderr)
                self.assertFalse(ks_log.exists(), f"HDR must not toggle with {disable_env}")

            # 2) Explicit OPTISCALER=0, CONSERVATIVE=1, and anti-cheat disable OptiScaler cleanly
            res_opt0 = subprocess.run([str(RUN), "--dry-run", "5101"], env={**env, "OPTISCALER": "0"}, text=True, capture_output=True, check=False)
            self.assertEqual(res_opt0.returncode, 0, res_opt0.stderr)
            self.assertIn("PROTON_USE_OPTISCALER=0", res_opt0.stdout)

            res_cons = subprocess.run([str(RUN), "--dry-run", "5101"], env={**env, "CONSERVATIVE": "1"}, text=True, capture_output=True, check=False)
            self.assertEqual(res_cons.returncode, 0, res_cons.stderr)
            self.assertIn("PROTON_USE_OPTISCALER=0", res_cons.stdout)

            res_ac = subprocess.run([str(RUN), "--dry-run", "5102"], env={**env, "OPTISCALER": "1"}, text=True, capture_output=True, check=False)
            self.assertEqual(res_ac.returncode, 0, res_ac.stderr)
            self.assertIn("PROTON_USE_OPTISCALER=0", res_ac.stdout)

    def test_doctor_reports_mesa_shader_hook_and_pending_flag(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            hooks_dir = home / "pacman-hooks"
            hooks_dir.mkdir()
            state_dir = home / ".local" / "state" / "steam-auto-profiler"
            state_dir.mkdir(parents=True)
            env = os.environ.copy()
            env.update({
                "HOME": str(home),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "SAP_PACMAN_HOOKS_DIR": str(hooks_dir),
            })

            res_missing = subprocess.run([str(RUN), "--doctor"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_missing.returncode, 0, res_missing.stderr)
            self.assertIn("[INFO] Automatic Mesa shader-cleanup pacman hook", res_missing.stdout)
            self.assertIn("--with-mesa-hook", res_missing.stdout)

            (hooks_dir / "95-steam-auto-profiler-mesa-shaders.hook").write_text(
                "Exec = /usr/local/bin/steam-auto-clean-shaders --hook\n",
                encoding="utf-8",
            )
            (state_dir / "pending-shader-cleanup").write_text("reason=steam_running\n", encoding="utf-8")
            res_ok = subprocess.run([str(RUN), "--doctor"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_ok.returncode, 0, res_ok.stderr)
            self.assertIn("[OK] Automatic Mesa shader-cleanup pacman hook installed", res_ok.stdout)
            self.assertIn("[WARN] Pending Steam shader cache cleanup", res_ok.stdout)

    def test_v24_smart_auto_afmf_vrr_pacing_guards_and_crash_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            rdna4_drm = self._make_mock_drm(home / "rdna4", "0x1002", "0x7550")
            steamapps = home / ".local/share/Steam/steamapps"
            common = steamapps / "common"

            def add_game(appid: str, name: str, files: tuple[str, ...]) -> None:
                gdir = common / name.replace(" ", "_")
                gdir.mkdir(parents=True, exist_ok=True)
                for rel in files:
                    p = gdir / rel
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.touch()
                (steamapps / f"appmanifest_{appid}.acf").write_text(
                    f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"installdir"\t\t"{gdir.name}"\n\t"name"\t\t"{name}"\n}}\n',
                    encoding="utf-8",
                )

            add_game("7101", "Cyber 3D Title", ("game.exe", "d3d12.dll"))
            add_game("7102", "Native FG Title", ("game.exe", "nvngx_dlssg.dll"))
            add_game("7103", "AC Protected", ("game.exe", "EasyAntiCheat/EasyAntiCheat.exe"))
            add_game("7104", "VR Title", ("game.exe", "openvr_api.dll"))
            add_game("594650", "Hunt Showdown 1896", ("hunt.exe",))

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
                        "disable_environment": {"DISABLE_AFMF": "1"},
                    },
                }),
                encoding="utf-8",
            )
            empty_layer_dir = home / "vk-layers-empty"
            empty_layer_dir.mkdir()

            mock_bin = home / "mock-bin"
            mock_bin.mkdir()
            ks = mock_bin / "kscreen-doctor"
            ks.write_text(
                "#!/bin/sh\n"
                'printf "Output: 1 DP-1 uuid-1\\n\\tenabled\\n\\tModes: 1:3440x1440@239.98*\\n"\n',
                encoding="utf-8",
            )
            ks.chmod(0o755)

            env = os.environ.copy()
            for k in (
                "AFMF", "USE_AFMF", "AFMF_ENABLE", "DISABLE_AFMF", "AFMF_GAMESCOPE",
                "MLFG", "USE_MLFG", "CONSERVATIVE", "USE_CONSERVATIVE",
                "VRR_CAP", "VRR_MINUS_MARGIN", "DXVK_FRAME_RATE", "VKD3D_FRAME_RATE",
                "GAMESCOPE_WAYLAND_DISPLAY", "XDG_CURRENT_DESKTOP", "RADV_EXPERIMENTAL",
                "NO_GUI", "FORCE_GUI",
            ):
                env.pop(k, None)
            env.update({
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_STATE_HOME": str(home / ".local" / "state"),
                "SAP_DRM_DIR": str(rdna4_drm),
                "SAP_AFMF_LAYER_DIRS": str(layer_dir),
                "WAYLAND_DISPLAY": "wayland-0",
                "PATH": f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}",
            })

            # 1) Zero-touch AFMF auto-activates with VRR half-cap (240 -> 120), native low-latency, MLFG=0
            res_auto = subprocess.run([str(RUN), "--dry-run", "7101"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_auto.returncode, 0, res_auto.stderr)
            self.assertIn("AFMF: enabled (afmf-linux; VRR half-cap=120)", res_auto.stdout)
            self.assertIn("AFMF_ENABLE=1", res_auto.stdout)
            self.assertIn("AFMF_PACING=1", res_auto.stdout)
            self.assertIn("AFMF_PRESENT_MODE=auto", res_auto.stdout)
            self.assertNotIn("DISABLE_AFMF=1", res_auto.stdout)
            self.assertIn("DXVK_FRAME_RATE=120", res_auto.stdout)
            self.assertIn("VKD3D_FRAME_RATE=120", res_auto.stdout)
            self.assertIn("PROTON_MLFG_UPGRADE=0", res_auto.stdout)
            self.assertIn("MLFG_UPGRADE=0", res_auto.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=0", res_auto.stdout)
            self.assertIn("PROTON_DXVK_LOWLATENCY=1", res_auto.stdout)
            self.assertIn("PROTON_VKD3D_LOWLATENCY=1", res_auto.stdout)

            # With VRR_MINUS_MARGIN=1 (225 -> half-cap 112)
            res_margin = subprocess.run(
                [str(RUN), "--dry-run", "7101"], env={**env, "VRR_MINUS_MARGIN": "1"},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_margin.returncode, 0, res_margin.stderr)
            self.assertIn("DXVK_FRAME_RATE=112", res_margin.stdout)
            self.assertIn("VKD3D_FRAME_RATE=112", res_margin.stdout)

            # Gamescope exports AFMF_GAMESCOPE=1 and omits caps unless VRR_CAP explicit
            res_gs = subprocess.run(
                [str(RUN), "--dry-run", "7101"], env={**env, "GAMESCOPE_WAYLAND_DISPLAY": "gamescope-0"},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_gs.returncode, 0, res_gs.stderr)
            self.assertIn("AFMF_ENABLE=1", res_gs.stdout)
            self.assertIn("AFMF_GAMESCOPE=1", res_gs.stdout)
            self.assertNotIn("DXVK_FRAME_RATE=", res_gs.stdout)

            # 2) AFMF=0, USE_AFMF=0, and CONSERVATIVE=1 opt out cleanly and restore 240 Hz cap
            for opt_out in ({"AFMF": "0"}, {"USE_AFMF": "0"}, {"CONSERVATIVE": "1"}):
                res_off = subprocess.run(
                    [str(RUN), "--dry-run", "7101"], env={**env, **opt_out},
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(res_off.returncode, 0, res_off.stderr)
                self.assertNotIn("AFMF_ENABLE=1", res_off.stdout)
                self.assertIn("DISABLE_AFMF=1", res_off.stdout)
                self.assertIn("DXVK_FRAME_RATE=240", res_off.stdout)

            # 3) MLFG=1 mutually excludes AFMF
            res_mlfg = subprocess.run(
                [str(RUN), "--dry-run", "7101"], env={**env, "MLFG": "1"},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_mlfg.returncode, 0, res_mlfg.stderr)
            self.assertNotIn("AFMF_ENABLE=1", res_mlfg.stdout)
            self.assertIn("DISABLE_AFMF=1", res_mlfg.stdout)
            self.assertIn("PROTON_MLFG_UPGRADE=1", res_mlfg.stdout)
            self.assertIn("MLFG_UPGRADE=1", res_mlfg.stdout)

            # 4) Native FG title disables AFMF by default, but allows explicit AFMF=1 override
            res_fg = subprocess.run([str(RUN), "--dry-run", "7102"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_fg.returncode, 0, res_fg.stderr)
            self.assertNotIn("AFMF_ENABLE=1", res_fg.stdout)
            self.assertIn("AFMF: disabled (native FG detected)", res_fg.stdout)

            res_fg_force = subprocess.run(
                [str(RUN), "--dry-run", "7102"], env={**env, "AFMF": "1"},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_fg_force.returncode, 0, res_fg_force.stderr)
            self.assertIn("AFMF_ENABLE=1", res_fg_force.stdout)

            # 5) Hard locks on competitive-anticheat, AppID 594650, and VR reject AFMF=1 and scrub AFMF_ENABLE
            for locked_id in ("7103", "594650", "7104"):
                res_lock = subprocess.run(
                    [str(RUN), "--dry-run", locked_id],
                    env={**env, "AFMF": "1", "AFMF_ENABLE": "1"},
                    text=True, capture_output=True, check=False,
                )
                self.assertEqual(res_lock.returncode, 0, res_lock.stderr)
                self.assertNotIn("AFMF_ENABLE=1", res_lock.stdout, f"AFMF_ENABLE leaked on {locked_id}")
                self.assertIn("DISABLE_AFMF=1", res_lock.stdout)

            # Early SteamVR (250820) and -vr bypass also scrub inherited AFMF_ENABLE=1
            res_svr = subprocess.run(
                [str(RUN), "/usr/bin/env"],
                env={**env, "SteamAppId": "250820", "AFMF_ENABLE": "1"},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_svr.returncode, 0, res_svr.stderr)
            self.assertNotIn("AFMF_ENABLE=1", res_svr.stdout)
            self.assertIn("DISABLE_AFMF=1", res_svr.stdout)

            # 6) Stage 1 fast-crash recovery (< 20s) persists USE_AFMF=0 so next launch auto-disables AFMF
            crash_env = {**env, "GAMEID": "7101"}
            res_crash = subprocess.run(
                [str(RUN), "/bin/sh", "-c", "exit 1"],
                env=crash_env, text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_crash.returncode, 1)
            prof_7101 = (home / ".config/steam-auto-profiler/profiles/7101.env").read_text(encoding="utf-8")
            self.assertIn("USE_AFMF=0", prof_7101)
            res_after_crash = subprocess.run([str(RUN), "--dry-run", "7101"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_after_crash.returncode, 0, res_after_crash.stderr)
            self.assertNotIn("AFMF_ENABLE=1", res_after_crash.stdout)
            self.assertIn("DISABLE_AFMF=1", res_after_crash.stdout)

            # 7) --doctor reports [OK] when installed & env-gated, and [INFO] (never [WARN]) when absent
            res_doc_ok = subprocess.run([str(RUN), "--doctor"], env=env, text=True, capture_output=True, check=False)
            self.assertEqual(res_doc_ok.returncode, 0, res_doc_ok.stderr)
            self.assertIn("[OK] afmf-linux (VK_LAYER_AFMF) installed with strict AFMF_ENABLE=1 env-gate", res_doc_ok.stdout)

            res_doc_abs = subprocess.run(
                [str(RUN), "--doctor"], env={**env, "SAP_AFMF_LAYER_DIRS": str(empty_layer_dir)},
                text=True, capture_output=True, check=False,
            )
            self.assertEqual(res_doc_abs.returncode, 0, res_doc_abs.stderr)
            self.assertIn("[INFO] afmf-linux (VK_LAYER_AFMF) not installed", res_doc_abs.stdout)
            self.assertNotIn("[WARN] afmf-linux", res_doc_abs.stdout)


if __name__ == "__main__":
    unittest.main()


_SAP_TEST_STATE_DIR = None
_SAP_TEST_CONFIG_DIR = None
_SAP_TEST_USB_DIR = None
_SAP_ORIG_XDG_ENV = {}


def setUpModule():
    import os as _os
    import tempfile as _tempfile
    global _SAP_TEST_STATE_DIR, _SAP_TEST_CONFIG_DIR, _SAP_TEST_USB_DIR, _SAP_ORIG_XDG_ENV
    _SAP_ORIG_XDG_ENV = {
        k: _os.environ.get(k)
        for k in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "SAP_USB_DIR")
    }
    _os.environ.pop("XDG_CONFIG_HOME", None)
    _os.environ.pop("XDG_DATA_HOME", None)
    _SAP_TEST_STATE_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-state-")
    _SAP_TEST_CONFIG_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-config-")
    _SAP_TEST_USB_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-usb-")
    _os.environ["XDG_CONFIG_HOME"] = _SAP_TEST_CONFIG_DIR.name
    _os.environ["XDG_STATE_HOME"] = _SAP_TEST_STATE_DIR.name
    _os.environ["SAP_USB_DIR"] = _SAP_TEST_USB_DIR.name


def tearDownModule():
    import os as _os
    global _SAP_TEST_STATE_DIR, _SAP_TEST_CONFIG_DIR, _SAP_TEST_USB_DIR, _SAP_ORIG_XDG_ENV
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
    if _SAP_TEST_USB_DIR is not None:
        _SAP_TEST_USB_DIR.cleanup()
        _SAP_TEST_USB_DIR = None
