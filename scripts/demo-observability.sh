#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"observability event"}],"max_tokens":4}' \
  | jq -e '.usage.total_tokens > 0' >/dev/null

for _ in $(seq 1 12); do
  if curl -fsS --connect-timeout 2 --max-time 5 \
    --data-urlencode 'query=sum(inference_gateway_requests_total)' \
    http://localhost:9090/api/v1/query \
    | jq -e '.data.result[0].value[1] | tonumber > 0' >/dev/null; then
    break
  fi
  sleep 2
done
curl -fsS --connect-timeout 2 --max-time 5 \
  --data-urlencode 'query=sum(inference_gateway_requests_total)' \
  http://localhost:9090/api/v1/query \
  | jq -e '.data.result[0].value[1] | tonumber > 0' >/dev/null

for _ in $(seq 1 12); do
  if curl -fsS --connect-timeout 2 --max-time 5 'http://localhost:3200/api/search?limit=20' \
    | jq -e '.traces | length > 0' >/dev/null; then
    echo 'Observability demo passed: generated gateway traffic appears in Prometheus and Tempo.'
    exit 0
  fi
  sleep 2
done
echo 'Trace export did not appear in Tempo within the bounded timeout.' >&2
exit 1
