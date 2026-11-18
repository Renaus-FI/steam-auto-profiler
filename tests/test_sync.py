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
        self.assertIn("Synced", result.stdout)

    def test_sanitize_dry_run_migrates_messy_flags(self):
        messy = (
            "PROTON_FSR4_RDNA3_UPGRADE=1 PROTON_ENABLE_WAYLAND=1 "
            "XWAYLAND=1 ENABLE_LAYER_MESA_ANTI_LAG=1 "
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
        result = self.run_sync("--migrate-cachy-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("730.env", result.stdout)
        migrated = self.home / ".config/steam-auto-profiler/profiles/730.env"
        self.assertTrue(migrated.exists())
        content = migrated.read_text(encoding="utf-8")
        self.assertIn("USE_SHARPEN=1", content)
        self.assertIn("AUTO_PRESET='competitive'", content)
        self.assertIn("USE_NET_OPT=1", content)


if __name__ == "__main__":
    unittest.main()
