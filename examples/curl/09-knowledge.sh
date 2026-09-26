#!/usr/bin/env bash
# Adds facts to an agent's knowledge base, searches them, and asks a question that uses them.
# Usage: AGENT=agent-... ./09-knowledge.sh   (defaults to the first enabled agent)
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')
AGENT=${AGENT:-$(curl -sf "$SWARM_URL/v1/agents" | jq -r '.data[0].id // empty')}
[ -n "$AGENT" ] || { echo "Create an agent first (see 08-agents.sh)" >&2; exit 1; }

add() {
  jq -n --arg s "$1" --arg p "$2" --arg o "$3" --arg c "$4" '{subject: $s, predicate: $p, object: $o, content: $c}' \
    | curl -sf -X POST "$SWARM_URL/api/agents/$AGENT/knowledge" -H 'content-type: application/json' --data-binary @- \
    | jq -r '"stored \(.id): \(.subject) [\(.predicate)] \(.object)"'
}
add "Line 3" "plc_supplier" "Siemens" "Line 3 uses a Siemens S7-1500 PLC. Contact: Carlos Gómez, carlos@example.com."
add "Line 3" "maintenance_window" "Friday 06:00" "Preventive maintenance of line 3 runs every Friday from 06:00 to 08:00."
add "ACME Corp" "payment_terms" "60 days" "ACME pays 60 days from invoice date; 2% discount for early payment."

echo; echo "Search:"
curl -sf -X POST "$SWARM_URL/api/agents/$AGENT/knowledge/search" -H 'content-type: application/json' \
  -d '{"query": "when is line 3 maintenance", "limit": 3}' \
  | jq -r '.[] | "\(.score)\t\(.item.subject) [\(.item.predicate)] \(.item.object)\t(\(.match_type))"'

echo; echo "Answer using the agent (facts are added automatically):"
jq -n --arg model "$MODEL" --arg agent "$AGENT" '{
  model: $model, agent: $agent,
  messages: [{ role: "user", content: "Can we schedule a line 3 intervention on Friday at 7am? Who is the PLC contact?" }]
}' | curl -sf "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.choices[0].message.content'
