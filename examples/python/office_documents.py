"""Reads a document shared from Word or Excel on this Mac and, optionally, sends it an instruction.
The instruction becomes a proposal in that document; nothing changes until its user clicks Apply.

    python office_documents.py                                   # list and read the first open document
    python office_documents.py Costos.xlsx "Add a row 'Revisado' with today's date below the table."
"""
import json
import os
import sys

import urllib3

from swarm import session

# The add-in certificate is trusted by the macOS Keychain, not by Python; the host only listens on localhost.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
OFFICE_URL = os.environ.get("OFFICE_URL", "https://localhost:43110")


def request(target: str, kind: str, arguments: dict) -> dict:
    response = session.post(
        f"{OFFICE_URL}/api/swarm/documents/request",
        json={"target": target, "kind": kind, "source": "Python example", "arguments": arguments},
        verify=False,
        timeout=60,
    )
    body = response.json()
    if not response.ok:
        raise SystemExit(body.get("error", response.text))
    return body["result"]


response = session.get(f"{OFFICE_URL}/api/swarm/documents", verify=False, timeout=30)
response.raise_for_status()
documents = response.json()["data"]
for document in documents:
    print(f"{document['name']:40} {document['app']:6} {'open' if document['online'] else 'closed'}")

if "--list-only" in sys.argv[1:]:
    raise SystemExit(0)

target = sys.argv[1] if len(sys.argv) > 1 else next((d["name"] for d in documents if d["online"]), None)
if not target:
    raise SystemExit("No open shared document. Enable 'Share with swarm' in a Word or Excel pane.")

content = request(target, "read", {})
print(f"\n{target}:")
print(content["text"] if content["app"] == "word" else json.dumps(content["text"], ensure_ascii=False, indent=1))

if len(sys.argv) > 2:
    print("\nSent:", request(target, "instruction", {"instruction": sys.argv[2]}))
