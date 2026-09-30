"""Shared connection settings for the examples."""
import getpass
import os
import sys

from openai import APIConnectionError, APIStatusError, OpenAI
import requests

SWARM_URL = os.environ.get("SWARM_URL", "http://127.0.0.1:43100").rstrip("/")
SWARM_API_KEY = os.environ.get("SWARM_API_KEY")
if not SWARM_API_KEY:
    if not sys.stdin.isatty():
        raise SystemExit("Set SWARM_API_KEY to a token from Settings > Server > Account > API tokens.")
    print("Create a token in DAFO Swarm: Settings > Server > Account > API tokens.")
    SWARM_API_KEY = getpass.getpass("Paste your API token (hidden), then press Enter: ").strip()
    if not SWARM_API_KEY:
        raise SystemExit("No token entered. Run the example again and paste your API token.")

# Distributed generation can take minutes for long answers.
client = OpenAI(base_url=f"{SWARM_URL}/v1", api_key=SWARM_API_KEY, timeout=600)
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {SWARM_API_KEY}"})


def active_model() -> str:
    try:
        models = client.models.list().data
    except APIConnectionError as error:
        raise SystemExit(f"Cannot reach DAFO Swarm at {SWARM_URL}. Start the coordinator or set SWARM_URL.") from error
    except APIStatusError as error:
        if error.status_code == 401:
            raise SystemExit("The API token was rejected. Create a new token in Settings > Server > Account.") from error
        raise SystemExit(f"DAFO Swarm returned HTTP {error.status_code}: {error.message}") from error
    if not models:
        raise SystemExit("The swarm has no active model yet. Select one in the dashboard.")
    return models[0].id


def enabled_agents() -> list[dict]:
    try:
        response = session.get(f"{SWARM_URL}/v1/agents", timeout=30)
        response.raise_for_status()
        return response.json()["data"]
    except requests.exceptions.ConnectionError as error:
        raise SystemExit(f"Cannot reach DAFO Swarm at {SWARM_URL}. Start the coordinator or set SWARM_URL.") from error
    except requests.exceptions.HTTPError as error:
        if response.status_code == 401:
            raise SystemExit("The API token was rejected. Create a new token in Settings > Server > Account.") from error
        raise SystemExit(f"DAFO Swarm returned HTTP {response.status_code}: {response.text}") from error
