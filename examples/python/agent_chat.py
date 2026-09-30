"""Chat as an agent. The node adds the agent's instructions and its most relevant knowledge facts.

    python agent_chat.py "Who is the PLC contact for line 3?"          # first enabled agent
    AGENT=agent-... python agent_chat.py "..."                          # a specific agent
"""
import argparse
import os
import sys

from swarm import active_model, client, enabled_agents

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("question", nargs="?", default="What do you know about line 3?")
parser.add_argument("--max-tokens", type=int, default=300, help="Maximum answer tokens (default: 300).")
args = parser.parse_args()
agents = enabled_agents()
if not agents:
    raise SystemExit("No enabled agent. Create one in the dashboard or with curl/08-agents.sh.")
agent = os.environ.get("AGENT") or agents[0]["id"]
print("Agent:", next((a["name"] for a in agents if a["id"] == agent), agent))

question = args.question
print("Question:", question, flush=True)
reply = client.chat.completions.create(
    model=active_model(),
    messages=[{"role": "user", "content": question}],
    extra_body={"agent": agent},  # DAFO Swarm extension to the OpenAI request
    max_completion_tokens=args.max_tokens,
)
print("Answer:", reply.choices[0].message.content)
print(f"[{reply.usage.completion_tokens} tokens, finish: {reply.choices[0].finish_reason}]")
if reply.choices[0].finish_reason == "length":
    print("Answer reached the token limit; retry with --max-tokens 512 if the model context allows it.", file=sys.stderr)
