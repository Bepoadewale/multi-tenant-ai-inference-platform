#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "${repo_root}/docker-compose.yml")
"${repo_root}/scripts/smoke.sh"
admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

"${compose[@]}" exec -T redis redis-cli FLUSHDB >/dev/null
curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"restart recovery evidence"}],"max_tokens":4}' \
  | jq -e '.usage.total_tokens > 0' >/dev/null

"${compose[@]}" restart gateway-1 >/dev/null
for _ in $(seq 1 30); do
  if curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8081/healthz >/dev/null; then
    break
  fi
  sleep 1
done

usage=$(curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8082/platform/v1/usage/team-search \
  -H "Authorization: Bearer ${admin_token}")
jq -e '.requests == 1 and .tokens > 0' <<<"${usage}" >/dev/null
echo 'Recovery demo passed: a gateway restart retained tenant usage in durable Redis state.'
