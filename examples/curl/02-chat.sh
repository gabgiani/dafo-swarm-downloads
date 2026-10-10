#!/usr/bin/env bash
# A single chat completion. Usage: ./02-chat.sh "your question"
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
: "${SWARM_API_KEY:?Set SWARM_API_KEY to an API token from Settings > API > API Access}"
# Every call to the swarm carries the API token.
curl() { command curl -H "Authorization: Bearer $SWARM_API_KEY" "$@"; }
PROMPT=${1:-"Explain OEE (Overall Equipment Effectiveness) in two sentences."}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')

jq -n --arg model "$MODEL" --arg prompt "$PROMPT" '{
  model: $model,
  messages: [
    { role: "system", content: "You are a concise manufacturing assistant." },
    { role: "user", content: $prompt }
  ],
  max_completion_tokens: 300,
  temperature: 0.2
}' | curl -sf "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.choices[0].message.content, "\n[\(.usage.completion_tokens) tokens, finish: \(.choices[0].finish_reason)]"'
