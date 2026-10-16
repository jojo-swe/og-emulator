"""The documented module command must start the CLI."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _help(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_python_module_help():
    """``python -m emulator --help`` exits successfully."""
    result = _help([sys.executable, "-m", "emulator", "--help"])
    assert result.returncode == 0, result.stderr
    assert "SSH Device Emulator" in result.stdout
    assert "--config" in result.stdout


def test_runner_script_help():
    """The checkout runner script reaches the same CLI."""
    script = PROJECT_ROOT / "scripts" / "run-ssh-emulator.py"
    result = _help([sys.executable, str(script), "--help"])
    assert result.returncode == 0, result.stderr
    assert "SSH Device Emulator" in result.stdout
