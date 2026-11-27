import json
import os
import pathlib
import subprocess
import tempfile
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN_DIR = REPO_ROOT / "bin"


class ReleaseHardeningTests(unittest.TestCase):
    def _base_env(self, tmp_path: pathlib.Path, extra_path: pathlib.Path | None = None) -> dict[str, str]:
        env = os.environ.copy()
        for key in (
            "VRR_CAP",
            "DXVK_FRAME_RATE",
            "VKD3D_FRAME_RATE",
            "GAMESCOPE_WAYLAND_DISPLAY",
            "XDG_CURRENT_DESKTOP",
            "FORCE_GUI",
            "XWAYLAND",
            "MLFG",
            "USE_MLFG",
            "VRR_MINUS_MARGIN",
        ):
            env.pop(key, None)
        usb_empty = tmp_path / "usb-empty"
        usb_empty.mkdir(parents=True, exist_ok=True)
        env["HOME"] = str(tmp_path)
        env["XDG_CONFIG_HOME"] = str(tmp_path / ".config")
        env["XDG_STATE_HOME"] = str(tmp_path / ".local" / "state")
        env["SAP_USB_DIR"] = str(usb_empty)
        env["WAYLAND_DISPLAY"] = "wayland-0"
        env["NO_GUI"] = "1"
        if extra_path is not None:
            env["PATH"] = f"{extra_path}:{env.get('PATH', '/usr/bin:/bin')}"
        return env

    def _make_mock_kscreen(self, mock_bin: pathlib.Path, output: str) -> None:
        mock_bin.mkdir(parents=True, exist_ok=True)
        script = mock_bin / "kscreen-doctor"
        script.write_text(f"#!/bin/sh\ncat <<'EOF'\n{output}\nEOF\n", encoding="utf-8")
        script.chmod(0o755)

    def test_kscreen_doctor_plasma6_active_mode_vrr_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            mock_bin = tmp_path / "mock-bin"
            self._make_mock_kscreen(
                mock_bin,
                "Output: 1 DP-1 4fd81866-f7aa-443c-ab90-03c60ce23d7b\n"
                "        Modes:  1:3440x1440@59.97!  2:3440x1440@239.98*  3:3440x1440@164.90",
            )
            env = self._base_env(tmp_path, mock_bin)
            res = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("VRR cap: 240", res.stdout)
            self.assertIn("DXVK_FRAME_RATE=240", res.stdout)
            self.assertIn("VKD3D_FRAME_RATE=240", res.stdout)

            env["VRR_MINUS_MARGIN"] = "1"
            res_margin = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_margin.returncode, 0, res_margin.stderr)
            self.assertIn("VRR cap: 225", res_margin.stdout)
            self.assertIn("DXVK_FRAME_RATE=225", res_margin.stdout)
            self.assertIn("VKD3D_FRAME_RATE=225", res_margin.stdout)

            env["VRR_CAP"] = "165"
            res_explicit = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_explicit.returncode, 0, res_explicit.stderr)
            self.assertIn("VRR cap: 165", res_explicit.stdout)
            self.assertIn("DXVK_FRAME_RATE=165", res_explicit.stdout)
            self.assertIn("VKD3D_FRAME_RATE=165", res_explicit.stdout)

    def test_kscreen_doctor_legacy_hz_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            mock_bin = tmp_path / "mock-bin"
            self._make_mock_kscreen(mock_bin, "Output: 1 DP-1 2560x1440 165.00Hz")
            res = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=self._base_env(tmp_path, mock_bin),
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("VRR cap: 165", res.stdout)

    def test_profile_vrr_settings_override_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            mock_bin = tmp_path / "mock-bin"
            profiles = tmp_path / ".config" / "steam-auto-profiler" / "profiles"
            profiles.mkdir(parents=True, exist_ok=True)
            self._make_mock_kscreen(
                mock_bin,
                "Output: 1 DP-1\n        Modes:  2:3440x1440@239.98*",
            )

            (profiles / "2357570.env").write_text(
                "VRR_MINUS_MARGIN=1\n",
                encoding="utf-8",
            )
            res_margin = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=self._base_env(tmp_path, mock_bin),
            )
            self.assertEqual(res_margin.returncode, 0, res_margin.stderr)
            self.assertIn("DXVK_FRAME_RATE=225", res_margin.stdout)

            (profiles / "2357570.env").write_text(
                "VRR_CAP=165\nVRR_MINUS_MARGIN=1\n",
                encoding="utf-8",
            )
            res_explicit = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=self._base_env(tmp_path, mock_bin),
            )
            self.assertEqual(res_explicit.returncode, 0, res_explicit.stderr)
            self.assertIn("DXVK_FRAME_RATE=165", res_explicit.stdout)

    def test_gamescope_skips_vrr_cap_unless_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            mock_bin = tmp_path / "mock-bin"
            self._make_mock_kscreen(
                mock_bin,
                "Output: 1 DP-1\n        Modes:  2:3440x1440@239.98*",
            )
            env = self._base_env(tmp_path, mock_bin)
            env["GAMESCOPE_WAYLAND_DISPLAY"] = "gamescope-0"

            res_auto = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_auto.returncode, 0, res_auto.stderr)
            self.assertNotIn("DXVK_FRAME_RATE=", res_auto.stdout)
            self.assertNotIn("VKD3D_FRAME_RATE=", res_auto.stdout)

            env["VRR_CAP"] = "144"
            res_explicit = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "2357570"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_explicit.returncode, 0, res_explicit.stderr)
            self.assertIn("DXVK_FRAME_RATE=144", res_explicit.stdout)
            self.assertIn("VKD3D_FRAME_RATE=144", res_explicit.stdout)

    def test_load_profile_safe_blocks_injection_and_reads_final_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            profiles = tmp_path / ".config" / "steam-auto-profiler" / "profiles"
            profiles.mkdir(parents=True, exist_ok=True)
            marker = tmp_path / "pwned.marker"
            (profiles / "999001.env").write_bytes(
                f"USE_XWAYLAND=1\r\nUSE_MLFG=$(touch {marker})\r\nUSE_SDL=1".encode("utf-8")
            )
            res = subprocess.run(
                [str(BIN_DIR / "steam-auto-detect"), "--inspect", "--json", "999001"],
                capture_output=True, text=True, env=self._base_env(tmp_path),
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertFalse(marker.exists(), "Injected shell command must not execute")
            data = json.loads(res.stdout)
            tokens = [t for t in data.get("proton_add_config", "").split(",") if t]
            self.assertIn("sdlinput", tokens)
            self.assertNotIn("wayland", tokens)
            self.assertNotIn("mlfg", tokens)

    def test_last_log_and_list_profiles(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            env = self._base_env(tmp_path)

            res_log = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--last-log"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_log.returncode, 0, res_log.stderr)
            self.assertIn("no last-launch log", res_log.stdout.lower())

            profiles = tmp_path / ".config" / "steam-auto-profiler" / "profiles"
            profiles.mkdir(parents=True, exist_ok=True)
            (profiles / "2357570.env").write_text("USE_XWAYLAND=1\n", encoding="utf-8")

            res_list = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--list-profiles"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_list.returncode, 0, res_list.stderr)
            self.assertIn("2357570", res_list.stdout)

    def test_sync_print_library_paths_and_keep_backups(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            steam_root = tmp_path / ".local" / "share" / "Steam"
            lib2 = tmp_path / "nvme2-steam"
            (steam_root / "steamapps").mkdir(parents=True, exist_ok=True)
            (steam_root / "config").mkdir(parents=True, exist_ok=True)
            (lib2 / "steamapps").mkdir(parents=True, exist_ok=True)

            vdf = (
                '"libraryfolders"\n{\n'
                f'\t"0"\n\t{{\n\t\t"path"\t\t"{steam_root}"\n\t}}\n'
                f'\t"1"\n\t{{\n\t\t"path"\t\t"{lib2}"\n\t}}\n'
                "}\n"
            )
            (steam_root / "steamapps" / "libraryfolders.vdf").write_text(vdf, encoding="utf-8")
            (steam_root / "config" / "libraryfolders.vdf").write_text(vdf, encoding="utf-8")

            env = self._base_env(tmp_path)
            res_paths = subprocess.run(
                [str(BIN_DIR / "steam-auto-sync"), "--print-library-paths"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res_paths.returncode, 0, res_paths.stderr)
            self.assertIn(str(steam_root), res_paths.stdout)
            self.assertIn(str(lib2), res_paths.stdout)

            cfg_dir = steam_root / "userdata" / "12345" / "config"
            cfg_dir.mkdir(parents=True, exist_ok=True)
            (steam_root / "steamapps" / "appmanifest_570.acf").write_text(
                '"AppState"\n{\n\t"appid"\t\t"570"\n\t"name"\t\t"Dota 2"\n}\n',
                encoding="utf-8",
            )
            (cfg_dir / "localconfig.vdf").write_text(
                '"UserLocalConfigStore"\n{\n\t"Software"\n\t{\n\t\t"Valve"\n\t\t{\n'
                '\t\t\t"Steam"\n\t\t\t{\n\t\t\t\t"apps"\n\t\t\t\t{\n'
                '\t\t\t\t\t"570"\n\t\t\t\t\t{\n\t\t\t\t\t\t"LaunchOptions"\t\t"cachy-run %command%"\n'
                '\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t}\n\t\t}\n\t}\n}\n',
                encoding="utf-8",
            )
            for idx in range(1, 5):
                bak = cfg_dir / f"localconfig.vdf.bak.20260101-00000{idx}"
                bak.write_text("old", encoding="utf-8")
                os.utime(bak, (1700000000 + idx * 10, 1700000000 + idx * 10))

            res_sync = subprocess.run(
                [str(BIN_DIR / "steam-auto-sync"), "--sanitize", "--keep-backups", "2"],
                capture_output=True, text=True, env=env,
            )
            combined = (res_sync.stdout + res_sync.stderr).lower()
            if res_sync.returncode != 0 and "running" in combined:
                self.skipTest("Steam is currently running on host")
            self.assertEqual(res_sync.returncode, 0, res_sync.stdout + res_sync.stderr)
            remaining = list(cfg_dir.glob("localconfig.vdf.bak.*"))
            self.assertLessEqual(len(remaining), 2, f"Expected <= 2 backups, got {remaining}")

    def test_conservative_profile_and_env_override_hardening(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            drm = tmp_path / "drm-rdna4"
            dev = drm / "card0" / "device"
            dev.mkdir(parents=True)
            (dev / "vendor").write_text("0x1002\n", encoding="utf-8")
            (dev / "device").write_text("0x7550\n", encoding="utf-8")
            (dev / "uevent").write_text("PCI_ID=1002:7550\n", encoding="utf-8")

            profiles = tmp_path / ".config" / "steam-auto-profiler" / "profiles"
            profiles.mkdir(parents=True, exist_ok=True)
            (profiles / "999002.env").write_text("USE_CONSERVATIVE=1\n", encoding="utf-8")

            env = self._base_env(tmp_path)
            env["SAP_DRM_DIR"] = str(drm)
            res = subprocess.run(
                [str(BIN_DIR / "steam-auto-run"), "--dry-run", "999002"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("Conservative: enabled", res.stdout)
            self.assertIn("RADV_PERFTEST=sam\n", res.stdout)
            self.assertIn("ENABLE_LAYER_MESA_ANTI_LAG=1", res.stdout)
            self.assertNotIn("PROTON_USE_WOW64=", res.stdout)
            self.assertNotIn("RADV_EXPERIMENTAL=video_decode", res.stdout)

    def test_clean_shaders_dry_run_preserves_prismlauncher_and_handles_running_steam(self):
        cleaner = BIN_DIR / "steam-auto-clean-shaders"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            cache = tmp_path / ".cache"
            mesa_cache = cache / "mesa_shader_cache_sf"
            radv_cache = cache / "radv_builtin_shaders64"
            vk_cache = cache / "vulkan"
            amd_cache = cache / "AMD"
            qt_cache = cache / "qtshadercache-x86_64"
            for d in (mesa_cache, radv_cache, vk_cache, amd_cache, qt_cache):
                d.mkdir(parents=True)
                (d / "blob.bin").write_bytes(b"data")

            # PrismLauncher & shaderpacks must NEVER be touched
            prism_pack = tmp_path / ".local" / "share" / "PrismLauncher" / "instances" / "1.21" / "shaderpacks" / "Complementary.zip"
            prism_pack.parent.mkdir(parents=True)
            prism_pack.write_bytes(b"zip")
            prism_in_steam = tmp_path / ".local" / "share" / "Steam" / "steamapps" / "common" / "PrismLauncher" / "shaderpacks" / "test.dxvk-cache"
            prism_in_steam.parent.mkdir(parents=True)
            prism_in_steam.write_bytes(b"keep")

            # Steam primary + secondary library shadercache & prefix caches
            steam_root = tmp_path / ".local" / "share" / "Steam"
            lib2 = tmp_path / "nvme2-steam"
            sc1 = steam_root / "steamapps" / "shadercache" / "361420"
            sc2 = lib2 / "steamapps" / "shadercache" / "594650"
            sc1.mkdir(parents=True)
            sc2.mkdir(parents=True)
            (sc1 / "foz.bin").write_bytes(b"s1")
            (sc2 / "foz.bin").write_bytes(b"s2")

            d3d_cache = lib2 / "steamapps" / "compatdata" / "594650" / "pfx" / "drive_c" / "users" / "steamuser" / "AppData" / "Local" / "D3DSCache"
            d3d_cache.mkdir(parents=True)
            (d3d_cache / "dx.cache").write_bytes(b"dx")
            ue_cache = lib2 / "steamapps" / "common" / "UEGame" / "Game.ushaderprecache"
            ue_cache.parent.mkdir(parents=True)
            ue_cache.write_bytes(b"ue")

            vdf = (
                '"libraryfolders"\n{\n'
                f'\t"0"\n\t{{\n\t\t"path"\t\t"{steam_root}"\n\t}}\n'
                f'\t"1"\n\t{{\n\t\t"path"\t\t"{lib2}"\n\t}}\n'
                "}\n"
            )
            (steam_root / "steamapps" / "libraryfolders.vdf").write_text(vdf, encoding="utf-8")

            # Mock pgrep returning not-running first
            mock_bin_idle = tmp_path / "mock-idle"
            mock_bin_idle.mkdir()
            pgrep_idle = mock_bin_idle / "pgrep"
            pgrep_idle.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            pgrep_idle.chmod(0o755)

            env = self._base_env(tmp_path, mock_bin_idle)
            env["XDG_CACHE_HOME"] = str(cache)

            # 1) --dry-run previews all caches without deleting anything and excludes PrismLauncher
            res_dry = subprocess.run([str(cleaner), "--dry-run"], capture_output=True, text=True, env=env)
            self.assertEqual(res_dry.returncode, 0, res_dry.stderr)
            self.assertIn("mesa_shader_cache_sf", res_dry.stdout)
            self.assertIn("radv_builtin_shaders64", res_dry.stdout)
            self.assertIn("shadercache/361420", res_dry.stdout)
            self.assertIn("shadercache/594650", res_dry.stdout)
            self.assertIn("D3DSCache", res_dry.stdout)
            self.assertIn("Game.ushaderprecache", res_dry.stdout)
            self.assertNotIn("PrismLauncher", res_dry.stdout)
            self.assertTrue(mesa_cache.exists())
            self.assertTrue(sc1.exists())
            self.assertTrue(prism_pack.exists())
            self.assertTrue(prism_in_steam.exists())

            # 2) When Steam IS running, cleans only safe driver/Mesa caches and sets pending flag
            mock_bin_run = tmp_path / "mock-running"
            mock_bin_run.mkdir()
            pgrep_run = mock_bin_run / "pgrep"
            pgrep_run.write_text('#!/bin/sh\nif [ "$1" = "-x" ] && [ "$2" = "steam" ]; then exit 0; fi\nexit 1\n', encoding="utf-8")
            pgrep_run.chmod(0o755)
            env_running = self._base_env(tmp_path, mock_bin_run)
            env_running["XDG_CACHE_HOME"] = str(cache)

            res_running = subprocess.run([str(cleaner), "--hook"], capture_output=True, text=True, env=env_running)
            self.assertEqual(res_running.returncode, 0, res_running.stderr)
            self.assertIn("Steam is currently running", res_running.stdout)
            self.assertFalse(mesa_cache.exists(), "Driver Mesa cache should be cleaned safely")
            self.assertFalse(radv_cache.exists())
            self.assertTrue(sc1.exists(), "Steam shadercache must be deferred while Steam is running")
            self.assertTrue(sc2.exists())
            pending_flag = tmp_path / ".local" / "state" / "steam-auto-profiler" / "pending-shader-cleanup"
            self.assertTrue(pending_flag.is_file())

            # 3) When Steam is closed, cleans Steam shadercache + prefix/UE caches, clears pending flag, preserves PrismLauncher
            res_clean = subprocess.run([str(cleaner)], capture_output=True, text=True, env=env)
            self.assertEqual(res_clean.returncode, 0, res_clean.stderr)
            self.assertFalse(sc1.exists())
            self.assertFalse(sc2.exists())
            self.assertFalse(d3d_cache.exists())
            self.assertFalse(ue_cache.exists())
            self.assertFalse(pending_flag.exists())
            self.assertTrue(prism_pack.exists(), "PrismLauncher shaderpacks must be preserved")
            self.assertTrue(prism_in_steam.exists(), "PrismLauncher inside Steam dir must be preserved")


if __name__ == "__main__":
    unittest.main()
