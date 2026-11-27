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

    def test_install_and_uninstall_includes_vr_run_ui_and_desktop_entry(self):
        expected = (
            "steam-auto-run",
            "steam-auto-detect",
            "steam-auto-sync",
            "steam-net-boost",
            "vr-run",
            "steam-auto-ui",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home.mkdir()
            data_home = home / ".local" / "share"
            env = {
                **os.environ,
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_DATA_HOME": str(data_home),
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

            desktop = data_home / "applications" / "steam-auto-profiler.desktop"
            self.assertTrue(desktop.is_file(), "Missing desktop entry")
            desktop_text = desktop.read_text(encoding="utf-8")
            self.assertIn("steam-auto-ui --gui", desktop_text)

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
            self.assertFalse(desktop.exists(), "Failed to uninstall desktop entry")

    def test_with_steam_controller_installs_and_uninstalls_udev_rules(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            home = tmp_path / "home"
            home.mkdir()
            udev_dir = tmp_path / "udev-rules"
            env = {
                **os.environ,
                "HOME": str(home),
                "XDG_CONFIG_HOME": str(home / ".config"),
                "XDG_DATA_HOME": str(home / ".local" / "share"),
                "STEAM_AUTO_PROFILER_SYSTEM_BIN_DIR": str(tmp_path / "sys-bin"),
                "STEAM_AUTO_PROFILER_SUDOERS_DIR": str(tmp_path / "sudoers.d"),
                "STEAM_AUTO_PROFILER_UDEV_DIR": str(udev_dir),
            }
            res_help = subprocess.run([str(ROOT / "install.sh"), "--help"], env=env, text=True, capture_output=True)
            self.assertEqual(res_help.returncode, 0)
            self.assertIn("--with-steam-controller", res_help.stdout)

            res = subprocess.run(
                [str(ROOT / "install.sh"), "--with-steam-controller"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            rule_file = udev_dir / "61-steam-controller-2026.rules"
            self.assertTrue(rule_file.is_file(), "Missing 61-steam-controller-2026.rules")
            text = rule_file.read_text(encoding="utf-8")
            for expected_token in (
                'idVendor}=="28de"',
                '1302|1304|1005|1007',
                'KERNEL=="hidraw*"',
                'SUBSYSTEM=="tty"',
                'KERNEL=="ttyACM*"',
                'TAG+="uaccess"',
                'GROUP="uucp"',
                'MODE="0660"',
                'ENV{ID_MM_DEVICE_IGNORE}="1"',
                'ATTR{power/control}="on"',
                'ATTR{power/autosuspend}="-1"',
            ):
                self.assertIn(expected_token, text)

            res_un = subprocess.run(
                [str(ROOT / "install.sh"), "--uninstall"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_un.returncode, 0, res_un.stderr)
            self.assertFalse(rule_file.exists(), "Failed to uninstall 61-steam-controller-2026.rules")


if __name__ == "__main__":
    unittest.main()
