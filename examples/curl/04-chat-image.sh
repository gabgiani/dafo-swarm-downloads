#!/usr/bin/env bash
# Sends a local image (JPEG, PNG or WebP) to a Gemma 4 model. Usage: ./04-chat-image.sh photo.png "question"
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}
IMAGE=${1:?usage: $0 image.png [question]}
QUESTION=${2:-"Describe this image and list any visible defects."}
MODEL=$(curl -sf "$SWARM_URL/v1/models" | jq -r '.data[0].id')

case "${IMAGE##*.}" in
  jpg|jpeg|JPG|JPEG) TYPE=image/jpeg ;;
  webp|WEBP) TYPE=image/webp ;;
  *) TYPE=image/png ;;
esac
DATA_URL="data:$TYPE;base64,$(base64 < "$IMAGE" | tr -d '\n')"

jq -n --arg model "$MODEL" --arg q "$QUESTION" --arg url "$DATA_URL" '{
  model: $model,
  messages: [{ role: "user", content: [
    { type: "text", text: $q },
    { type: "image_url", image_url: { url: $url } }
  ]}]
}' | curl -sf "$SWARM_URL/v1/chat/completions" -H 'content-type: application/json' --data-binary @- \
  | jq -r '.choices[0].message.content'
