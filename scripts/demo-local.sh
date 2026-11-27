#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
payments_token=$(jq -r '.payments' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")
docker compose -f "${repo_root}/docker-compose.yml" exec -T redis redis-cli FLUSHDB >/dev/null

curl -sS --connect-timeout 2 --max-time 5 -N http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","stream":true,"messages":[{"role":"user","content":"good streaming request"}],"max_tokens":4}' \
  >/tmp/inference-stream.json
if ! grep -q 'classification=positive' /tmp/inference-stream.json; then
  echo 'Streaming demo failed: response did not contain the expected positive classification.' >&2
  cat /tmp/inference-stream.json >&2
  exit 1
fi
if ! grep -q 'data: \[DONE\]' /tmp/inference-stream.json; then
  echo 'Streaming demo failed: response did not contain the completion marker.' >&2
  cat /tmp/inference-stream.json >&2
  exit 1
fi

request() {
  local port="$1"
  curl -sS --connect-timeout 2 --max-time 5 -o /tmp/inference-demo-response.json -w '%{http_code}' \
    "http://localhost:${port}/v1/chat/completions" \
    -H "Authorization: Bearer ${payments_token}" -H 'content-type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"good and safe"}],"max_tokens":4}'
}

for port in 8081 8082 8081 8082 8081; do
  status="$(request "${port}")"
  if [[ "${status}" != 200 ]]; then
    echo "Tenant inference demo failed: gateway port ${port} returned HTTP ${status}; expected 200." >&2
    cat /tmp/inference-demo-response.json >&2
    exit 1
  fi
done
status="$(request 8082)"
if [[ "${status}" != 429 ]]; then
  echo "Quota demo failed: gateway port 8082 returned HTTP ${status}; expected 429." >&2
  cat /tmp/inference-demo-response.json >&2
  exit 1
fi
if ! grep -q 'requests_per_minute' /tmp/inference-demo-response.json; then
  echo 'Quota demo failed: rejection did not name the request-rate policy.' >&2
  cat /tmp/inference-demo-response.json >&2
  exit 1
fi
echo 'Local demo passed: signed tenant traffic reached ONNX runtime targets and Redis enforced its shared quota across two gateways.'
