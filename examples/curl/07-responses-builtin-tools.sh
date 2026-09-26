#!/usr/bin/env bash
# Responses API with the node's built-in tools: the model stores and searches the agent's knowledge base.
# Usage: ./07-responses-builtin-tools.sh "Remember that line 3 maintenance is every Friday at 6am."
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
PROMPT=${1:-"What do you know about line 3?"}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')
AGENT=${AGENT:-$(curl -sf "$SWARM_URL/v1/agents" | jq -r '.data[0].id // empty')}
[ -n "$AGENT" ] || { echo "Create an agent first (see 08-agents.sh)" >&2; exit 1; }

jq -n --arg model "$MODEL" --arg agent "$AGENT" --arg prompt "$PROMPT" '{
  model: $model, agent: $agent, input: $prompt, max_tool_calls: 4,
  tools: [{
    type: "mcp", server_label: "swarm",
    server_url: ("builtin://chat?agent=" + $agent),
    allowed_tools: ["store_knowledge", "search_knowledge", "list_knowledge",
                    "list_office_documents", "read_office_document", "send_office_document_instruction"],
    require_approval: "never"
  }]
}' | curl -sf "$SWARM_URL/v1/responses" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.output[]
      | if .type == "mcp_call" then "tool \(.name) \(.arguments) -> \(.output // .error)"
        elif .type == "message" then "\n" + .content[0].text
        else empty end'
