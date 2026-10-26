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


def test_check_config():
    """``--check-config`` prints the default devices and exits 0."""
    result = _help([sys.executable, "-m", "emulator", "--check-config"])
    assert result.returncode == 0, result.stderr
    for hostname in ("opengear-1", "cisco-switch-1", "garderos-1"):
        assert hostname in result.stdout


def test_check_config_rejects_unknown_device_type(tmp_path):
    """An unknown ``device_type`` makes ``--check-config`` exit 1."""
    config = tmp_path / "bad.json"
    config.write_text(
        '{"devices": [{"port": 1, "device_type": "nope", "model": "X", "hostname": "bad-1"}]}'
    )
    result = _help([sys.executable, "-m", "emulator", "--check-config", "--config", str(config)])
    assert result.returncode == 1
    assert "bad-1  (INVALID)" in result.stdout
