#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
"${repo_root}/scripts/smoke.sh"

admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
approver_token=$(jq -r '.approver' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")

plan=$(curl -fsS --max-time 10 -X POST http://localhost:8083/release/v1/plans \
  -H "Authorization: Bearer ${admin_token}")
plan_id=$(jq -r '.id' <<<"${plan}")
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/approve" \
  -H "Authorization: Bearer ${approver_token}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/canary" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "CANARY"' >/dev/null

canary_response=$(curl -fsS --max-time 10 http://localhost:8081/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"release-aware operational evidence"}],"max_tokens":4}')

request_id=$(jq -r '.x_observability.request_id' <<<"${canary_response}")
trace_id=$(jq -r '.x_observability.trace_id' <<<"${canary_response}")
test "${trace_id}" != null
analysis=$(curl -fsS --max-time 10 \
  "http://localhost:8081/platform/v1/requests/${request_id}/analysis" \
  -H "Authorization: Bearer ${admin_token}")
jq -e --arg plan "${plan_id}" '
  .release.plan_id == $plan and
  .release.phase_at_request == "CANARY" and
  (.deployment.backend == "onnx-stable-v1" or .deployment.backend == "onnx-candidate-v2") and
  .trace_id != null and
  .cost.kind == "ESTIMATED_LOCAL_TOKEN_ALLOCATION" and
  .slo.status == "SATISFIED" and
  .privacy.raw_prompt_stored == false and
  .privacy.raw_completion_stored == false
' <<<"${analysis}" >/dev/null

for _ in $(seq 1 30); do
  if curl -sS --max-time 5 "http://localhost:3200/api/traces/${trace_id}" | jq -e '.batches? | length > 0' >/dev/null; then
    break
  fi
  sleep 2
done
curl -sS --max-time 5 "http://localhost:3200/api/traces/${trace_id}" | jq -e '.batches? | length > 0' >/dev/null

timeout_headers=$(mktemp)
timeout_status=$(curl -sS -o /tmp/inference-platform-slo-timeout.json -D "${timeout_headers}" -w '%{http_code}' --max-time 10 \
  http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-timeout-demo","messages":[{"role":"user","content":"timeout evidence"}],"max_tokens":4}')
test "${timeout_status}" = 502
timeout_request_id=$(awk 'BEGIN{IGNORECASE=1} /^x-request-id:/ {print $2}' "${timeout_headers}" | tr -d '\r')
rm "${timeout_headers}"
test -n "${timeout_request_id}"
curl -fsS --max-time 10 "http://localhost:8082/platform/v1/requests/${timeout_request_id}/analysis" \
  -H "Authorization: Bearer ${admin_token}" \
  | jq -e '.outcome == "backend_error" and .slo.status == "VIOLATED"' >/dev/null

wait_for_positive_metric() {
  local query=$1
  local label=$2
  for _ in $(seq 1 30); do
    if curl -sS --max-time 5 --data-urlencode "query=${query}" \
      http://localhost:9090/api/v1/query \
      | jq -e '.data.result[0]?.value[1] | tonumber? > 0' >/dev/null; then
      return 0
    fi
    sleep 2
  done
  echo "Prometheus did not expose positive ${label} within the bounded timeout." >&2
  return 1
}

wait_for_positive_metric 'sum(inference_gateway_estimated_cost_usd_total)' 'estimated-cost evidence'
wait_for_positive_metric \
  'sum(inference_gateway_request_slo_evaluations_total{status="VIOLATED"})' \
  'violated-SLO evidence'

curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/rollback" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "ROLLED_BACK"' >/dev/null

echo "Operational-evidence demo passed: request ${request_id} correlated a real Tempo trace, canary release plan, local SLO, and explicitly estimated cost; a backend timeout was recorded as an SLO violation."
