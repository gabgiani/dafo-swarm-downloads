"""Local SWARM_API_KEY storage for the portable Python examples."""

from __future__ import annotations

import getpass
import os
from pathlib import Path
import sys
from urllib import error, request


CREDENTIALS_FILE = Path(__file__).resolve().parent / ".env"


def _saved_key() -> str | None:
    try:
        for line in CREDENTIALS_FILE.read_text(encoding="utf-8").splitlines():
            if line.startswith("SWARM_API_KEY="):
                key = line.removeprefix("SWARM_API_KEY=").strip()
                return key or None
    except FileNotFoundError:
        pass
    return None


def _save_key(key: str) -> None:
    if "\n" in key or "\r" in key:
        raise RuntimeError("API token contains an invalid newline.")
    descriptor = os.open(CREDENTIALS_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(f"SWARM_API_KEY={key}\n")
    if os.name != "nt":
        CREDENTIALS_FILE.chmod(0o600)


def _valid(base_url: str, key: str) -> bool:
    check = request.Request(f"{base_url.rstrip('/')}/v1/models", headers={"Authorization": f"Bearer {key}"})
    try:
        with request.urlopen(check, timeout=15):
            return True
    except error.HTTPError as exc:
        if exc.code == 401:
            return False
        raise RuntimeError(f"DAFO Swarm returned HTTP {exc.code} while checking SWARM_API_KEY.") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Cannot reach DAFO Swarm at {base_url}. Start the coordinator first.") from exc


def api_key(base_url: str) -> str:
    """Read SWARM_API_KEY from the environment or local .env, prompting once if needed."""
    supplied = os.environ.get("SWARM_API_KEY")
    if supplied:
        return supplied
    stored = _saved_key()
    if stored and _valid(base_url, stored):
        return stored
    if not sys.stdin.isatty():
        raise RuntimeError("No valid SWARM_API_KEY. Set it or run the menu in a terminal once.")
    if stored:
        print("The saved SWARM_API_KEY was rejected; enter a new one.")
    else:
        print("Create a token in Settings > API > API Access.")
    key = getpass.getpass("SWARM_API_KEY (hidden; saved for future runs): ").strip()
    if not key:
        raise RuntimeError("No token entered.")
    if not _valid(base_url, key):
        raise RuntimeError("The API token was rejected and was not saved.")
    _save_key(key)
    print(f"SWARM_API_KEY saved locally in {CREDENTIALS_FILE.name}.")
    return key
