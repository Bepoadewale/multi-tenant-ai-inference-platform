#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

restore_stable() {
  curl -fsS --connect-timeout 2 --max-time 5 -X PUT http://localhost:8081/platform/v1/rollouts/chat-default \
    -H "Authorization: Bearer ${admin_token}" -H 'content-type: application/json' \
    -d '{"weights":{"onnx-stable-v1":90,"onnx-candidate-v2":10}}' >/dev/null || true
}
trap restore_stable EXIT

curl -fsS --connect-timeout 2 --max-time 5 -X PUT http://localhost:8081/platform/v1/rollouts/chat-default \
  -H "Authorization: Bearer ${admin_token}" -H 'content-type: application/json' \
  -d '{"weights":{"onnx-stable-v1":0,"onnx-candidate-v2":100}}' \
  | jq -e '.targets[] | select(.name == "onnx-candidate-v2" and .weight == 100)' >/dev/null

response=$(curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"good routing test"}],"max_tokens":4}')
test "$(jq -r '.x_backend' <<<"${response}")" = onnx-candidate-v2
grep -q 'classification=positive' <<<"${response}"
echo 'Routing demo passed: an administrator changed weights and live traffic reached the candidate CPU ONNX target.'
