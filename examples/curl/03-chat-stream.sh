#!/usr/bin/env bash
# Streams tokens as they are generated (Server-Sent Events).
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
PROMPT=${1:-"Write a short paragraph about predictive maintenance."}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')

jq -n --arg model "$MODEL" --arg prompt "$PROMPT" '{
  model: $model, stream: true, stream_options: { include_usage: true },
  messages: [{ role: "user", content: $prompt }]
}' | curl -sfN "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @- \
  | while IFS= read -r line; do
      data=${line#data: }
      [ "$line" = "$data" ] && continue
      [ "$data" = "[DONE]" ] && { echo; break; }
      echo "$data" | jq -j '(.choices[0].delta.content // empty), (if .usage then "\n[\(.usage.completion_tokens) tokens]" else empty end)'
    done
