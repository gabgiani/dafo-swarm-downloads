"""Loads facts from a CSV (subject,predicate,object,content) into an agent's knowledge base,
skipping facts that already exist, then runs a test search.

    python load_knowledge_csv.py knowledge.csv                 # first enabled agent
    AGENT=agent-... python load_knowledge_csv.py my-facts.csv
"""
import csv
import os
import sys

import requests

from swarm import SWARM_URL

path = sys.argv[1] if len(sys.argv) > 1 else "knowledge.csv"
agents = requests.get(f"{SWARM_URL}/v1/agents", timeout=30).json()["data"]
if not agents and not os.environ.get("AGENT"):
    raise SystemExit("No enabled agent. Create one first.")
agent = os.environ.get("AGENT") or agents[0]["id"]
base = f"{SWARM_URL}/api/agents/{agent}/knowledge"

existing = {
    (item["subject"], item["predicate"], item["object"])
    for item in requests.get(base, timeout=30).json()
}

stored = skipped = 0
with open(path, newline="", encoding="utf-8") as handle:
    for row in csv.DictReader(handle):
        key = (row["subject"].strip(), row["predicate"].strip(), row["object"].strip())
        if key in existing:
            skipped += 1
            continue
        response = requests.post(base, json=row, timeout=60)
        response.raise_for_status()
        stored += 1
        print("stored", response.json()["id"], *key)

print(f"{stored} stored, {skipped} already present")

results = requests.post(f"{base}/search", json={"query": "line 3 maintenance", "limit": 3}, timeout=60).json()
for result in results:
    item = result["item"]
    print(f"{result['score']:.2f}  {item['subject']} [{item['predicate']}] {item['object']}  ({result['match_type']})")
