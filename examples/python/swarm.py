"""Shared connection settings for the examples."""
import os

from openai import OpenAI
import requests

SWARM_URL = os.environ.get("SWARM_URL", "http://127.0.0.1:43100").rstrip("/")
SWARM_API_KEY = os.environ.get("SWARM_API_KEY") or os.environ.get("SWARM_API_TOKEN")
if not SWARM_API_KEY:
    raise SystemExit("Set SWARM_API_KEY to a token from Settings > Server > Account > API tokens.")

# Distributed generation can take minutes for long answers.
client = OpenAI(base_url=f"{SWARM_URL}/v1", api_key=SWARM_API_KEY, timeout=600)
session = requests.Session()
session.headers.update({"Authorization": f"Bearer {SWARM_API_KEY}"})


def active_model() -> str:
    models = client.models.list().data
    if not models:
        raise SystemExit("The swarm has no active model yet. Select one in the dashboard.")
    return models[0].id


def enabled_agents() -> list[dict]:
    response = session.get(f"{SWARM_URL}/v1/agents", timeout=30)
    response.raise_for_status()
    return response.json()["data"]
