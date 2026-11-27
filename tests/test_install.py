import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallTests(unittest.TestCase):
    def test_help_is_available_in_isolated_home(self):
        with tempfile.TemporaryDirectory() as home:
            result = subprocess.run(
                [str(ROOT / "install.sh"), "--help"],
                env={**os.environ, "HOME": home},
                text=True, capture_output=True,
            )
        self.assertEqual(result.returncode, 0)
        self.assertIn("--with-auto-sync", result.stdout)

    def test_install_and_uninstall_includes_vr_run(self):
        expected = (
            "steam-auto-run",
            "steam-auto-detect",
            "steam-auto-sync",
            "steam-net-boost",
            "vr-run",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home.mkdir()
            env = {
                **os.environ,
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "STEAM_AUTO_PROFILER_SYSTEM_BIN_DIR": str(tmp_path / "sys-bin"),
                "STEAM_AUTO_PROFILER_SUDOERS_DIR": str(tmp_path / "sudoers.d"),
            }
            res_install = subprocess.run(
                [str(ROOT / "install.sh")],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_install.returncode, 0, res_install.stderr)
            bin_dir = home / ".local" / "bin"
            for name in expected:
                target = bin_dir / name
                self.assertTrue(target.is_file(), f"Missing installed script: {name}")
                self.assertTrue(os.access(target, os.X_OK), f"Not executable: {name}")

            res_uninstall = subprocess.run(
                [str(ROOT / "install.sh"), "--uninstall"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_uninstall.returncode, 0, res_uninstall.stderr)
            for name in expected:
                self.assertFalse((bin_dir / name).exists(), f"Failed to uninstall: {name}")


if __name__ == "__main__":
    unittest.main()
