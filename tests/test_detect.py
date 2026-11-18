import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DETECT = ROOT / "bin" / "steam-auto-detect"


class DetectTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        self.steam = self.home / ".local/share/Steam"
        self.apps = self.steam / "steamapps"
        self.common = self.apps / "common"
        self.common.mkdir(parents=True)

    def tearDown(self):
        self.tmp.cleanup()

    def create_game(self, appid, name, files=(), dirs=()):
        game_dir = self.common / name.replace(" ", "_")
        game_dir.mkdir()
        for relative in files:
            path = game_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        for relative in dirs:
            (game_dir / relative).mkdir(parents=True, exist_ok=True)
        acf = self.apps / f"appmanifest_{appid}.acf"
        acf.write_text(
            f'"AppState"\n{{\n\t"appid"\t\t"{appid}"\n\t"installdir"\t\t"{game_dir.name}"\n\t"name"\t\t"{name}"\n}}\n',
            encoding="utf-8",
        )
        return game_dir

    def classify(self, appid):
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        result = subprocess.run(
            [str(DETECT), "--json", str(appid)],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)

    def test_tier1_eac_or_battleye(self):
        self.create_game("1001", "Anti Cheat", files=("EasyAntiCheat/EasyAntiCheat.exe",))
        report = self.classify("1001")
        self.assertEqual(report["class"], "competitive-anticheat")
        self.assertFalse(report["sharpen_layer"])
        self.assertIn("proton_add_config", report)

    def test_tier2_native_fsr(self):
        self.create_game("1002", "Native FSR", files=("amdxcffx64.dll",))
        report = self.classify("1002")
        self.assertEqual(report["class"], "native-fsr")
        self.assertTrue(report["has_fsr"])
        self.assertIn("fsr4", report["proton_add_config"].split(","))

    def test_modular_fidelityfx_wins_over_streamline_dlls(self):
        cases = (
            ("1006", "Modular Upscaler", "amd_fidelityfx_upscaler_dx12.dll"),
            ("1007", "Modular Loader", "amd_fidelityfx_loader_dx12.dll"),
        )
        for appid, name, fidelityfx_dll in cases:
            with self.subTest(fidelityfx_dll=fidelityfx_dll):
                self.create_game(
                    appid,
                    name,
                    files=(fidelityfx_dll, "nvngx_dlssd.dll", "sl.interposer.dll"),
                )
                report = self.classify(appid)
                self.assertEqual(report["class"], "native-fsr4")
                self.assertFalse(report["optiscaler"])

    def test_tier3_dlss_xess_cef(self):
        self.create_game(
            "1003",
            "Legacy",
            files=("nvngx_dlss.dll", "libxess.dll", "launcher/EADesktop.exe"),
        )
        report = self.classify("1003")
        self.assertEqual(report["class"], "legacy-upscaler")
        self.assertTrue(report["has_dlss"])
        self.assertTrue(report["has_xess"])

    def test_tier4_standard(self):
        self.create_game("1004", "Classic", files=("Game.exe",))
        report = self.classify("1004")
        self.assertEqual(report["class"], "standard")
        self.assertFalse(report["has_dlss"])
        self.assertFalse(report["has_xess"])
        self.assertFalse(report["has_fsr"])
        self.assertNotIn("fsr4", report["proton_add_config"].split(","))

    def test_saved_profile_overrides_compat_tokens(self):
        self.create_game("1005", "Profiled", files=("Game.exe",))
        profile_dir = self.home / ".config/steam-auto-profiler/profiles"
        profile_dir.mkdir(parents=True)
        (profile_dir / "1005.env").write_text(
            "USE_XWAYLAND=1\n"
            "USE_MLFG=1\n"
            "USE_SDL=1\n"
            "USE_SAFEDX12=1\n"
            "PROTON_NO_NTSYNC=1\n",
            encoding="utf-8",
        )
        report = self.classify("1005")
        tokens = report["proton_add_config"].split(",")
        self.assertIn("mlfg", tokens)
        self.assertIn("sdlinput", tokens)
        self.assertIn("nontsync", tokens)
        self.assertNotIn("vkd3dbindlesstb", tokens)
        self.assertNotIn("dxvklowlatency", tokens)


if __name__ == "__main__":
    unittest.main()
