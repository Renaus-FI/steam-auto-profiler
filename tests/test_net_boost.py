import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "bin/steam-net-boost"


def _write_exe(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(0o755)


class NetBoostTests(unittest.TestCase):
    def _make_mock_env(self, tmp: Path, tc_show: str, active_services: tuple[str, ...] = ()):
        mock_bin = tmp / "mock-bin"
        mock_bin.mkdir(parents=True, exist_ok=True)
        log_file = tmp / "commands.log"
        state_dir = tmp / "state"

        _write_exe(
            mock_bin / "tc",
            f"#!/bin/sh\n"
            f'echo "tc $*" >> "{log_file}"\n'
            f'if [ "$1" = "qdisc" ] && [ "$2" = "show" ]; then\n'
            f"cat <<'EOF'\n{tc_show}EOF\n"
            f"fi\n",
        )
        _write_exe(
            mock_bin / "ethtool",
            f"#!/bin/sh\n"
            f'echo "ethtool $*" >> "{log_file}"\n'
            f'if [ "$1" = "--show-eee" ]; then\n'
            f"  echo 'EEE status: enabled - active'\n"
            f"fi\n",
        )
        _write_exe(
            mock_bin / "ip",
            f"#!/bin/sh\n"
            f'echo "ip $*" >> "{log_file}"\n'
            f'if [ "$1" = "-o" ]; then\n'
            f"  echo 'default via 192.0.2.1 dev lo'\n"
            f"fi\n",
        )
        services_case = "|".join(active_services) if active_services else "__none__"
        _write_exe(
            mock_bin / "systemctl",
            f"#!/bin/sh\n"
            f'if [ "$1" = "is-active" ]; then\n'
            f'  case "$3" in\n'
            f"    {services_case}) exit 0 ;;\n"
            f"    *) exit 3 ;;\n"
            f"  esac\n"
            f"fi\n"
            f"exit 0\n",
        )

        env = os.environ.copy()
        env["PATH"] = f"{mock_bin}:{env.get('PATH', '/usr/bin:/bin')}"
        env["STEAM_NET_BOOST_STATE_DIR"] = str(state_dir)
        return env, state_dir, log_file

    def test_rejects_unknown_subcommand(self):
        result = subprocess.run([str(NET), "bogus"], text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)

    def test_invalid_interface_is_ignored_without_mutation(self):
        with tempfile.TemporaryDirectory() as state:
            env = os.environ.copy()
            env["STEAM_NET_BOOST_STATE_DIR"] = state
            result = subprocess.run(
                [str(NET), "status", "--iface", "not a valid iface"],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, "")
            self.assertEqual(list(Path(state).iterdir()), [])

    def test_status_output_and_malformed_interface(self):
        with tempfile.TemporaryDirectory() as state:
            env = os.environ.copy()
            env["STEAM_NET_BOOST_STATE_DIR"] = state
            if Path("/sys/class/net/lo").is_dir():
                result = subprocess.run(
                    [str(NET), "status", "--iface", "lo"],
                    env=env, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 0)
                self.assertIn("interface=lo", result.stdout)
                self.assertIn("active_sessions=", result.stdout)

            for iface in ("eth0; rm -rf /", "../bad", "..", "eth0..1"):
                result = subprocess.run(
                    [str(NET), "status", "--iface", iface],
                    env=env, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 2)

    def test_status_is_read_only_without_existing_state_dir(self):
        if not Path("/sys/class/net/lo").is_dir():
            self.skipTest("loopback interface unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env, state_dir, _ = self._make_mock_env(
                tmp_path,
                "qdisc fq_codel 0: root refcnt 2 limit 10240p\n",
            )
            missing_dir = tmp_path / "nonexistent-parent" / "steam-net-boost"
            env["STEAM_NET_BOOST_STATE_DIR"] = str(missing_dir)
            result = subprocess.run(
                [str(NET), "status", "--iface", "lo"],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(missing_dir.exists())
            self.assertIn("interface=lo", result.stdout)
            self.assertIn("active_sessions=0", result.stdout)
            self.assertIn("static_cake=no", result.stdout)

    def test_preserves_htb_plus_leaf_cake_setup(self):
        if not Path("/sys/class/net/lo").is_dir():
            self.skipTest("loopback interface unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env, _, log_file = self._make_mock_env(
                tmp_path,
                "qdisc htb 1: root refcnt 2 r2q 10 default 0x20\n"
                "qdisc fq_codel 10: parent 1:10 limit 10240p\n"
                "qdisc cake 20: parent 1:20 bandwidth 450Mbit diffserv4\n",
            )
            res_status = subprocess.run(
                [str(NET), "status", "--iface", "lo"],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(res_status.returncode, 0, res_status.stderr)
            self.assertIn("static_cake=yes", res_status.stdout)
            self.assertIn("qdisc=htb", res_status.stdout)

            pid = str(os.getpid())
            res_on = subprocess.run(
                [str(NET), "on", "--iface", "lo", "--pid", pid],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(res_on.returncode, 0, res_on.stderr)
            res_off = subprocess.run(
                [str(NET), "off", "--iface", "lo", "--pid", pid],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(res_off.returncode, 0, res_off.stderr)

            log = log_file.read_text(encoding="utf-8")
            self.assertNotIn("tc qdisc replace", log)
            self.assertNotIn("ethtool --set-eee", log)

    def test_preserves_wan_cake_shaper_service(self):
        if not Path("/sys/class/net/lo").is_dir():
            self.skipTest("loopback interface unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env, _, log_file = self._make_mock_env(
                tmp_path,
                "qdisc htb 1: root refcnt 2\n",
                active_services=("wan-cake-shaper.service",),
            )
            res_status = subprocess.run(
                [str(NET), "status", "--iface", "lo"],
                env=env, text=True, capture_output=True,
            )
            self.assertEqual(res_status.returncode, 0, res_status.stderr)
            self.assertIn("static_cake=yes", res_status.stdout)

            pid = str(os.getpid())
            subprocess.run([str(NET), "on", "--iface", "lo", "--pid", pid], env=env, check=True)
            subprocess.run([str(NET), "off", "--iface", "lo", "--pid", pid], env=env, check=True)
            log = log_file.read_text(encoding="utf-8")
            self.assertNotIn("tc qdisc replace", log)

    def test_restores_preexisting_root_cake_instead_of_fq_codel(self):
        if not Path("/sys/class/net/lo").is_dir():
            self.skipTest("loopback interface unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            env, _, log_file = self._make_mock_env(
                tmp_path,
                "qdisc cake 8001: root refcnt 2 bandwidth unlimited diffserv3\n",
            )
            pid = str(os.getpid())
            subprocess.run([str(NET), "on", "--iface", "lo", "--pid", pid], env=env, check=True)
            subprocess.run([str(NET), "off", "--iface", "lo", "--pid", pid], env=env, check=True)

            log = log_file.read_text(encoding="utf-8")
            self.assertIn("tc qdisc replace dev lo root cake diffserv4 triple-isolate", log)
            self.assertIn("tc qdisc replace dev lo root cake\n", log)
            self.assertNotIn("root fq_codel", log)


if __name__ == "__main__":
    unittest.main()
