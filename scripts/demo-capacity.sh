#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"

search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")
payments_token=$(jq -r '.payments' "${repo_root}/.local/identity/tokens.json")
analytics_token=$(jq -r '.analytics' "${repo_root}/.local/identity/tokens.json")
reporting_token=$(jq -r '.reporting' "${repo_root}/.local/identity/tokens.json")
admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
results=$(mktemp -d)
trap 'rm -rf "${results}"' EXIT
docker compose -f "${repo_root}/docker-compose.yml" exec -T redis redis-cli FLUSHDB >/dev/null

request() {
  local token="$1" model="$2" output="$3"
  curl -sS --connect-timeout 2 --max-time 5 -o "${output}.json" -w '%{http_code}' \
    http://localhost:8081/v1/chat/completions \
    -H "Authorization: Bearer ${token}" -H 'content-type: application/json' \
    -d "{\"model\":\"${model}\",\"messages\":[{\"role\":\"user\",\"content\":\"good\"}],\"max_tokens\":4}" \
    >"${output}.status"
}

# One search request holds that tenant's only simulated slot while the CPU fixture runs.
request "${search_token}" chat-default "${results}/search-primary" &
search_pid=$!
sleep 0.05
request "${search_token}" chat-default "${results}/search-denied"
test "$(cat "${results}/search-denied.status")" = 429
grep -q 'simulated GPU tenant capacity quota exceeded' "${results}/search-denied.json"

# A different tenant receives its own allocation; capacity remains globally bounded at two slots.
request "${payments_token}" chat-default "${results}/payments-primary" &
payments_pid=$!
sleep 0.05

# This tenant is allowed to wait briefly for an existing capacity holder to finish.
request "${reporting_token}" chat-default "${results}/reporting-queued" &
reporting_pid=$!
sleep 0.05

# The third tenant's approved fallback request reaches the real CPU ONNX runtime, not a fake GPU.
request "${analytics_token}" chat-cpu-fallback-demo "${results}/analytics-fallback"
test "$(cat "${results}/analytics-fallback.status")" = 200
jq -e '.x_capacity.decision == "CPU_FALLBACK" and .x_capacity.simulated_hardware == true' \
  "${results}/analytics-fallback.json" >/dev/null

curl -fsS --connect-timeout 2 --max-time 5 http://localhost:8081/platform/v1/capacity \
  -H "Authorization: Bearer ${admin_token}" \
  | jq -e '.hardware == "SIMULATED" and .pools[0].total_slots == 2' >/dev/null

wait "${search_pid}" "${payments_pid}"
wait "${reporting_pid}"
test "$(cat "${results}/search-primary.status")" = 200
test "$(cat "${results}/payments-primary.status")" = 200
test "$(cat "${results}/reporting-queued.status")" = 200
jq -e '.x_capacity.queued == true and .x_capacity.decision == "SIMULATED_GPU_ADMITTED"' \
  "${results}/reporting-queued.json" >/dev/null
echo 'Capacity demo passed: shared simulated-GPU quota admitted, queued, rejected, and CPU-fell-back while inference stayed on real ONNX CPU.'
