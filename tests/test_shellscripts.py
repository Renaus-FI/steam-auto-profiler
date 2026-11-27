import re
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL_SHEBANG_RE = re.compile(r"^#!(?:/(?:usr/)?bin/(?:env\s+)?(?:ba|da)?sh)\b")


def _is_shell_script(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            first_line = fh.readline()
    except OSError:
        return False
    return bool(SHELL_SHEBANG_RE.match(first_line))


class ShellScriptTests(unittest.TestCase):
    def test_shellcheck(self):
        shellcheck = shutil.which("shellcheck")
        if not shellcheck:
            self.skipTest("shellcheck is not installed")

        scripts = [ROOT / "install.sh"]
        scripts.extend(
            sorted(script for script in (ROOT / "bin").glob("*") if _is_shell_script(script))
        )
        self.assertIn(ROOT / "bin" / "vr-run", scripts)
        self.assertNotIn(ROOT / "bin" / "steam-auto-ui", scripts)
        self.assertNotIn(ROOT / "bin" / "steam-auto-sync", scripts)
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
