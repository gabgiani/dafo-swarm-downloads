#!/usr/bin/env bash
# Function calling: the model asks for a tool, we answer it, and the model writes the final reply.
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')

TOOLS='[{
  "type": "function",
  "function": {
    "name": "get_stock",
    "description": "Current warehouse stock for a part number",
    "parameters": { "type": "object", "properties": { "part": { "type": "string" } }, "required": ["part"] }
  }
}]'
MESSAGES='[{"role": "user", "content": "How many units of part A-100 do we have?"}]'

FIRST=$(jq -n --arg model "$MODEL" --argjson tools "$TOOLS" --argjson messages "$MESSAGES" \
  '{model: $model, messages: $messages, tools: $tools, tool_choice: "auto"}' \
  | curl -sf "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @-)

CALL=$(echo "$FIRST" | jq -c '.choices[0].message.tool_calls[0] // empty')
if [ -z "$CALL" ]; then
  echo "$FIRST" | jq -r '.choices[0].message.content'
  exit 0
fi
echo "Model called: $(echo "$CALL" | jq -r '.function.name') $(echo "$CALL" | jq -r '.function.arguments')"

# Replace this with a real lookup in your ERP.
RESULT='{"part":"A-100","stock":42,"warehouse":"Main"}'

jq -n --arg model "$MODEL" --argjson tools "$TOOLS" --argjson messages "$MESSAGES" \
  --argjson assistant "$(echo "$FIRST" | jq -c '.choices[0].message')" \
  --arg id "$(echo "$CALL" | jq -r '.id')" --arg result "$RESULT" \
  '{model: $model, tools: $tools,
    messages: ($messages + [$assistant, {role: "tool", tool_call_id: $id, content: $result}])}' \
  | curl -sf "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.choices[0].message.content'
