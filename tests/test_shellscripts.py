import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ShellScriptTests(unittest.TestCase):
    def test_shellcheck(self):
        shellcheck = shutil.which("shellcheck")
        if not shellcheck:
            self.skipTest("shellcheck is not installed")

        scripts = [ROOT / "install.sh"]
        scripts.extend(
            sorted(
                script
                for script in (ROOT / "bin").glob("*")
                if script.is_file()
                and script.read_text(encoding="utf-8", errors="ignore").startswith("#!")
                and "python" not in script.read_text(encoding="utf-8", errors="ignore").splitlines()[0]
            )
        )
        result = subprocess.run(
            [shellcheck, *[str(script) for script in scripts]],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
