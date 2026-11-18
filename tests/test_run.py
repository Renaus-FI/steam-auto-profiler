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


if __name__ == "__main__":
    unittest.main()
