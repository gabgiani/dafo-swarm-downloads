#!/usr/bin/env python3
"""Set up the Python examples in a local virtual environment, then open the menu.

    python examples/python/run.py
    python examples/python/run.py --install-only
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
import venv


HERE = Path(__file__).resolve().parent
VENV = HERE / ".venv"
REQUIREMENTS = HERE / "requirements.txt"
STAMP = VENV / ".requirements.sha256"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def install() -> Path:
    if sys.version_info < (3, 9):
        raise RuntimeError("Python 3.9 or newer is required.")
    python = venv_python()
    if not python.exists():
        print(f"Creating virtual environment: {VENV}")
        venv.EnvBuilder(with_pip=True).create(VENV)
    digest = requirements_hash()
    if not STAMP.exists() or STAMP.read_text(encoding="utf-8").strip() != digest:
        print("Installing Python example dependencies...")
        subprocess.run([str(python), "-m", "pip", "install", "-r", str(REQUIREMENTS)], check=True)
        STAMP.write_text(digest + "\n", encoding="utf-8")
    return python


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--install-only", action="store_true", help="Create or update .venv, then exit.")
    args = parser.parse_args()
    try:
        python = install()
    except (OSError, subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"Setup failed: {exc}", file=sys.stderr)
        return 1
    if args.install_only:
        print(f"Ready: {python}")
        return 0
    return subprocess.run([str(python), str(HERE / "menu.py")]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
