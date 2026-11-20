import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NET = ROOT / "bin/steam-net-boost"


class NetBoostTests(unittest.TestCase):
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

            for iface in ("eth0; rm -rf /", "../bad"):
                result = subprocess.run(
                    [str(NET), "status", "--iface", iface],
                    env=env, text=True, capture_output=True,
                )
                self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
