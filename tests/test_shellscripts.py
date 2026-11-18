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

    def test_no_tracked_python_bytecode(self):
        result = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files"],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            self.skipTest("repository is not available as a git worktree")
        tracked = result.stdout.splitlines()
        offenders = [
            path for path in tracked
            if "/__pycache__/" in f"/{path}"
            or path.endswith(".pyc")
            or path.endswith(".pyo")
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
