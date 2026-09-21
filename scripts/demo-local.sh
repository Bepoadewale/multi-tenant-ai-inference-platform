#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
payments_token=$(jq -r '.payments' "${repo_root}/.local/identity/tokens.json")
docker compose -f "${repo_root}/docker-compose.yml" exec -T redis redis-cli FLUSHDB >/dev/null

request() {
  local port="$1"
  curl -sS --connect-timeout 2 --max-time 5 -o /tmp/inference-demo-response.json -w '%{http_code}' \
    "http://localhost:${port}/v1/chat/completions" \
    -H "Authorization: Bearer ${payments_token}" -H 'content-type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"good and safe"}],"max_tokens":4}'
}

for port in 8081 8082 8081 8082 8081; do
  test "$(request "${port}")" = 200
done
test "$(request 8082)" = 429
grep -q 'requests_per_minute' /tmp/inference-demo-response.json
echo 'Local demo passed: signed tenant traffic reached ONNX runtime targets and Redis enforced its shared quota across two gateways.'
