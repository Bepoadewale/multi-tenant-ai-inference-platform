#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"
payments_token=$(jq -r '.payments' "${repo_root}/.local/identity/tokens.json")
results=$(mktemp -d)
trap 'rm -rf "${results}"' EXIT
docker compose -f "${repo_root}/docker-compose.yml" exec -T redis redis-cli FLUSHDB >/dev/null

for index in $(seq 1 6); do
  port=8081
  [[ $((index % 2)) -eq 0 ]] && port=8082
  (
    curl -sS --connect-timeout 2 --max-time 5 -o "${results}/${index}.json" -w '%{http_code}' \
      "http://localhost:${port}/v1/chat/completions" \
      -H "Authorization: Bearer ${payments_token}" -H 'content-type: application/json' \
      -d '{"model":"chat-default","messages":[{"role":"user","content":"good"}],"max_tokens":4}' \
      >"${results}/${index}.status"
  ) &
done
wait

grep -q '^429$' "${results}"/*.status
grep -R -Eq 'queue (wait exceeded|full)' "${results}"/*.json
echo 'Overload demo passed: bounded shared admission returned an explicit 429 instead of unbounded waiting.'
