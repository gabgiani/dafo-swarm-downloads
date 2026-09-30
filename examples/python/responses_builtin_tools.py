"""Responses API with the node's built-in MCP tools. The model decides when to store or search
knowledge and when to read or change shared Office documents.

    python responses_builtin_tools.py "Remember that line 3 maintenance is every Friday at 6am."
    python responses_builtin_tools.py "Read Costos.xlsx and ask Informe.docx to add a paragraph with the total."
"""
import os
import sys

from swarm import SWARM_URL, active_model, enabled_agents, session

agents = enabled_agents()
agent = os.environ.get("AGENT") or (agents[0]["id"] if agents else None)
prompt = sys.argv[1] if len(sys.argv) > 1 else "What do you know about line 3?"
print("Question:", prompt, flush=True)

body = {
    "model": active_model(),
    "input": prompt,
    "max_tool_calls": 6,
    "tools": [{
        "type": "mcp",
        "server_label": "swarm",
        "server_url": "builtin://chat" + (f"?agent={agent}" if agent else ""),
        "allowed_tools": [
            "store_knowledge", "search_knowledge", "list_knowledge",
            "list_office_documents", "read_office_document", "send_office_document_instruction",
        ],
        "require_approval": "never",
    }],
}
if os.environ.get("SWARM_READ_ONLY") == "1":
    body["tools"][0]["allowed_tools"] = ["search_knowledge", "list_knowledge", "list_office_documents", "read_office_document"]
if agent:
    body["agent"] = agent

response = session.post(f"{SWARM_URL}/v1/responses", json=body, timeout=900)
response.raise_for_status()
for item in response.json()["output"]:
    if item["type"] == "mcp_call":
        print(f"tool {item['name']} {item['arguments']}\n  -> {item.get('output') or item.get('error')}")
    elif item["type"] == "message":
        print("\n" + item["content"][0]["text"])
