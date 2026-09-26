#!/usr/bin/env bash
# Creates an agent, uses it in a chat, and optionally deletes it (DELETE=1).
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')

AGENT=$(curl -sf -X POST "$SWARM_URL/api/agents" -H 'content-type: application/json' -d '{
  "name": "Plant assistant (example)",
  "system_prompt": "You are the production assistant of ACME Metal. Answer briefly and cite the line number when relevant.",
  "enabled": true
}' | jq -r '.id')
echo "Created agent $AGENT"

jq -n --arg model "$MODEL" --arg agent "$AGENT" '{
  model: $model, agent: $agent,
  messages: [{ role: "user", content: "Introduce yourself in one sentence." }]
}' | curl -sf "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.choices[0].message.content'

if [ "${DELETE:-0}" = "1" ]; then
  curl -sf -X DELETE "$SWARM_URL/api/agents/$AGENT" && echo "Deleted agent $AGENT"
fi
