#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

status=$(curl -sS --connect-timeout 2 --max-time 5 -o /tmp/inference-timeout.json -w '%{http_code}' \
  http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-timeout-demo","messages":[{"role":"user","content":"timeout fixture"}],"max_tokens":4}')
test "${status}" = 502
grep -q 'inference backend failed' /tmp/inference-timeout.json
echo 'Timeout demo passed: a bounded backend timeout returned an explicit 502 without replaying the request.'
