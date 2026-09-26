#!/usr/bin/env bash
# Shows the active model and the enabled agents.
set -euo pipefail
SWARM_URL=${SWARM_URL:-http://127.0.0.1:43100}

echo "Model:"
curl -sf "$SWARM_URL/v1/models" | jq -r '.data[].id'

echo "Agents:"
curl -sf "$SWARM_URL/v1/agents" | jq -r '.data[] | "\(.id)\t\(.name)"'
