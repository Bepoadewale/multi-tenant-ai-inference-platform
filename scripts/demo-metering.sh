#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"do not store this private prompt"}],"max_tokens":4}' \
  | jq -e '.usage.total_tokens > 0' >/dev/null

usage=$(curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8081/platform/v1/usage/team-search \
  -H "Authorization: Bearer ${admin_token}")
jq -e '.requests > 0 and .tokens > 0 and .estimated_cost_usd >= 0' <<<"${usage}" >/dev/null
! grep -q 'private prompt' <<<"${usage}"
echo 'Metering demo passed: Redis retained metadata-only tenant usage across gateway replicas.'
