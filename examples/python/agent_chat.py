"""Chat as an agent. The node adds the agent's instructions and its most relevant knowledge facts.

    python agent_chat.py "Who is the PLC contact for line 3?"          # first enabled agent
    AGENT=agent-... python agent_chat.py "..."                          # a specific agent
"""
import os
import sys

import requests

from swarm import SWARM_URL, active_model, client

agents = requests.get(f"{SWARM_URL}/v1/agents", timeout=30).json()["data"]
if not agents:
    raise SystemExit("No enabled agent. Create one in the dashboard or with curl/08-agents.sh.")
agent = os.environ.get("AGENT") or agents[0]["id"]
print("Agent:", next((a["name"] for a in agents if a["id"] == agent), agent))

question = sys.argv[1] if len(sys.argv) > 1 else "What do you know about line 3?"
reply = client.chat.completions.create(
    model=active_model(),
    messages=[{"role": "user", "content": question}],
    extra_body={"agent": agent},  # DAFO Swarm extension to the OpenAI request
)
print(reply.choices[0].message.content)
