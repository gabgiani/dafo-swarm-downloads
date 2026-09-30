"""Loads facts from a CSV (subject,predicate,object,content) into an agent's knowledge base,
skipping facts that already exist, then runs a test search.

    python load_knowledge_csv.py knowledge.csv                 # first enabled agent
    AGENT=agent-... python load_knowledge_csv.py my-facts.csv
"""
import csv
import os
import sys

from swarm import SWARM_URL, enabled_agents, session

path = sys.argv[1] if len(sys.argv) > 1 else "knowledge.csv"
dry_run = os.environ.get("SWARM_DRY_RUN") == "1"
agents = enabled_agents()
if not agents and not os.environ.get("AGENT"):
    raise SystemExit("No enabled agent. Create one first.")
agent = os.environ.get("AGENT") or agents[0]["id"]
base = f"{SWARM_URL}/api/agents/{agent}/knowledge"

existing_response = session.get(base, timeout=30)
existing_response.raise_for_status()
existing = {
    (item["subject"], item["predicate"], item["object"])
    for item in existing_response.json()
}

stored = skipped = 0
with open(path, newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        key = (row["subject"].strip(), row["predicate"].strip(), row["object"].strip())
        if key in existing:
            skipped += 1
            continue
        if dry_run:
            print("would store", *key)
            continue
        response = session.post(base, json=row, timeout=60)
        response.raise_for_status()
        stored += 1
        print("stored", response.json()["id"], *key)

print(f"{stored} stored, {skipped} already present" + (" (dry run)" if dry_run else ""))

search_response = session.post(f"{base}/search", json={"query": "line 3 maintenance", "limit": 3}, timeout=60)
search_response.raise_for_status()
results = search_response.json()
for result in results:
    item = result["item"]
    print(f"{result['score']:.2f}  {item['subject']} [{item['predicate']}] {item['object']}  ({result['match_type']})")
