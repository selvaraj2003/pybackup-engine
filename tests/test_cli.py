import subprocess
import sys


def test_cli_help():
    """
    Verify that pybackup CLI runs and shows help.
    """
    result = subprocess.run(
        [sys.executable, "-m", "pybackup", "--help"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert result.returncode == 0
    assert "usage" in result.stdout.lower()