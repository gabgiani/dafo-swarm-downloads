#!/usr/bin/env bash
# Lists documents shared from Word/Excel on this Mac, reads one, and optionally sends it an instruction.
# Usage: ./10-office-documents.sh [document-name] ["instruction"]
# Requires the macOS app and a pane with "Share with swarm" enabled. -k is used because the
# add-in certificate is trusted by macOS Keychain, not by curl.
set -euo pipefail
OFFICE_URL=${OFFICE_URL:-https://localhost:43110}

echo "Shared documents:"
curl -skf "$OFFICE_URL/api/swarm/documents" | jq -r '.data[] | "\(.name)\t\(.app)\t\(if .online then "open" else "closed" end)"'

DOC=${1:-$(curl -skf "$OFFICE_URL/api/swarm/documents" | jq -r '[.data[] | select(.online)][0].name // empty')}
[ -n "$DOC" ] || { echo "No open shared document. Enable 'Share with swarm' in a Word or Excel pane." >&2; exit 1; }

echo; echo "Reading $DOC:"
jq -n --arg target "$DOC" '{target: $target, kind: "read", source: "curl example", arguments: {}}' \
  | curl -skf "$OFFICE_URL/api/swarm/documents/request" -H 'content-type: application/json' --data-binary @- \
  | jq '.result'

if [ -n "${2:-}" ]; then
  echo; echo "Sending instruction to $DOC (its user reviews and applies it):"
  jq -n --arg target "$DOC" --arg instruction "$2" \
    '{target: $target, kind: "instruction", source: "curl example", arguments: {instruction: $instruction}}' \
    | curl -skf "$OFFICE_URL/api/swarm/documents/request" -H 'content-type: application/json' --data-binary @- \
    | jq '.result'
fi
