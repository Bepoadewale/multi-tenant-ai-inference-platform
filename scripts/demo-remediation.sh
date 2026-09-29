#!/usr/bin/env bash
set -euo pipefail

# Demonstrate the one allowlisted remediation capability. This intentionally
# creates a real candidate-runtime outage; it never grants a generic shell,
# Kubernetes, Docker, or cloud action to the controller.

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "${repo_root}/docker-compose.yml")
"${repo_root}/scripts/smoke.sh"

admin_token=$(jq -r '.admin' "${repo_root}/.local/identity/tokens.json")
release_approver_token=$(jq -r '.approver' "${repo_root}/.local/identity/tokens.json")
search_token=$(jq -r '.search' "${repo_root}/.local/identity/tokens.json")
plan_id=""

recover() {
  "${compose[@]}" up -d --wait runtime-v2 >/dev/null || true
  if test -n "${plan_id}"; then
    curl -sS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/rollback" \
      -H "Authorization: Bearer ${admin_token}" >/dev/null || true
  fi
}
trap recover EXIT

# A 99% candidate canary makes the real backend outage deterministic without
# adding an unsafe routing override to the remediation controller.
release_plan=$(curl -fsS --max-time 10 -X POST 'http://localhost:8083/release/v1/plans?canary_weight=99' \
  -H "Authorization: Bearer ${admin_token}")
plan_id=$(jq -r '.id' <<<"${release_plan}")
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/approve" \
  -H "Authorization: Bearer ${release_approver_token}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${plan_id}/canary" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "CANARY"' >/dev/null

"${compose[@]}" stop runtime-v2 >/dev/null
failure_request_id=""
for _ in $(seq 1 12); do
  headers=$(mktemp)
  status=$(curl -sS -o /tmp/inference-remediation-failure.json -D "${headers}" -w '%{http_code}' --max-time 10 \
    http://localhost:8081/v1/chat/completions \
    -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"candidate outage evidence"}],"max_tokens":4}')
  if test "${status}" = 502; then
    failure_request_id=$(awk 'BEGIN{IGNORECASE=1} /^x-request-id:/ {print $2}' "${headers}" | tr -d '\r')
    rm -f "${headers}"
    break
  fi
  rm -f "${headers}"
done
test -n "${failure_request_id}"

"${compose[@]}" up -d --wait runtime-v2 >/dev/null

incident=$(curl -fsS --max-time 10 -X POST http://localhost:8084/remediation/v1/incidents \
  -H "Authorization: Bearer ${admin_token}" -H 'content-type: application/json' \
  -d "{\"request_id\":\"${failure_request_id}\"}")
incident_id=$(jq -r '.incident.id' <<<"${incident}")
# Drive the known remediation workflow through the Operator Console BFF. The direct
# self-approval denial below remains important: the BFF's independent approver is
# deliberately different from the original requester.
remediation_plan=$(curl -fsS --max-time 10 -X POST "http://localhost:8091/console/v1/remediation/incidents/${incident_id}/plan")
remediation_plan_id=$(jq -r '.id' <<<"${remediation_plan}")

self_status=$(curl -sS -o /tmp/remediation-self-approval.json -w '%{http_code}' --max-time 10 \
  -X POST "http://localhost:8084/remediation/v1/plans/${remediation_plan_id}/approve" \
  -H "Authorization: Bearer ${admin_token}")
test "${self_status}" = 403
curl -fsS --max-time 10 -X POST "http://localhost:8091/console/v1/remediation/plans/${remediation_plan_id}/approve" \
  | jq -e '.status == "APPROVED"' >/dev/null

result=$(curl -fsS --max-time 10 -X POST "http://localhost:8091/console/v1/remediation/plans/${remediation_plan_id}/execute")
jq -e '.verified == true and .incident.state == "RESOLVED" and .plan.status == "EXECUTED"' <<<"${result}" >/dev/null

response=$(curl -fsS --max-time 10 http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"post-remediation verification"}],"max_tokens":4}')
test "$(jq -r '.x_backend' <<<"${response}")" = onnx-stable-v1

timeline=$(curl -fsS --max-time 10 "http://localhost:8084/remediation/v1/incidents/${incident_id}/timeline" \
  -H "Authorization: Bearer ${admin_token}")
jq -e 'map(.event) | index("INCIDENT_DETECTED") and index("PLAN_CREATED") and index("PLAN_APPROVED") and index("REMEDIATION_VERIFIED")' <<<"${timeline}" >/dev/null

for _ in $(seq 1 30); do
  if curl -sS --max-time 5 --data-urlencode \
    'query=sum(inference_gateway_remediation_actions_total{result="ROLLED_BACK"})' \
    http://localhost:9090/api/v1/query \
    | jq -e '.data.result[0]?.value[1] | tonumber? > 0' >/dev/null; then
    break
  fi
  sleep 2
done
curl -sS --max-time 5 --data-urlencode \
  'query=sum(inference_gateway_remediation_actions_total{result="ROLLED_BACK"})' \
  http://localhost:9090/api/v1/query \
  | jq -e '.data.result[0]?.value[1] | tonumber? > 0' >/dev/null

# Prove the controller has no in-memory-only incident record. The metric assertion
# intentionally precedes restart because Prometheus client counters are process-local.
"${compose[@]}" restart remediation-control >/dev/null
for _ in $(seq 1 30); do
  if curl -fsS --max-time 5 http://localhost:8084/healthz >/dev/null; then break; fi
  sleep 1
done
curl -fsS --max-time 10 "http://localhost:8084/remediation/v1/incidents/${incident_id}" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.incident.state == "RESOLVED" and (.timeline | length >= 4)' >/dev/null

echo "Governed-remediation demo passed: observed request ${failure_request_id} created incident ${incident_id}; independent approval, bounded stable rollback, durable audit, and post-action ONNX verification succeeded."
