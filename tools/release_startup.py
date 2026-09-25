"""Fail closed before starting a manually approved release container.

Install outside /app so an accidental source bind cannot hide this check.
The check never reads or logs bot tokens.
"""
import os
from pathlib import Path
import subprocess
import sys


def validate(root, enabled):
    root = Path(root)
    if enabled != "true":
        return "Release quarantined: validate isolated bot assignments before enabling."
    for name in ("start.sh", "moon_multibot.py", "core/config.py"):
        target = root / name
        if not target.is_file() or not os.access(target, os.R_OK):
            return f"Release startup blocked: missing or unreadable {name}; check /app mounts."
    result = subprocess.run(["bash", "-n", str(root / "start.sh")], capture_output=True)
    if result.returncode:
        return "Release startup blocked: start.sh has invalid shell syntax."
    return None


def main():
    root = Path("/app")
    error = validate(root, os.environ.get("MOON_RELEASE_ENABLED", "false"))
    if error:
        print(error, file=sys.stderr, flush=True)
        return 78
    os.chdir(root)
    os.execvp("bash", ["bash", str(root / "start.sh")])


if __name__ == "__main__":
    sys.exit(main())
