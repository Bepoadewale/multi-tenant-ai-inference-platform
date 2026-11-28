#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "${repo_root}/docker-compose.yml")

"${repo_root}/scripts/smoke.sh"
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")
redis_stopped=0

restore_redis() {
  [[ "${redis_stopped}" == 1 ]] || return 0
  "${compose[@]}" start redis >/dev/null || return 1
  for _ in $(seq 1 30); do
    if "${compose[@]}" exec -T redis redis-cli ping 2>/dev/null | grep -qx PONG; then
      redis_stopped=0
      return 0
    fi
    sleep 1
  done
  echo 'Redis did not become healthy after the outage drill.' >&2
  return 1
}

finish() {
  local result=$?
  trap - EXIT
  if ! restore_redis; then
    result=1
  fi
  exit "${result}"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

redis_stopped=1
"${compose[@]}" stop redis >/dev/null

for port in 8081 8082; do
  response=$(curl -sS --connect-timeout 2 --max-time 5 \
    "http://localhost:${port}/v1/chat/completions" \
    -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"redis outage drill"}],"max_tokens":4}' \
    -w '\n%{http_code}' || true)
  status=${response##*$'\n'}
  body=${response%$'\n'*}
  detail=$(jq -r '.detail // "unparseable response"' <<<"${body}" 2>/dev/null || true)
  if [[ "${status}" != 503 ]] || ! jq -e '.detail == "shared rollout state unavailable"' <<<"${body}" >/dev/null; then
    echo "Redis outage drill failed: gateway ${port} returned HTTP ${status}, detail=${detail}; expected fail-closed HTTP 503." >&2
    exit 1
  fi
  echo "Observed gateway ${port}: HTTP 503, shared rollout state unavailable."
done

restore_redis
for port in 8081 8082; do
  ready=0
  for _ in $(seq 1 30); do
    if curl -fsS --connect-timeout 2 --max-time 5 "http://localhost:${port}/healthz" \
      | jq -e '.status == "ok" and .admission_ready == true' >/dev/null; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "${ready}" != 1 ]]; then
    echo "Redis recovery drill failed: gateway ${port} did not restore admission readiness." >&2
    exit 1
  fi
  echo "Observed gateway ${port}: readiness restored after Redis restart."
done

echo 'Redis outage drill passed: both independent gateways rejected inference while Redis was unavailable and recovered after Redis restarted.'
