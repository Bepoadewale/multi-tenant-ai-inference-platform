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
stage="starting capacity requests"
report_failure() {
  local status_file body
  echo "Capacity demo failed at: ${stage}" >&2
  for status_file in "${results}"/*.status; do
    [[ -f "${status_file}" ]] || continue
    body="${status_file%.status}.json"
    printf '  %s: HTTP %s\n' "$(basename "${status_file%.status}")" "$(cat "${status_file}")" >&2
    if [[ -s "${body}" ]] && jq -e . "${body}" >/dev/null 2>&1; then
      jq -c '{detail, error, x_capacity, usage, mode, pools} | with_entries(select(.value != null))' "${body}" >&2
    fi
  done
}
on_exit() {
  local result=$?
  trap - EXIT
  if ((result != 0)); then report_failure; fi
  rm -rf -- "${results}"
}
trap on_exit EXIT
expect_status() {
  local name="$1" expected="$2" actual
  actual=$(cat "${results}/${name}.status")
  if [[ "${actual}" != "${expected}" ]]; then
    echo "${name}: expected HTTP ${expected}, received HTTP ${actual}" >&2
    return 1
  fi
}
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
stage="start search tenant capacity holder"
request "${search_token}" chat-default "${results}/search-primary" &
search_pid=$!
sleep 0.05
stage="verify search tenant quota rejection"
request "${search_token}" chat-default "${results}/search-denied"
expect_status search-denied 429
grep -q 'simulated GPU tenant capacity quota exceeded' "${results}/search-denied.json"

# A different tenant receives its own allocation; capacity remains globally bounded at two slots.
stage="start payments tenant capacity holder"
request "${payments_token}" chat-default "${results}/payments-primary" &
payments_pid=$!
sleep 0.05

# This tenant is allowed to wait briefly for an existing capacity holder to finish.
stage="start reporting tenant queued request"
request "${reporting_token}" chat-default "${results}/reporting-queued" &
reporting_pid=$!
sleep 0.05

# The third tenant's approved fallback request reaches the real CPU ONNX runtime, not a fake GPU.
stage="verify analytics CPU fallback response"
request "${analytics_token}" chat-cpu-fallback-demo "${results}/analytics-fallback"
expect_status analytics-fallback 200
jq -e '.x_capacity.decision == "CPU_FALLBACK" and .x_capacity.simulated_hardware == true' \
  "${results}/analytics-fallback.json" >/dev/null

stage="verify administrative capacity snapshot"
curl -sS --connect-timeout 2 --max-time 5 -o "${results}/capacity-snapshot.json" -w '%{http_code}' \
  http://localhost:8081/platform/v1/capacity \
  -H "Authorization: Bearer ${admin_token}" \
  >"${results}/capacity-snapshot.status"
expect_status capacity-snapshot 200
jq -e '.mode == "SIMULATED_HARDWARE_QUOTA_ACCOUNTING" and .pools[0].total_slots == 2' \
  "${results}/capacity-snapshot.json" >/dev/null

stage="wait for capacity holders and queued request"
wait "${search_pid}" "${payments_pid}"
wait "${reporting_pid}"
expect_status search-primary 200
expect_status payments-primary 200
expect_status reporting-queued 200
jq -e '.x_capacity.queued == true and .x_capacity.decision == "SIMULATED_GPU_ADMITTED"' \
  "${results}/reporting-queued.json" >/dev/null
echo 'Capacity demo passed: shared simulated-GPU quota admitted, queued, rejected, and CPU-fell-back while inference stayed on real ONNX CPU.'
