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


if __name__ == "__main__":
    unittest.main()
