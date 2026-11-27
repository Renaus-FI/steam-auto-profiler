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
