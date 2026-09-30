#!/usr/bin/env bash
set -euo pipefail

: "${INFERENCE_API_TOKEN:?Export a local signed token; see examples/README.md}"

base_url="${INFERENCE_BASE_URL:-http://localhost:8081}"
model="${INFERENCE_MODEL:-chat-default}"

curl --fail-with-body --silent --show-error \
  "${base_url}/v1/chat/completions" \
  -H "Authorization: Bearer ${INFERENCE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{\"model\":\"${model}\",\"messages\":[{\"role\":\"user\",\"content\":\"good and safe\"}],\"max_tokens\":4}"
