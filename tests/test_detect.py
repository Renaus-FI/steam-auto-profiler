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
        self.assertFalse(report["has_reflex"])
        # v2.2.0: non-anticheat Proton titles default to bleeding_edge=True (wow64 + fsr4)
        self.assertTrue(report["bleeding_edge"])
        tokens = report["proton_add_config"].split(",")
        self.assertIn("wow64", tokens)
        self.assertIn("fsr4", tokens)

        # Opting out via CONSERVATIVE=1 or BLEEDING_EDGE=0 restores baseline tokens
        env = os.environ.copy()
        env["HOME"] = str(self.home)
        env["CONSERVATIVE"] = "1"
        cons_raw = subprocess.run(
            [str(DETECT), "--json", "1004"],
            env=env,
            text=True,
            capture_output=True,
            check=True,
        ).stdout
        cons = json.loads(cons_raw)
        self.assertFalse(cons["bleeding_edge"])
        self.assertNotIn("wow64", cons["proton_add_config"].split(","))
        self.assertNotIn("fsr4", cons["proton_add_config"].split(","))

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

        # Standard title defaults to bleeding_edge + wow64 + fsr4 tokens
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

    def test_smart_experimental_defaults_rdna4_reflex_and_guards(self):
        drm = self.home / "drm-rdna4"
        dev = drm / "card0" / "device"
        dev.mkdir(parents=True)
        (dev / "vendor").write_text("0x1002\n", encoding="utf-8")
        (dev / "device").write_text("0x7550\n", encoding="utf-8")
        (dev / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

        base_env = os.environ.copy()
        for k in ("BLEEDING_EDGE", "TRANSFER_QUEUE", "NATIVE_ANTILAG", "REFLEX_LAYER", "VK_VIDEO_DECODE", "CONSERVATIVE", "MLFG"):
            base_env.pop(k, None)
        base_env["HOME"] = str(self.home)
        base_env["SAP_DRM_DIR"] = str(drm)

        # 1) Non-anticheat title with sl.reflex.dll auto-enables all RDNA 4 + Reflex + Bleeding-Edge defaults
        self.create_game("3101", "Forza Horizon 6", files=("ForzaHorizon6.exe", "sl.reflex.dll", "amd_fidelityfx_upscaler_dx12.dll"))
        rep_fh = json.loads(subprocess.run(
            [str(DETECT), "--json", "3101"], env=base_env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertTrue(rep_fh["has_reflex"])
        self.assertTrue(rep_fh["reflex_layer"])
        self.assertTrue(rep_fh["transfer_queue"])
        self.assertTrue(rep_fh["native_antilag"])
        self.assertTrue(rep_fh["vk_video_decode"])
        self.assertTrue(rep_fh["bleeding_edge"])
        self.assertEqual(rep_fh["smart_defaults"]["USE_BLEEDING_EDGE"], "1")
        self.assertEqual(rep_fh["smart_defaults"]["USE_REFLEX_LAYER"], "1")
        self.assertEqual(rep_fh["smart_defaults"]["USE_TRANSFER_QUEUE"], "1")
        self.assertEqual(rep_fh["smart_defaults"]["USE_NATIVE_ANTILAG"], "1")
        self.assertEqual(rep_fh["smart_defaults"]["USE_VK_VIDEO_DECODE"], "1")
        self.assertIn("lowlatencylayer", rep_fh["proton_add_config"].split(","))
        self.assertIn("wow64", rep_fh["proton_add_config"].split(","))

        # 2) MLFG=1 disables native_antilag and reflex_layer
        rep_mlfg = json.loads(subprocess.run(
            [str(DETECT), "--json", "3101"], env={**base_env, "MLFG": "1"}, text=True, capture_output=True, check=True
        ).stdout)
        self.assertFalse(rep_mlfg["native_antilag"])
        self.assertFalse(rep_mlfg["reflex_layer"])
        self.assertNotIn("lowlatencylayer", rep_mlfg["proton_add_config"].split(","))

        # 3) competitive-anticheat with sl.reflex.dll keeps driver-level RDNA 4 defaults but blocks bleeding_edge & reflex_layer
        self.create_game("3102", "AC Reflex Shooter", files=("game.exe", "sl.reflex.dll", "EasyAntiCheat/EasyAntiCheat.exe"))
        rep_ac = json.loads(subprocess.run(
            [str(DETECT), "--json", "3102"], env=base_env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertEqual(rep_ac["class"], "competitive-anticheat")
        self.assertTrue(rep_ac["has_reflex"])
        self.assertTrue(rep_ac["transfer_queue"])
        self.assertTrue(rep_ac["native_antilag"])
        self.assertTrue(rep_ac["vk_video_decode"])
        self.assertFalse(rep_ac["reflex_layer"])
        self.assertFalse(rep_ac["bleeding_edge"])
        self.assertNotIn("lowlatencylayer", rep_ac["proton_add_config"].split(","))
        self.assertNotIn("wow64", rep_ac["proton_add_config"].split(","))

        # 4) Native Linux game hard-forces bleeding_edge=False and reflex_layer=False
        self.create_game("3103", "Native Linux Title", files=("game.x86_64",))
        rep_nat = json.loads(subprocess.run(
            [str(DETECT), "--json", "3103"], env={**base_env, "BLEEDING_EDGE": "1"}, text=True, capture_output=True, check=True
        ).stdout)
        self.assertEqual(rep_nat["runtime"], "native_linux")
        self.assertFalse(rep_nat["bleeding_edge"])
        self.assertFalse(rep_nat["reflex_layer"])

    def test_v23_auto_optiscaler_legacy_upscaler_and_auto_hdr_defaults(self):
        drm_rdna4 = self.home / "drm-rdna4-v23"
        dev4 = drm_rdna4 / "card0" / "device"
        dev4.mkdir(parents=True)
        (dev4 / "vendor").write_text("0x1002\n", encoding="utf-8")
        (dev4 / "device").write_text("0x7550\n", encoding="utf-8")
        (dev4 / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

        drm_rdna2 = self.home / "drm-rdna2-v23"
        dev2 = drm_rdna2 / "card0" / "device"
        dev2.mkdir(parents=True)
        (dev2 / "vendor").write_text("0x1002\n", encoding="utf-8")
        (dev2 / "device").write_text("0x73bf\n", encoding="utf-8")
        (dev2 / "uevent").write_text("PCI_ID=1002:73BF\n", encoding="utf-8")

        mock_bin = self.home / "mock-bin-v23"
        mock_bin.mkdir()
        ks = mock_bin / "kscreen-doctor"
        ks.write_text("#!/bin/sh\necho 'Output: 1 DP-1'\n", encoding="utf-8")
        ks.chmod(0o755)

        base_env = os.environ.copy()
        for k in (
            "OPTISCALER", "USE_OPTISCALER", "CONSERVATIVE", "USE_CONSERVATIVE",
            "AUTO_HDR_SWITCH", "DXVK_NO_HDR", "XWAYLAND", "USE_XWAYLAND",
        ):
            base_env.pop(k, None)
        base_env.update({
            "HOME": str(self.home),
            "SAP_DRM_DIR": str(drm_rdna4),
            "WAYLAND_DISPLAY": "wayland-0",
            "PATH": f"{mock_bin}:{base_env.get('PATH', '/usr/bin:/bin')}",
        })

        # 1) Legacy upscaler on AMD RDNA 4 auto-enables optiscaler + auto_hdr_switch
        self.create_game("4201", "DLSS Legacy Title", files=("game.exe", "nvngx_dlss.dll"))
        rep_leg = json.loads(subprocess.run(
            [str(DETECT), "--json", "4201"], env=base_env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertEqual(rep_leg["class"], "legacy-upscaler")
        self.assertTrue(rep_leg["optiscaler"])
        self.assertTrue(rep_leg["auto_hdr_switch"])
        self.assertEqual(rep_leg["smart_defaults"]["USE_OPTISCALER"], "1")
        self.assertEqual(rep_leg["smart_defaults"]["AUTO_HDR_SWITCH"], "1")

        # 2) Explicit OPTISCALER=0, CONSERVATIVE=1, and DXVK_NO_HDR=1 opt out cleanly
        rep_opt0 = json.loads(subprocess.run(
            [str(DETECT), "--json", "4201"],
            env={**base_env, "OPTISCALER": "0", "AUTO_HDR_SWITCH": "0"},
            text=True, capture_output=True, check=True,
        ).stdout)
        self.assertFalse(rep_opt0["optiscaler"])
        self.assertFalse(rep_opt0["auto_hdr_switch"])

        rep_cons = json.loads(subprocess.run(
            [str(DETECT), "--json", "4201"],
            env={**base_env, "CONSERVATIVE": "1"},
            text=True, capture_output=True, check=True,
        ).stdout)
        self.assertFalse(rep_cons["optiscaler"])

        rep_nohdr = json.loads(subprocess.run(
            [str(DETECT), "--json", "4201"],
            env={**base_env, "DXVK_NO_HDR": "1"},
            text=True, capture_output=True, check=True,
        ).stdout)
        self.assertFalse(rep_nohdr["auto_hdr_switch"])
        self.assertEqual(rep_nohdr["smart_defaults"]["AUTO_HDR_SWITCH"], "0")

        # 3) Non-RDNA3/4 (RDNA 2) keeps optiscaler=False by default
        rep_r2 = json.loads(subprocess.run(
            [str(DETECT), "--json", "4201"],
            env={**base_env, "SAP_DRM_DIR": str(drm_rdna2)},
            text=True, capture_output=True, check=True,
        ).stdout)
        self.assertFalse(rep_r2["optiscaler"])
        self.assertEqual(rep_r2["smart_defaults"]["USE_OPTISCALER"], "0")

        # 4) Native FSR 4, Standard, Anti-Cheat, and Native Linux keep optiscaler=False
        self.create_game("4202", "Native FSR4 Title", files=("game.exe", "amd_fidelityfx_upscaler_dx12.dll", "nvngx_dlss.dll"))
        self.create_game("4203", "AC DLSS Title", files=("game.exe", "nvngx_dlss.dll", "EasyAntiCheat/EasyAntiCheat.exe"))
        self.create_game("4204", "Standard Title", files=("game.exe",))
        self.create_game("4205", "Native Linux DLSS", files=("game.x86_64", "nvngx_dlss.dll"))
        for aid in ("4202", "4203", "4204", "4205"):
            rep = json.loads(subprocess.run(
                [str(DETECT), "--json", aid], env=base_env, text=True, capture_output=True, check=True
            ).stdout)
            self.assertFalse(rep["optiscaler"], f"Expected optiscaler=False for {aid} ({rep['class']})")
            self.assertEqual(rep["smart_defaults"]["USE_OPTISCALER"], "0")

    def test_v24_smart_auto_afmf_heuristics_and_guards(self):
        layer_dir = self.home / "vk-layers"
        layer_dir.mkdir()
        fake_so = self.home / "libafmf-linux.so"
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
        empty_layer_dir = self.home / "vk-layers-empty"
        empty_layer_dir.mkdir()

        base_env = os.environ.copy()
        for k in ("AFMF", "USE_AFMF", "MLFG", "USE_MLFG", "CONSERVATIVE", "USE_CONSERVATIVE"):
            base_env.pop(k, None)
        base_env["HOME"] = str(self.home)
        base_env["SAP_AFMF_LAYER_DIRS"] = str(layer_dir)

        def run_json(appid, extra_env=None):
            env = {**base_env, **(extra_env or {})}
            out = subprocess.run(
                [str(DETECT), "--inspect", "--json", str(appid)],
                env=env, text=True, capture_output=True, check=True,
            ).stdout
            return json.loads(out)

        # 1) Standard 3D game gets AUTO_AFMF=1 when afmf-linux is installed, 0 when absent
        self.create_game("6101", "Standard 3D Game", files=("game.exe", "d3d12.dll"))
        rep_on = run_json("6101")
        self.assertTrue(rep_on["afmf_installed"])
        self.assertTrue(rep_on["afmf"])
        self.assertEqual(rep_on["AUTO_AFMF"], 1)
        self.assertEqual(rep_on["AUTO_HAS_NATIVE_FG"], 0)
        self.assertEqual(rep_on["AUTO_IS_TOOL_OR_2D"], 0)
        self.assertEqual(rep_on["smart_defaults"]["USE_AFMF"], "1")

        # Verify default shell eval output exposes AUTO_HAS_NATIVE_FG, AUTO_IS_TOOL_OR_2D, AUTO_AFMF
        raw_eval = subprocess.run(
            [str(DETECT), "6101"], env=base_env, text=True, capture_output=True, check=True
        ).stdout
        self.assertIn("AUTO_AFMF=1", raw_eval)
        self.assertIn("AUTO_HAS_NATIVE_FG=0", raw_eval)
        self.assertIn("AUTO_IS_TOOL_OR_2D=0", raw_eval)

        rep_absent = run_json("6101", {"SAP_AFMF_LAYER_DIRS": str(empty_layer_dir)})
        self.assertFalse(rep_absent["afmf_installed"])
        self.assertFalse(rep_absent["afmf"])
        self.assertEqual(rep_absent["AUTO_AFMF"], 0)
        self.assertEqual(rep_absent["smart_defaults"]["USE_AFMF"], "0")

        # 2) Native FG libraries set AUTO_HAS_NATIVE_FG=1 and AUTO_AFMF=0
        fg_cases = (
            ("6110", "FSR31 FG Game", ("game.exe", "amd_fidelityfx_framegeneration_dx12.dll")),
            ("6111", "FSR3 FG Game", ("game.exe", "ffx_fsr3fg_x64.dll")),
            ("6112", "FFX Interp Game", ("game.exe", "ffx_frameinterpolation_x64.dll")),
            ("6113", "DLSSG Game", ("game.exe", "nvngx_dlssg.dll")),
            ("6114", "Streamline DLSSG", ("game.exe", "sl.dlss_g.dll")),
            ("6115", "XeFG Lib Game", ("game.exe", "libxefg.dll")),
            ("6116", "XeFG Game", ("game.exe", "xefg.dll")),
            ("6117", "OptiScaler FG Game", ("game.exe", "OptiScaler.ini")),
        )
        for aid, gname, files in fg_cases:
            with self.subTest(fg_game=gname):
                self.create_game(aid, gname, files=files)
                rep = run_json(aid)
                self.assertTrue(rep["has_native_fg"])
                self.assertEqual(rep["AUTO_HAS_NATIVE_FG"], 1)
                self.assertFalse(rep["afmf"])
                self.assertEqual(rep["AUTO_AFMF"], 0)

        # 3) Steam tools/runtimes, pure 2D/text, and Electron/CEF-only apps set AUTO_IS_TOOL_OR_2D=1 and AUTO_AFMF=0
        tool_2d_cases = (
            ("480", "Spacewar", ("spacewar.exe",)),
            ("4690330", "Steam Tool App", ("tool.exe",)),
            ("6120", "Legacy Steam Runtime", ("run.sh",)),
            ("6121", "Proton 11.0", ("proton",)),
            ("6122", "Steamworks Common Redistributables", ("vcredist.exe",)),
            ("6123", "GeoGuessr", ("GeoGuessr.exe",)),
            ("6124", "Dwarf Fortress", ("Dwarf Fortress.exe",)),
            ("6125", "Electron Only App", ("electron.exe", "resources/app.asar", "chrome_elf.dll")),
        )
        for aid, gname, files in tool_2d_cases:
            with self.subTest(tool_or_2d=gname):
                self.create_game(aid, gname, files=files)
                rep = run_json(aid)
                self.assertTrue(rep["is_tool_or_2d"])
                self.assertEqual(rep["AUTO_IS_TOOL_OR_2D"], 1)
                self.assertFalse(rep["afmf"])
                self.assertEqual(rep["AUTO_AFMF"], 0)

        # 3D game with embedded CEF + DX12 DLL is NOT classified as Electron/CEF-only 2D
        self.create_game("6126", "3D Game With CEF", files=("game.exe", "libcef.dll", "d3d12.dll"))
        rep_cef_3d = run_json("6126")
        self.assertFalse(rep_cef_3d["is_tool_or_2d"])
        self.assertTrue(rep_cef_3d["afmf"])

        # 4) Hard locks on competitive-anticheat, AppID 594650, and VR ignore AFMF=1
        self.create_game("6130", "AC Locked", files=("game.exe", "EasyAntiCheat/EasyAntiCheat.exe"))
        self.create_game("594650", "Hunt Showdown 1896", files=("hunt.exe",))
        self.create_game("6131", "VR Locked", files=("game.exe", "openvr_api.dll"))
        for locked_id in ("6130", "594650", "6131"):
            rep_lock = run_json(locked_id, {"AFMF": "1"})
            self.assertFalse(rep_lock["afmf"], f"AFMF must remain locked off for {locked_id}")
            self.assertEqual(rep_lock["AUTO_AFMF"], 0)

        # 5) AFMF=0, CONSERVATIVE=1, and MLFG=1 opt out cleanly; explicit AFMF=1 works on non-locked native-FG title
        self.assertFalse(run_json("6101", {"AFMF": "0"})["afmf"])
        self.assertFalse(run_json("6101", {"CONSERVATIVE": "1"})["afmf"])
        self.assertFalse(run_json("6101", {"MLFG": "1"})["afmf"])
        self.assertTrue(run_json("6113", {"AFMF": "1"})["afmf"])

    def test_v241_no_hang_on_unsafe_shortcut_dirs_empty_installdir_symlinks_or_open_stdin(self):
        import struct
        import time

        # Seed an unrelated game with anti-cheat + DLSS inside $HOME/.local/share/Steam
        self.create_game(
            "7101",
            "Other AC Game",
            files=("game.exe", "EasyAntiCheat/EasyAntiCheat.exe", "nvngx_dlss.dll"),
        )

        # 1) App manifest with empty installdir and another with non-existent installdir
        (self.apps / "appmanifest_7102.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"7102"\n\t"installdir"\t\t""\n\t"name"\t\t"Empty Install Dir"\n}\n',
            encoding="utf-8",
        )
        (self.apps / "appmanifest_7103.acf").write_text(
            '"AppState"\n{\n\t"appid"\t\t"7103"\n\t"installdir"\t\t"DoesNotExist"\n\t"name"\t\t"Missing Dir"\n}\n',
            encoding="utf-8",
        )

        # 2) Game with symlink loop back to its own directory
        loop_dir = self.create_game("7104", "Symlink Loop Game", files=("game.exe", "nvngx_dlss.dll"))
        (loop_dir / "self_loop").symlink_to(loop_dir)

        # 3) Heroic-style non-Steam shortcuts with StartDir=$HOME and StartDir=/
        def pack_str(k: str, v: str) -> bytes:
            return b"\x01" + k.encode() + b"\x00" + v.encode() + b"\x00"

        def pack_u32(k: str, v: int) -> bytes:
            return b"\x02" + k.encode() + b"\x00" + struct.pack("<I", v)

        vdf_bytes = (
            b"\x00shortcuts\x00"
            + b"\x000\x00"
            + pack_u32("appid", 2795151330)
            + pack_str("AppName", "MORDHAU")
            + pack_str("Exe", '"/opt/Heroic/heroic"')
            + pack_str("StartDir", f'"{self.home}"')
            + pack_str("LaunchOptions", '--no-gui "heroic://launch?appName=test"')
            + b"\x08"
            + b"\x001\x00"
            + pack_u32("appid", 2386697165)
            + pack_str("AppName", "Root StartDir Game")
            + pack_str("Exe", '"/usr/bin/flatpak"')
            + pack_str("StartDir", '"/"')
            + pack_str("LaunchOptions", "vr-run %command%")
            + b"\x08"
            + b"\x08"
        )
        vdf_path = self.steam / "userdata" / "100" / "config" / "shortcuts.vdf"
        vdf_path.parent.mkdir(parents=True, exist_ok=True)
        vdf_path.write_bytes(vdf_bytes)

        env = os.environ.copy()
        env["HOME"] = str(self.home)

        for aid in ("7102", "7103", "7104", "2795151330", "2386697165"):
            t0 = time.monotonic()
            res = subprocess.run(
                [str(DETECT), "--json", aid],
                env=env,
                stdin=subprocess.DEVNULL,
                text=True,
                capture_output=True,
                timeout=5,
                check=True,
            )
            self.assertLess(time.monotonic() - t0, 3.0, f"Detector too slow on {aid}")
            rep = json.loads(res.stdout)
            if aid in ("7102", "7103", "2795151330", "2386697165"):
                self.assertIsNone(rep["install_dir"], f"Unsafe/missing install_dir should not be scanned for {aid}")
            if aid == "2795151330":
                # Must NOT falsely inherit EAC/DLSS from sibling Steam game in $HOME
                self.assertEqual(rep["source"], "shortcut")
                self.assertEqual(rep["game"], "MORDHAU")
                self.assertEqual(rep["class"], "standard")
                self.assertFalse(rep["has_dlss"])
            if aid == "2386697165":
                # Empty/rejected StartDir must still preserve LaunchOptions (vr-run)
                self.assertTrue(rep["is_vr"])
                self.assertEqual(rep["class"], "vr")
            if aid == "7104":
                self.assertEqual(rep["class"], "legacy-upscaler")
                self.assertTrue(rep["has_dlss"])

        # 4) Never hangs even when stdin is an open pipe that never sends EOF
        proc = subprocess.Popen(
            [str(DETECT), "--json", "7102"],
            env=env,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            proc.wait(timeout=5)
            self.assertEqual(proc.returncode, 0)
            stdout_data = proc.stdout.read()
            self.assertEqual(json.loads(stdout_data)["app_id"], "7102")
        finally:
            if proc.stdin:
                proc.stdin.close()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()
            if proc.poll() is None:
                proc.kill()
                proc.wait()

    def test_v242_fh6_2483190_rdna4_stability_guard(self):
        drm = self.home / "drm-rdna4-fh6"
        dev = drm / "card0" / "device"
        dev.mkdir(parents=True)
        (dev / "vendor").write_text("0x1002\n", encoding="utf-8")
        (dev / "device").write_text("0x7550\n", encoding="utf-8")
        (dev / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

        self.create_game(
            "2483190",
            "Forza Horizon 6",
            files=("forzahorizon6.exe", "amd_fidelityfx_loader_dx12.dll", "amd_fidelityfx_upscaler_dx12.dll", "sl.reflex.dll"),
        )
        env = os.environ.copy()
        for k in ("BLEEDING_EDGE", "TRANSFER_QUEUE", "REFLEX_LAYER", "VK_VIDEO_DECODE", "AFMF", "CONSERVATIVE"):
            env.pop(k, None)
        env["HOME"] = str(self.home)
        env["SAP_DRM_DIR"] = str(drm)
        env["WAYLAND_DISPLAY"] = "wayland-0"

        rep = json.loads(subprocess.run(
            [str(DETECT), "--json", "2483190"], env=env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertEqual(rep["class"], "native-fsr4")
        self.assertFalse(rep["bleeding_edge"])
        self.assertFalse(rep["transfer_queue"])
        self.assertFalse(rep["reflex_layer"])
        self.assertFalse(rep["vk_video_decode"])
        self.assertFalse(rep["afmf"])
        self.assertFalse(rep["optiscaler"])
        self.assertTrue(rep["native_antilag"])
        self.assertFalse(rep["xwayland"])
        tokens = rep["proton_add_config"].split(",")
        self.assertIn("wayland", tokens)
        self.assertIn("fsr4", tokens)
        self.assertNotIn("wow64", tokens)
        self.assertNotIn("lowlatencylayer", tokens)

    def test_v243_unreal_engine_detection_and_safe_rdna4_defaults(self):
        drm = self.home / "drm-rdna4-ue"
        dev = drm / "card0" / "device"
        dev.mkdir(parents=True)
        (dev / "vendor").write_text("0x1002\n", encoding="utf-8")
        (dev / "device").write_text("0x7550\n", encoding="utf-8")
        (dev / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

        env = os.environ.copy()
        for k in ("BLEEDING_EDGE", "TRANSFER_QUEUE", "REFLEX_LAYER", "VK_VIDEO_DECODE", "AFMF", "OPTISCALER", "CONSERVATIVE"):
            env.pop(k, None)
        env["HOME"] = str(self.home)
        env["SAP_DRM_DIR"] = str(drm)
        env["WAYLAND_DISPLAY"] = "wayland-0"

        ue_cases = (
            ("8101", "UE Shipping Game", ("FSD/Binaries/Win64/FSD-Win64-Shipping.exe",)),
            ("8102", "UE Engine Dir Game", ("Engine/Binaries/Win64/UnrealCEFSubProcess.exe", "game.exe")),
            ("8103", "UE Pak Game", ("game.exe", "Content/Paks/pakchunk0-WindowsNoEditor.pak")),
            ("8104", "UE IoStore Game", ("game.exe", "Content/Paks/global.ucas", "Content/Paks/global.utoc")),
        )
        for aid, name, files in ue_cases:
            with self.subTest(ue_game=name):
                self.create_game(aid, name, files=files)
                rep = json.loads(subprocess.run(
                    [str(DETECT), "--json", aid], env=env, text=True, capture_output=True, check=True
                ).stdout)
                self.assertTrue(rep["engine_ue"])
                self.assertEqual(rep["AUTO_ENGINE_UE"], 1)
                # AMD RADV UE defaults disable transfer_queue & bleeding_edge while keeping safe FSR4/Wayland
                self.assertFalse(rep["transfer_queue"])
                self.assertFalse(rep["bleeding_edge"])
                self.assertEqual(rep["smart_defaults"]["USE_TRANSFER_QUEUE"], "0")
                self.assertEqual(rep["smart_defaults"]["USE_BLEEDING_EDGE"], "0")
                tokens = rep["proton_add_config"].split(",")
                self.assertIn("fsr4", tokens)
                self.assertNotIn("wow64", tokens)

        # Explicit user override still enables bleeding_edge & transfer_queue on generic UE titles
        rep_ovr = json.loads(subprocess.run(
            [str(DETECT), "--json", "8101"],
            env={**env, "BLEEDING_EDGE": "1", "TRANSFER_QUEUE": "1"},
            text=True, capture_output=True, check=True,
        ).stdout)
        self.assertTrue(rep_ovr["bleeding_edge"])
        self.assertTrue(rep_ovr["transfer_queue"])

        # Deep Rock Galactic (548430) with unused openvr_api.dll is UE4 flatscreen, NOT VR, with RDNA 4 stability guard
        self.create_game(
            "548430",
            "Deep Rock Galactic",
            files=(
                "FSD/Binaries/Win64/FSD-Win64-Shipping.exe",
                "FSD/Content/Paks/FSD-WindowsNoEditor.pak",
                "Engine/Binaries/ThirdParty/OpenVR/OpenVRv1_5_17/Win64/openvr_api.dll",
                "nvngx_dlss.dll",
                "sl.interposer.dll",
            ),
        )
        rep_drg = json.loads(subprocess.run(
            [str(DETECT), "--json", "548430"], env=env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertTrue(rep_drg["engine_ue"])
        self.assertFalse(rep_drg["is_vr"])
        self.assertEqual(rep_drg["class"], "legacy-upscaler")
        self.assertFalse(rep_drg["bleeding_edge"])
        self.assertFalse(rep_drg["transfer_queue"])
        self.assertFalse(rep_drg["reflex_layer"])
        self.assertFalse(rep_drg["vk_video_decode"])
        self.assertFalse(rep_drg["optiscaler"])
        self.assertFalse(rep_drg["afmf"])
        self.assertIn("fsr4", rep_drg["proton_add_config"].split(","))
        self.assertNotIn("wow64", rep_drg["proton_add_config"].split(","))
        self.assertNotIn("lowlatencylayer", rep_drg["proton_add_config"].split(","))

    def test_v243_optiscaler_afmf_mutual_exclusion_and_recovery_visibility(self):
        drm = self.home / "drm-rdna4-excl"
        dev = drm / "card0" / "device"
        dev.mkdir(parents=True)
        (dev / "vendor").write_text("0x1002\n", encoding="utf-8")
        (dev / "device").write_text("0x7550\n", encoding="utf-8")
        (dev / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

        layer_dir = self.home / "vk-layers-excl"
        layer_dir.mkdir()
        fake_so = self.home / "libafmf-excl.so"
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

        self.create_game("8150", "Legacy DLSS NoFG", files=("game.exe", "nvngx_dlss.dll"))
        env = os.environ.copy()
        for k in ("AFMF", "USE_AFMF", "OPTISCALER", "USE_OPTISCALER", "CONSERVATIVE"):
            env.pop(k, None)
        env.update({
            "HOME": str(self.home),
            "XDG_STATE_HOME": str(self.home / ".local/state"),
            "SAP_DRM_DIR": str(drm),
            "SAP_AFMF_LAYER_DIRS": str(layer_dir),
        })

        # Legacy upscaler on RDNA 4 auto-enables OptiScaler and MUST suppress AUTO_AFMF
        rep_auto = json.loads(subprocess.run(
            [str(DETECT), "--json", "8150"], env=env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertEqual(rep_auto["class"], "legacy-upscaler")
        self.assertTrue(rep_auto["optiscaler"])
        self.assertFalse(rep_auto["afmf"])
        self.assertEqual(rep_auto["AUTO_AFMF"], 0)
        self.assertEqual(rep_auto["smart_defaults"]["USE_OPTISCALER"], "1")
        self.assertEqual(rep_auto["smart_defaults"]["USE_AFMF"], "0")

        # Explicitly forcing both OPTISCALER=1 and AFMF=1 must never stack them
        rep_both = json.loads(subprocess.run(
            [str(DETECT), "--json", "8150"],
            env={**env, "OPTISCALER": "1", "AFMF": "1"},
            text=True, capture_output=True, check=True,
        ).stdout)
        self.assertTrue(rep_both["optiscaler"])
        self.assertFalse(rep_both["afmf"])

        # Recovery state is surfaced in both --json and --inspect
        state_dir = self.home / ".local/state/steam-auto-profiler"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "recovery-8150.state").write_text(
            "RECOVERY_STAGE=2\nRECOVERY_MODE=CONSERVATIVE_XWAYLAND\nCONSECUTIVE_CRASHES=2\n",
            encoding="utf-8",
        )
        rep_rec = json.loads(subprocess.run(
            [str(DETECT), "--json", "8150"], env=env, text=True, capture_output=True, check=True
        ).stdout)
        self.assertEqual(rep_rec["recovery_stage"], 2)
        self.assertEqual(rep_rec["recovery_mode"], "CONSERVATIVE_XWAYLAND")
        self.assertEqual(rep_rec["consecutive_crashes"], 2)

        insp = subprocess.run(
            [str(DETECT), "--inspect", "8150"], env=env, text=True, capture_output=True, check=True
        ).stdout
        self.assertIn("Unreal Engine:", insp)
        self.assertIn("Stage 2 (CONSERVATIVE_XWAYLAND; crashes=2)", insp)


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
