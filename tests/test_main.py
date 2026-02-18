"""Test CLI entry point."""

import os
import subprocess
import sys

# Ensure subprocess finds the package (e.g. when not installed, only pytest pythonpath is set)
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(_SCRIPT_DIR, "..", "src")
_ENV = os.environ.copy()
_ENV["PYTHONPATH"] = os.path.abspath(_SRC)


def test_evawiki_mcp_help_exits_zero():
    """evawiki-mcp --help exits with code 0."""
    result = subprocess.run(
        [sys.executable, "-m", "evawiki_mcp", "--help"],
        capture_output=True,
        text=True,
        cwd=None,
        env=_ENV,
    )
    assert result.returncode == 0
    assert "evawiki-mcp" in result.stdout or "usage" in result.stdout.lower()
