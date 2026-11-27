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

    def test_vr_detection_openvr_openxr_and_vrmanifest(self):
        cases = (
            ("2001", "Half Life VR", ("bin/openvr_api.dll", "game.exe")),
            ("2002", "OpenXR Flight", ("openxr_loader.dll", "sim.exe")),
            ("2003", "Manifest VR", ("actions/game.vrmanifest", "app.exe")),
        )
        for appid, name, files in cases:
            with self.subTest(appid=appid):
                self.create_game(appid, name, files=files)
                report = self.classify(appid)
                self.assertTrue(report["is_vr"])
                self.assertEqual(report["class"], "vr")
                env = os.environ.copy()
                env["HOME"] = str(self.home)
                raw = subprocess.run(
                    [str(DETECT), appid],
                    env=env,
                    text=True,
                    capture_output=True,
                    check=True,
                ).stdout
                self.assertIn("AUTO_IS_VR=1", raw)

    def test_upscaler_sdk_info_fsr31_vs_legacy(self):
        self.create_game("2010", "Modern FSR4", files=("amd_fidelityfx_upscaler_dx12.dll", "game.exe"))
        modern = self.classify("2010")
        self.assertIn("FidelityFX 3.1+", modern["upscaler_info"])
        self.assertIn("PROTON_FSR4_UPGRADE=1", modern["upscaler_info"])
        self.assertNotIn("will not hook", modern["upscaler_info"])

        self.create_game("2011", "Legacy Upscaler", files=("ffx_fsr2_api_x64.dll", "nvngx_dlss.dll", "game.exe"))
        legacy = self.classify("2011")
        self.assertIn("Legacy upscaler", legacy["upscaler_info"])
        self.assertIn("will not hook", legacy["upscaler_info"])
        self.assertIn("USE_OPTISCALER=1", legacy["upscaler_info"])

    def test_non_steam_shortcut_binary_vdf_detection(self):
        import struct

        sc_dir = self.common / "NonSteam_Game"
        sc_dir.mkdir(parents=True)
        (sc_dir / "nvngx_dlss.dll").touch()
        (sc_dir / "game.exe").touch()

        def pack_str(k: str, v: str) -> bytes:
            return b"\x01" + k.encode() + b"\x00" + v.encode() + b"\x00"

        def pack_u32(k: str, v: int) -> bytes:
            return b"\x02" + k.encode() + b"\x00" + struct.pack("<I", v)

        vdf_bytes = (
            b"\x00shortcuts\x00"
            + b"\x000\x00"
            + pack_u32("appid", 3123456789)
            + pack_str("AppName", "Cyber Shortcut")
            + pack_str("Exe", f'"{sc_dir / "game.exe"}"')
            + pack_str("StartDir", f'"{sc_dir}"')
            + pack_str("LaunchOptions", "steam-auto-run %command%")
            + b"\x08"
            + b"\x001\x00"
            + pack_u32("appid", 3987654321)
            + pack_str("AppName", "VR Shortcut")
            + pack_str("Exe", '"/opt/vr/app.exe"')
            + pack_str("StartDir", '"/opt/vr"')
            + pack_str("LaunchOptions", "vr-run %command% -vr")
            + b"\x08"
            + b"\x08"
        )
        vdf_path = self.steam / "userdata" / "100" / "config" / "shortcuts.vdf"
        vdf_path.parent.mkdir(parents=True, exist_ok=True)
        vdf_path.write_bytes(vdf_bytes)

        rep1 = self.classify("3123456789")
        self.assertEqual(rep1["source"], "shortcut")
        self.assertEqual(rep1["game"], "Cyber Shortcut")
        self.assertTrue(rep1["has_dlss"])
        self.assertIn("USE_OPTISCALER=1", rep1["upscaler_info"])

        rep2 = self.classify("3987654321")
        self.assertEqual(rep2["source"], "shortcut")
        self.assertEqual(rep2["game"], "VR Shortcut")
        self.assertTrue(rep2["is_vr"])
        self.assertEqual(rep2["class"], "vr")

    def test_hunt_showdown_594650_safe_defaults_and_bleeding_edge_guard(self):
        self.create_game("594650", "Hunt: Showdown 1896", files=("hunt.exe",))
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["WAYLAND_DISPLAY"] = "wayland-0"
        env["BLEEDING_EDGE"] = "1"
        raw = subprocess.run(
            [str(DETECT), "--json", "594650"],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        report = json.loads(raw)
        self.assertEqual(report["class"], "competitive-anticheat")
        self.assertTrue(report["xwayland"])
        self.assertTrue(report["safedx12"])
        self.assertFalse(report["native_ags"])
        self.assertTrue(report["net_qos_hook"])
        self.assertFalse(report["bleeding_edge"])
        tokens = report["proton_add_config"].split(",")
        self.assertNotIn("wayland", tokens)
        self.assertNotIn("vkd3dbindlesstb", tokens)
        self.assertNotIn("nativeags", tokens)
        self.assertNotIn("wow64", tokens)

        # Standard title with BLEEDING_EDGE=1 enables bleeding_edge + wow64 + fsr4 tokens
        self.create_game("2099", "Standard Experimental", files=("game.exe",))
        raw_std = subprocess.run(
            [str(DETECT), "--json", "2099"],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        std_report = json.loads(raw_std)
        self.assertTrue(std_report["bleeding_edge"])
        std_tokens = std_report["proton_add_config"].split(",")
        self.assertIn("wow64", std_tokens)
        self.assertIn("fsr4", std_tokens)


if __name__ == "__main__":
    unittest.main()


_SAP_TEST_STATE_DIR = None
_SAP_TEST_USB_DIR = None
_SAP_ORIG_XDG_ENV = {}


def setUpModule():
    import os as _os
    import tempfile as _tempfile
    global _SAP_TEST_STATE_DIR, _SAP_TEST_USB_DIR, _SAP_ORIG_XDG_ENV
    _SAP_ORIG_XDG_ENV = {
        k: _os.environ.get(k)
        for k in ("XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "SAP_USB_DIR")
    }
    _os.environ.pop("XDG_CONFIG_HOME", None)
    _os.environ.pop("XDG_DATA_HOME", None)
    _SAP_TEST_STATE_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-state-")
    _SAP_TEST_USB_DIR = _tempfile.TemporaryDirectory(prefix="sap-test-usb-")
    _os.environ["XDG_STATE_HOME"] = _SAP_TEST_STATE_DIR.name
    _os.environ["SAP_USB_DIR"] = _SAP_TEST_USB_DIR.name


def tearDownModule():
    import os as _os
    global _SAP_TEST_STATE_DIR, _SAP_TEST_USB_DIR, _SAP_ORIG_XDG_ENV
    for k, val in _SAP_ORIG_XDG_ENV.items():
        if val is None:
            _os.environ.pop(k, None)
        else:
            _os.environ[k] = val
    _SAP_ORIG_XDG_ENV = {}
    if _SAP_TEST_STATE_DIR is not None:
        _SAP_TEST_STATE_DIR.cleanup()
        _SAP_TEST_STATE_DIR = None
    if _SAP_TEST_USB_DIR is not None:
        _SAP_TEST_USB_DIR.cleanup()
        _SAP_TEST_USB_DIR = None
