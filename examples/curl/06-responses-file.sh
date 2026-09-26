#!/usr/bin/env bash
# Responses API with a text file attached. Usage: ./06-responses-file.sh notes.txt "question"
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
FILE=${1:?usage: $0 file.(txt|md|csv|json|pdf) [question]}
QUESTION=${2:-"Summarise this file in five bullet points."}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')

case "${FILE##*.}" in
  pdf) TYPE=application/pdf ;;
  csv) TYPE=text/csv ;;
  json) TYPE=application/json ;;
  md) TYPE=text/markdown ;;
  *) TYPE=text/plain ;;
esac
DATA_URL="data:$TYPE;base64,$(base64 < "$FILE" | tr -d '\n')"

jq -n --arg model "$MODEL" --arg q "$QUESTION" --arg name "$(basename "$FILE")" --arg data "$DATA_URL" '{
  model: $model,
  input: [{ role: "user", content: [
    { type: "input_text", text: $q },
    { type: "input_file", filename: $name, file_data: $data }
  ]}]
}' | curl -sf "$SWARM_URL/v1/responses" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.output[] | select(.type == "message") | .content[0].text'
