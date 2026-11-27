import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VR_RUN = ROOT / "bin" / "vr-run"


def _write_exe(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


class VrRunTests(unittest.TestCase):
    def _clean_env(self, tmp_path: Path) -> dict[str, str]:
        env = os.environ.copy()
        for key in (
            "DXVK_FRAME_RATE",
            "VKD3D_FRAME_RATE",
            "DXVK_FRAME_PACE",
            "PROTON_ENABLE_WAYLAND",
            "PROTON_USE_WAYLAND",
            "ENABLE_LAYER_MESA_ANTI_LAG",
            "ENABLE_VKBASALT",
            "PROTON_MLFG_UPGRADE",
            "MLFG_UPGRADE",
            "AMD_VULKAN_ICD",
            "RADV_PERFTEST",
            "MESA_VK_DEVICE_SELECT",
            "XR_RUNTIME_JSON",
            "VR_OVERRIDE",
            "PRESSURE_VESSEL_FILESYSTEMS_RO",
            "PRESSURE_VESSEL_FILESYSTEMS_RW",
            "LD_LIBRARY_PATH",
        ):
            env.pop(key, None)
        env["HOME"] = str(tmp_path)
        env["XDG_DATA_HOME"] = str(tmp_path / ".local" / "share")
        env["XDG_CONFIG_HOME"] = str(tmp_path / ".config")
        env["XDG_RUNTIME_DIR"] = str(tmp_path / "run")
        env["VR_RUN_XRIZER_DIR"] = str(tmp_path / "opt" / "xrizer")
        env["VR_RUN_SYSTEM_OPENXR_JSON"] = str(tmp_path / "usr" / "share" / "openxr" / "1" / "openxr_wivrn.json")
        env["VR_RUN_DRM_DIR"] = str(tmp_path / "drm")
        return env

    def test_help_and_missing_command(self):
        res_help = subprocess.run([str(VR_RUN), "--help"], text=True, capture_output=True, check=False)
        self.assertEqual(res_help.returncode, 0, res_help.stderr)
        self.assertIn("vr-run %command%", res_help.stdout)
        self.assertIn("--dry-run", res_help.stdout)

        res_empty = subprocess.run([str(VR_RUN)], text=True, capture_output=True, check=False)
        self.assertEqual(res_empty.returncode, 2)

    def test_dry_run_scrubs_flatscreen_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            scrubbed = {
                "DXVK_FRAME_RATE": "144",
                "VKD3D_FRAME_RATE": "144",
                "DXVK_FRAME_PACE": "low-latency-vrr",
                "PROTON_ENABLE_WAYLAND": "1",
                "PROTON_USE_WAYLAND": "1",
                "ENABLE_LAYER_MESA_ANTI_LAG": "1",
                "ENABLE_VKBASALT": "1",
                "PROTON_MLFG_UPGRADE": "1",
                "MLFG_UPGRADE": "1",
            }
            env.update(scrubbed)

            res = subprocess.run(
                [str(VR_RUN), "--dry-run"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn("Steam Auto-Profiler VR dry run", res.stdout)
            for var in scrubbed:
                self.assertNotIn(f"{var}=", res.stdout)

            # Verify actual command execution also sees scrubbed environment
            res_exec = subprocess.run(
                [str(VR_RUN), "/usr/bin/env"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_exec.returncode, 0, res_exec.stderr)
            for var in scrubbed:
                self.assertNotIn(f"{var}=", res_exec.stdout)

    def test_dynamic_wivrn_and_xrizer_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            wivrn_slr = tmp_path / ".local" / "share" / "wivrn-slr"
            wivrn_slr.mkdir(parents=True)
            openxr_json = wivrn_slr / "openxr_wivrn.json"
            openxr_json.write_text('{"runtime": {}}\n', encoding="utf-8")

            xrizer = tmp_path / "opt" / "xrizer"
            xrizer.mkdir(parents=True)

            openvr_cfg = tmp_path / ".config" / "openvr"
            openvr_cfg.mkdir(parents=True)

            wivrn_run = tmp_path / "run" / "wivrn"
            wivrn_run.mkdir(parents=True)

            res = subprocess.run(
                [str(VR_RUN), "--dry-run"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertIn(f"XR_RUNTIME_JSON={openxr_json}", res.stdout)
            self.assertIn(f"VR_OVERRIDE={xrizer}", res.stdout)
            self.assertIn(
                f"PRESSURE_VESSEL_FILESYSTEMS_RO={wivrn_slr}:{xrizer}:{openvr_cfg}",
                res.stdout,
            )
            self.assertIn(f"PRESSURE_VESSEL_FILESYSTEMS_RW={wivrn_run}", res.stdout)
            self.assertIn(f"LD_LIBRARY_PATH={wivrn_slr}", res.stdout)

    def test_system_openxr_fallback_and_preserves_user_overrides(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            sys_json = tmp_path / "usr" / "share" / "openxr" / "1" / "openxr_wivrn.json"
            sys_json.parent.mkdir(parents=True)
            sys_json.write_text('{"runtime": {}}\n', encoding="utf-8")

            res_fallback = subprocess.run(
                [str(VR_RUN), "--dry-run"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_fallback.returncode, 0, res_fallback.stderr)
            self.assertIn(f"XR_RUNTIME_JSON={sys_json}", res_fallback.stdout)

            # User overrides must never be clobbered
            xrizer = tmp_path / "opt" / "xrizer"
            xrizer.mkdir(parents=True)
            env.update({
                "XR_RUNTIME_JSON": "/custom/openxr.json",
                "VR_OVERRIDE": "/custom/openvr",
                "MESA_VK_DEVICE_SELECT": "1002:9999!",
                "PRESSURE_VESSEL_FILESYSTEMS_RO": "/existing/ro",
                "LD_LIBRARY_PATH": "/existing/lib",
            })
            res_override = subprocess.run(
                [str(VR_RUN), "--dry-run"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_override.returncode, 0, res_override.stderr)
            self.assertIn("XR_RUNTIME_JSON=/custom/openxr.json", res_override.stdout)
            self.assertIn("VR_OVERRIDE=/custom/openvr", res_override.stdout)
            self.assertIn("MESA_VK_DEVICE_SELECT=1002:9999!", res_override.stdout)
            self.assertIn(f"PRESSURE_VESSEL_FILESYSTEMS_RO=/existing/ro:{xrizer}", res_override.stdout)
            self.assertIn("LD_LIBRARY_PATH=/existing/lib", res_override.stdout)

    def test_dynamic_gpu_detection_amd_and_nvidia(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            drm = tmp_path / "drm"

            # Intel iGPU + AMD dGPU -> picks AMD dGPU + RADV
            igpu = drm / "card0" / "device"
            igpu.mkdir(parents=True)
            (igpu / "vendor").write_text("0x8086\n", encoding="utf-8")
            (igpu / "device").write_text("0x46a6\n", encoding="utf-8")
            (igpu / "boot_vga").write_text("1\n", encoding="utf-8")

            dgpu = drm / "card1" / "device"
            dgpu.mkdir(parents=True)
            (dgpu / "vendor").write_text("0x1002\n", encoding="utf-8")
            (dgpu / "device").write_text("0x7550\n", encoding="utf-8")
            (dgpu / "mem_info_vram_total").write_text("17179869184\n", encoding="utf-8")
            (dgpu / "boot_vga").write_text("0\n", encoding="utf-8")

            res_amd = subprocess.run(
                [str(VR_RUN), "--dry-run"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_amd.returncode, 0, res_amd.stderr)
            self.assertIn("GPU: amd", res_amd.stdout)
            self.assertIn("MESA_VK_DEVICE_SELECT=1002:7550!", res_amd.stdout)
            self.assertIn("AMD_VULKAN_ICD=RADV", res_amd.stdout)
            self.assertIn("RADV_PERFTEST=sam", res_amd.stdout)

            # Switch dGPU to NVIDIA -> picks NVIDIA dGPU without AMD_VULKAN_ICD
            (dgpu / "vendor").write_text("0x10de\n", encoding="utf-8")
            (dgpu / "device").write_text("0x2684\n", encoding="utf-8")
            res_nv = subprocess.run(
                [str(VR_RUN), "--dry-run"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res_nv.returncode, 0, res_nv.stderr)
            self.assertIn("GPU: nvidia", res_nv.stdout)
            self.assertIn("MESA_VK_DEVICE_SELECT=10de:2684!", res_nv.stdout)
            self.assertNotIn("AMD_VULKAN_ICD=", res_nv.stdout)

    def test_scheduler_chain_uses_game_performance_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            mock_bin = tmp_path / "mock-bin"
            mock_bin.mkdir()
            _write_exe(mock_bin / "game-performance", '#!/bin/sh\necho "gp:$*"\n')
            env["PATH"] = f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}"

            res = subprocess.run(
                [str(VR_RUN), "echo", "hello"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertEqual(res.stdout.strip(), "gp:echo hello")

    def test_vr_mode_ref_counted_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            mock_bin = tmp_path / "mock-bin"
            mock_bin.mkdir()
            log_file = tmp_path / "vr-mode.log"
            _write_exe(
                mock_bin / "vr-mode",
                f'#!/bin/sh\necho "$1" >> "{log_file}"\n',
            )
            env["PATH"] = f"{mock_bin}:/usr/bin:/bin"
            env["VR_AUTO_MODE"] = "1"

            # Start two overlapping VR sessions: session 1 stays alive while session 2 starts & exits
            p1 = subprocess.Popen(
                [str(VR_RUN), "/bin/sleep", "0.8"],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            # Wait briefly until session 1 records itself
            sessions_file = Path(env["XDG_RUNTIME_DIR"]) / "vr-run.sessions"
            for _ in range(40):
                if sessions_file.is_file() and sessions_file.read_text(encoding="utf-8").strip():
                    break
                import time
                time.sleep(0.05)

            res2 = subprocess.run(
                [str(VR_RUN), "/bin/true"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res2.returncode, 0, res2.stderr)

            # While session 1 is still active, vr-mode off MUST NOT have been called yet
            mid_calls = log_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(mid_calls, ["on"])

            _, p1_err = p1.communicate(timeout=10)
            self.assertEqual(p1.returncode, 0, p1_err)

            final_calls = log_file.read_text(encoding="utf-8").splitlines()
            self.assertEqual(final_calls, ["on", "off"])
            self.assertFalse(sessions_file.exists())

    def test_vr_auto_mode_disabled_skips_vr_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env = self._clean_env(tmp_path)
            mock_bin = tmp_path / "mock-bin"
            mock_bin.mkdir()
            log_file = tmp_path / "vr-mode.log"
            _write_exe(
                mock_bin / "vr-mode",
                f'#!/bin/sh\necho "$1" >> "{log_file}"\n',
            )
            env["PATH"] = f"{mock_bin}:/usr/bin:/bin"
            env["VR_AUTO_MODE"] = "0"

            res = subprocess.run(
                [str(VR_RUN), "/bin/true"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(res.returncode, 0, res.stderr)
            self.assertFalse(log_file.exists())


if __name__ == "__main__":
    unittest.main()
