import importlib.machinery
import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file.resolve()) if False else Path(__file__).resolve().parents[1]
SYNC = ROOT / "bin" / "steam-auto-sync"

SAMPLE_VDF = '''"UserLocalConfigStore"
{
    "software"
    {
        "Valve"
        {
            "Steam"
            {
                "apps"
                {
                    "730"
                    {
                        "LaunchOptions"        "%command%"
                        "OtherSetting"         "preserved"
                    }
                }
            }
        }
    }
}
'''


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.steam = self.home / ".local/share/Steam"
        steamapps = self.steam / "steamapps"
        (steamapps / "common" / "Counter_Strike").mkdir(parents=True)
        (steamapps / "appmanifest_730.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"730"\n\t"installdir"\t\t"Counter_Strike"\n\t"name"\t\t"Counter-Strike 2"\n}\n',
            encoding="utf-8",
        )
        config = self.steam / "userdata/100/config/localconfig.vdf"
        config.parent.mkdir(parents=True)
        config.write_text(SAMPLE_VDF, encoding="utf-8")
        self.config = config

    def tearDown(self):
        self.tmp.cleanup()

    def run_sync(self, *args):
        import os
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        return subprocess.run(
            [str(SYNC), *args],
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_dry_run_span_editing(self):
        loader = importlib.machinery.SourceFileLoader("steam_auto_sync", str(SYNC))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        app_launch, app_close, apps_close = module.find_launch_options(SAMPLE_VDF)
        current, start, end = app_launch["730"]
        replacement = current.replace("%command%", "steam-auto-run %command%", 1)
        escaped = replacement.replace("\\", "\\\\").replace('"', '\\"')
        output = SAMPLE_VDF[:start] + f'"{escaped}"' + SAMPLE_VDF[end:]
        self.assertIn("steam-auto-run %command%", output)
        self.assertIn('"OtherSetting"         "preserved"', output)

    def test_dry_run_cli(self):
        result = self.run_sync("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[DRY-RUN]", result.stdout)
        self.assertIn("730", result.stdout)

    def test_remove_dry_run(self):
        self.config.write_text(SAMPLE_VDF.replace("%command%", "steam-auto-run %command%"), encoding="utf-8")
        result = self.run_sync("--dry-run", "--remove")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Removed", result.stdout)

    def test_report_is_read_only(self):
        result = self.run_sync("--report")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("AppID", result.stdout)
        self.assertIn("Compat Tokens", result.stdout)
        self.assertIn("Profile", result.stdout)
        self.assertIn("Synced", result.stdout)

    def test_report_shows_saved_profile_and_overrides(self):
        profile_dir = self.home / ".config/steam-auto-profiler/profiles"
        profile_dir.mkdir(parents=True)
        (profile_dir / "730.env").write_text(
            "USE_XWAYLAND=1\n"
            "USE_MLFG=1\n"
            "USE_SDL=1\n"
            "USE_SAFEDX12=1\n"
            "PROTON_NO_NTSYNC=1\n",
            encoding="utf-8",
        )
        result = self.run_sync("--report")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Profile", result.stdout)
        self.assertIn("Saved", result.stdout)
        self.assertIn("mlfg", result.stdout)
        self.assertIn("sdlinput", result.stdout)
        self.assertIn("nontsync", result.stdout)
        self.assertNotIn("vkd3dbindlesstb", result.stdout)

    def test_sanitize_dry_run_migrates_messy_flags(self):
        messy = (
            "PROTON_FSR4_RDNA3_UPGRADE=1 PROTON_ENABLE_WAYLAND=0 "
            "ENABLE_LAYER_MESA_ANTI_LAG=1 "
            "cachy-run game-performance steam-auto-run "
            "%command% -dx12"
        )
        self.config.write_text(
            SAMPLE_VDF.replace("%command%", messy),
            encoding="utf-8",
        )
        result = self.run_sync("--sanitize", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("730", result.stdout)

        loader = importlib.machinery.SourceFileLoader("steam_auto_sync_sanitize", str(SYNC))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        replacement, profile = module.sanitize_launch_option(
            "730", messy, self.home / ".config/steam-auto-profiler/profiles", dry_run=True
        )
        self.assertEqual(replacement, "steam-auto-run %command% -dx12")
        self.assertEqual(profile["USE_XWAYLAND"], "1")

    def test_migrate_cachy_run_profiles(self):
        legacy = self.home / ".config/cachy-run/profiles"
        legacy.mkdir(parents=True)
        (legacy / "730.env").write_text(
            "USE_RCAS=1\n"
            "AUTO_PRESET='shooter'\n",
            encoding="utf-8",
        )
        target = self.home / ".config/steam-auto-profiler/profiles"
        target.mkdir(parents=True)
        (target / "730.env").write_text(
            "USE_NET_OPT=1\nUSE_NET_OPT=1\n",
            encoding="utf-8",
        )
        result = self.run_sync("--migrate-cachy-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("730.env", result.stdout)
        migrated = self.home / ".config/steam-auto-profiler/profiles/730.env"
        self.assertTrue(migrated.exists())
        content = migrated.read_text(encoding="utf-8")
        self.assertIn("USE_SHARPEN=1", content)
        self.assertIn("AUTO_PRESET='competitive'", content)
        self.assertIn("USE_NET_OPT=1", content)
        keys = [
            line.split("=", 1)[0]
            for line in content.splitlines()
            if "=" in line
        ]
        self.assertEqual(len(keys), len(set(keys)))

    def test_sanitize_cleans_orphan_app_launch_entries(self):
        orphan_vdf = '''"UserLocalConfigStore"
{
    "software"
    {
        "Valve"
        {
            "Steam"
            {
                "apps"
                {
                    "730"
                    {
                        "LaunchOptions"        "%command%"
                    }
                    "999999"
                    {
                        "LaunchOptions"        "cachy-run game-performance PROTON_FSR4_RDNA3_UPGRADE=1 %command%"
                    }
                }
            }
        }
    }
}
'''
        self.config.write_text(orphan_vdf, encoding="utf-8")
        result = self.run_sync("--sanitize")
        self.assertEqual(result.returncode, 0, result.stderr)
        updated = self.config.read_text(encoding="utf-8")
        self.assertIn("steam-auto-run %command%", updated)
        self.assertNotIn("cachy-run", updated)
        self.assertNotIn("PROTON_FSR4_RDNA3_UPGRADE=1", updated)
        orphan_profile = (
            self.home / ".config/steam-auto-profiler/profiles/999999.env"
        )
        self.assertFalse(orphan_profile.exists())

    def test_sanitize_wayland_fsr4_installed_has_no_redundant_profile(self):
        launch = (
            "PROTON_ENABLE_WAYLAND=1 "
            "PROTON_FSR4_RDNA3_UPGRADE=1 game-performance %command%"
        )
        loader = importlib.machinery.SourceFileLoader(
            "steam_auto_sync_wayland", str(SYNC)
        )
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        profile_dir = self.home / ".config/steam-auto-profiler/profiles"
        replacement, profile = module.sanitize_launch_option(
            "730", launch, profile_dir
        )
        self.assertIn("steam-auto-run %command%", replacement)
        self.assertNotIn("USE_XWAYLAND", profile)
        self.assertFalse((profile_dir / "730.env").exists())

    def test_preserves_vr_run_in_sync_sanitize_and_orphans(self):
        vr_vdf = '''"UserLocalConfigStore"
{
    "software"
    {
        "Valve"
        {
            "Steam"
            {
                "apps"
                {
                    "730"
                    {
                        "LaunchOptions"        "vr-run %command% -vr"
                    }
                    "546560"
                    {
                        "LaunchOptions"        "PROTON_LOG=1 /usr/local/bin/vr-run %command%"
                    }
                }
            }
        }
    }
}
'''
        self.config.write_text(vr_vdf, encoding="utf-8")

        # Normal sync dry-run must not rewrite vr-run %command%
        res_sync = self.run_sync("--dry-run")
        self.assertEqual(res_sync.returncode, 0, res_sync.stderr)
        self.assertNotIn("[730]", res_sync.stdout)

        # Sanitize dry-run must not rewrite vr-run (installed OR orphan with PROTON_LOG=1)
        res_san = self.run_sync("--sanitize", "--dry-run")
        self.assertEqual(res_san.returncode, 0, res_san.stderr)
        self.assertNotIn("[730]", res_san.stdout)
        self.assertNotIn("[546560]", res_san.stdout)

        # Report marks vr-run titles cleanly as VR
        res_rep = self.run_sync("--report")
        self.assertEqual(res_rep.returncode, 0, res_rep.stderr)
        self.assertIn("VR", res_rep.stdout)

        # Direct sanitize_launch_option call leaves vr-run intact
        loader = importlib.machinery.SourceFileLoader("steam_auto_sync_vr", str(SYNC))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        replacement, profile = module.sanitize_launch_option(
            "546560",
            "PROTON_LOG=1 vr-run %command% -vr",
            self.home / ".config/steam-auto-profiler/profiles",
            dry_run=True,
        )
        self.assertEqual(replacement, "PROTON_LOG=1 vr-run %command% -vr")
        self.assertEqual(profile, {})

    def test_auto_assigns_vr_run_to_newly_installed_vr_title(self):
        vr_dir = self.steam / "steamapps" / "common" / "Alyx_VR"
        vr_dir.mkdir(parents=True)
        (vr_dir / "openvr_api.dll").touch()
        (vr_dir / "hlvr.exe").touch()
        (self.steam / "steamapps" / "appmanifest_546560.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"546560"\n\t"installdir"\t\t"Alyx_VR"\n\t"name"\t\t"Half-Life: Alyx"\n}\n',
            encoding="utf-8",
        )
        res = self.run_sync()
        combined = (res.stdout + res.stderr).lower()
        if res.returncode != 0 and "running" in combined:
            self.skipTest("Steam is currently running on host")
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        updated = self.config.read_text(encoding="utf-8")
        self.assertIn('"546560"', updated)
        self.assertIn('"LaunchOptions"\t\t"vr-run %command%"', updated)
        self.assertIn("steam-auto-run %command%", updated)

    def test_report_includes_non_steam_shortcuts_read_only(self):
        import struct

        def pack_str(k: str, v: str) -> bytes:
            return b"\x01" + k.encode() + b"\x00" + v.encode() + b"\x00"

        def pack_u32(k: str, v: int) -> bytes:
            return b"\x02" + k.encode() + b"\x00" + struct.pack("<I", v)

        vdf_bytes = (
            b"\x00shortcuts\x00"
            + b"\x000\x00"
            + pack_u32("appid", 3456789012)
            + pack_str("AppName", "Custom VR Mod")
            + pack_str("Exe", '"/opt/vrmod/start.sh"')
            + pack_str("StartDir", '"/opt/vrmod"')
            + pack_str("LaunchOptions", "vr-run %command% -vr")
            + b"\x08"
            + b"\x08"
        )
        vdf_path = self.steam / "userdata" / "100" / "config" / "shortcuts.vdf"
        vdf_path.write_bytes(vdf_bytes)

        res = self.run_sync("--report")
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("Source", res.stdout)
        self.assertIn("Custom VR Mod", res.stdout)
        self.assertIn("shortcut", res.stdout)
        self.assertIn("VR", res.stdout)
        # Binary shortcuts.vdf must remain byte-for-byte untouched
        self.assertEqual(vdf_path.read_bytes(), vdf_bytes)

    def test_sanitize_strips_retired_proton_flags_and_migrates_mesa27_flags(self):
        loader = importlib.machinery.SourceFileLoader("steam_auto_sync_mesa27", str(SYNC))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        profile_dir = self.home / ".config/steam-auto-profiler/profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)
        # Seed existing profile with retired vars to verify they get purged
        (profile_dir / "730.env").write_text(
            "PROTON_ENABLE_HDR=1\n"
            "PROTON_VKD3D_HEAP=1\n"
            "WINEPULSE_FAST_POLLING=1\n"
            "USE_SDL=1\n",
            encoding="utf-8",
        )

        messy = (
            "PROTON_ENABLE_HDR=1 PROTON_VKREFLEX=1 PROTON_MEDIA_USE_GST=1 "
            "PROTON_FSR3_UPGRADE=1 PROTON_VKD3D_HEAP=1 WINEPULSE_FAST_POLLING=1 "
            "RADV_PERFTEST=sam,video_decode,transfer_queue "
            "LOW_LATENCY_LAYER=1 LOW_LATENCY_LAYER_REFLEX=1 "
            "NATIVE_ANTILAG=1 %command% -dx12"
        )
        replacement, profile = module.sanitize_launch_option("730", messy, profile_dir)
        self.assertEqual(replacement, "steam-auto-run %command% -dx12")
        self.assertEqual(profile.get("USE_TRANSFER_QUEUE"), "1")
        self.assertEqual(profile.get("USE_VK_VIDEO_DECODE"), "1")
        self.assertEqual(profile.get("USE_REFLEX_LAYER"), "1")
        self.assertEqual(profile.get("USE_NATIVE_ANTILAG"), "1")
        for retired in module.RETIRED_PROTON_VARS:
            self.assertNotIn(retired, profile)

        written = (profile_dir / "730.env").read_text(encoding="utf-8")
        self.assertIn("USE_TRANSFER_QUEUE=1", written)
        self.assertIn("USE_VK_VIDEO_DECODE=1", written)
        self.assertIn("USE_REFLEX_LAYER=1", written)
        self.assertIn("USE_NATIVE_ANTILAG=1", written)
        self.assertIn("USE_SDL=1", written)
        for retired in module.RETIRED_PROTON_VARS:
            self.assertNotIn(retired, written)

        # Retired-only launch string strips cleanly without creating a redundant profile
        clean_rep, clean_prof = module.sanitize_launch_option(
            "999002",
            "PROTON_ENABLE_HDR=1 PROTON_VKREFLEX=1 PROTON_FSR3_UPGRADE=1 WINEPULSE_FAST_POLLING=1 %command%",
            profile_dir,
        )
        self.assertEqual(clean_rep, "steam-auto-run %command%")
        self.assertEqual(clean_prof, {})
        self.assertFalse((profile_dir / "999002.env").exists())

    def test_sanitize_migrates_bleeding_edge_and_steam_controller_flags(self):
        loader = importlib.machinery.SourceFileLoader("steam_auto_sync_bleeding", str(SYNC))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        profile_dir = self.home / ".config/steam-auto-profiler/profiles"
        messy = "BLEEDING_EDGE=1 USE_STEAM_CONTROLLER=1 WAYLANDDRV_RAWINPUT=1 %command% -dx12"
        replacement, profile = module.sanitize_launch_option("361420", messy, profile_dir)
        self.assertEqual(replacement, "steam-auto-run %command% -dx12")
        self.assertEqual(profile.get("USE_BLEEDING_EDGE"), "1")
        self.assertEqual(profile.get("USE_STEAM_CONTROLLER"), "1")
        written = (profile_dir / "361420.env").read_text(encoding="utf-8")
        self.assertIn("USE_BLEEDING_EDGE=1", written)
        self.assertIn("USE_STEAM_CONTROLLER=1", written)


if __name__ == "__main__":
    unittest.main()


_SAP_TEST_STATE_DIR = None
_SAP_ORIG_XDG_ENV = {}


def setUpModule():
    import os as _os
    import tempfile as _tempfile
    global _SAP_TEST_STATE_DIR, _SAP_ORIG_XDG_ENV
    _SAP_ORIG_XDG_ENV = {
        k: _os.environ.get(k)
        for k in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME")
    }
    _os.environ.pop("XDG_CONFIG_HOME", None)
    _os.environ.pop("XDG_DATA_HOME", None)
    _SAP_TEST_STATE_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-state-")
    _os.environ["XDG_STATE_HOME"] = _SAP_TEST_STATE_DIR.name


def tearDownModule():
    import os as _os
    global _SAP_TEST_STATE_DIR, _SAP_ORIG_XDG_ENV
    for k, val in _SAP_ORIG_XDG_ENV.items():
        if val is None:
            _os.environ.pop(k, None)
        else:
            _os.environ[k] = val
    _SAP_ORIG_XDG_ENV = {}
    if _SAP_TEST_STATE_DIR is not None:
        _SAP_TEST_STATE_DIR.cleanup()
        _SAP_TEST_STATE_DIR = None
