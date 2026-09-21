#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "${repo_root}/docker-compose.yml")
"${repo_root}/scripts/smoke.sh"
admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

recover() {
  "${compose[@]}" up -d --wait runtime-v2 >/dev/null || true
  curl -fsS --connect-timeout 2 --max-time 5 -X PUT http://localhost:8081/platform/v1/rollouts/chat-default \
    -H "Authorization: Bearer ${admin_token}" -H 'content-type: application/json' \
    -d '{"weights":{"onnx-stable-v1":90,"onnx-candidate-v2":10}}' >/dev/null || true
}
trap recover EXIT

curl -fsS --connect-timeout 2 --max-time 5 -X PUT http://localhost:8081/platform/v1/rollouts/chat-default \
  -H "Authorization: Bearer ${admin_token}" -H 'content-type: application/json' \
  -d '{"weights":{"onnx-stable-v1":0,"onnx-candidate-v2":100}}' >/dev/null
"${compose[@]}" stop runtime-v2 >/dev/null

status=$(curl -sS --connect-timeout 2 --max-time 5 -o /tmp/inference-backend-failure.json -w '%{http_code}' \
  http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"backend failure test"}],"max_tokens":4}')
test "${status}" = 502
grep -q 'inference backend failed' /tmp/inference-backend-failure.json
echo 'Failure demo passed: an unavailable candidate backend produced an explicit 502 and no retry loop.'
