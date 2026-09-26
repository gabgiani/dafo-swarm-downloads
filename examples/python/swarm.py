"""Shared connection settings for the examples."""
import os

from openai import OpenAI

SWARM_URL = os.environ.get("SWARM_URL", "http://127.0.0.1:43100").rstrip("/")

# The node ignores the API key, but the SDK requires one. Distributed generation can take
# minutes for long answers, so the timeout is generous.
client = OpenAI(base_url=f"{SWARM_URL}/v1", api_key="unused", timeout=600)


def active_model() -> str:
    models = client.models.list().data
    if not models:
        raise SystemExit("The swarm has no active model yet. Select one in the dashboard.")
    return models[0].id
