#!/usr/bin/env bash
set -euo pipefail

# Prove that a delegated agent can discover only bounded tools, inspect its own
# tenant's metadata-only evidence, and prepare (but not approve or execute) one
# allowlisted rollback plan for a failed canary.

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "${repo_root}/docker-compose.yml")
"${repo_root}/scripts/smoke.sh"

tokens="${repo_root}/.local/identity/tokens.json"
agent_token=$(jq -r '.delegated_agent' "${tokens}")
search_token=$(jq -r '.search' "${tokens}")
reporting_token=$(jq -r '.reporting' "${tokens}")
admin_token=$(jq -r '.admin' "${tokens}")
release_approver_token=$(jq -r '.approver' "${tokens}")
remediation_approver_token=$(jq -r '.remediation_approver' "${tokens}")
release_plan_id=""

invoke_until_admitted() {
  local url="$1"
  local token="$2"
  local prompt="$3"
  local response status
  for _ in $(seq 1 20); do
    response=$(mktemp)
    status=$(curl -sS -o "${response}" -w '%{http_code}' --max-time 10 "${url}/v1/chat/completions" \
      -H "Authorization: Bearer ${token}" -H 'content-type: application/json' \
      -d "{\"model\":\"chat-default\",\"messages\":[{\"role\":\"user\",\"content\":\"${prompt}\"}],\"max_tokens\":4}")
    if test "${status}" = 200; then
      cat "${response}"
      rm -f "${response}"
      return 0
    fi
    rm -f "${response}"
    if test "${status}" != 429; then
      echo "inference request unexpectedly returned ${status}" >&2
      return 1
    fi
    sleep 0.3
  done
  echo "inference request was not admitted before bounded retry limit" >&2
  return 1
}

recover() {
  "${compose[@]}" up -d --wait runtime-v2 >/dev/null || true
  if test -n "${release_plan_id}"; then
    curl -sS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${release_plan_id}/rollback" \
      -H "Authorization: Bearer ${admin_token}" >/dev/null || true
  fi
}
trap recover EXIT

# Discovery is filtered: the agent sees its two read/plan tools, never privileged
# approval, execution, rollout-promotion, or arbitrary infrastructure tools.
tools=$(curl -fsS --max-time 10 http://localhost:8085/agent/v1/tools \
  -H "Authorization: Bearer ${agent_token}")
jq -e '[.tools[].name] | sort == ["get_request_evidence", "plan_canary_rollback"]' <<<"${tools}" >/dev/null

search_response=$(invoke_until_admitted http://localhost:8081 "${search_token}" "delegated evidence")
search_request_id=$(jq -r '.x_observability.request_id' <<<"${search_response}")
evidence=$(curl -fsS --max-time 10 http://localhost:8085/agent/v1/tools/get_request_evidence \
  -H "Authorization: Bearer ${agent_token}" -H 'content-type: application/json' \
  -d "{\"arguments\":{\"request_id\":\"${search_request_id}\"}}")
jq -e '.result.tenant == "team-search" and (.result | has("request_id"))' <<<"${evidence}" >/dev/null

reporting_response=$(invoke_until_admitted http://localhost:8082 "${reporting_token}" "other tenant")
reporting_request_id=$(jq -r '.x_observability.request_id' <<<"${reporting_response}")
cross_tenant_status=$(curl -sS -o /tmp/agent-tools-cross-tenant.json -w '%{http_code}' --max-time 10 \
  http://localhost:8085/agent/v1/tools/get_request_evidence \
  -H "Authorization: Bearer ${agent_token}" -H 'content-type: application/json' \
  -d "{\"arguments\":{\"request_id\":\"${reporting_request_id}\"}}")
test "${cross_tenant_status}" = 403

# Make a failed canary request without granting the agent a route-management power.
release_plan=$(curl -fsS --max-time 10 -X POST 'http://localhost:8083/release/v1/plans?canary_weight=99' \
  -H "Authorization: Bearer ${admin_token}")
release_plan_id=$(jq -r '.id' <<<"${release_plan}")
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${release_plan_id}/approve" \
  -H "Authorization: Bearer ${release_approver_token}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS --max-time 10 -X POST "http://localhost:8083/release/v1/plans/${release_plan_id}/canary" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.status == "CANARY"' >/dev/null

"${compose[@]}" stop runtime-v2 >/dev/null
failure_request_id=""
for _ in $(seq 1 12); do
  headers=$(mktemp)
  status=$(curl -sS -o /tmp/agent-tools-failure.json -D "${headers}" -w '%{http_code}' --max-time 10 \
    http://localhost:8081/v1/chat/completions \
    -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
    -d '{"model":"chat-default","messages":[{"role":"user","content":"candidate outage for delegated plan"}],"max_tokens":4}')
  if test "${status}" = 502; then
    failure_request_id=$(awk 'BEGIN{IGNORECASE=1} /^x-request-id:/ {print $2}' "${headers}" | tr -d '\r')
    rm -f "${headers}"
    break
  fi
  rm -f "${headers}"
done
test -n "${failure_request_id}"
"${compose[@]}" up -d --wait runtime-v2 >/dev/null

agent_plan=$(curl -fsS --max-time 10 -X POST http://localhost:8085/agent/v1/tools/plan_canary_rollback \
  -H "Authorization: Bearer ${agent_token}" -H 'content-type: application/json' \
  -d "{\"arguments\":{\"request_id\":\"${failure_request_id}\"}}")
remediation_plan_id=$(jq -r '.result.id' <<<"${agent_plan}")
test -n "${remediation_plan_id}"

# The same delegated identity cannot self-approve or directly execute its plan.
approve_status=$(curl -sS -o /tmp/agent-tools-approve.json -w '%{http_code}' --max-time 10 \
  -X POST "http://localhost:8084/remediation/v1/plans/${remediation_plan_id}/approve" \
  -H "Authorization: Bearer ${agent_token}")
execute_status=$(curl -sS -o /tmp/agent-tools-execute.json -w '%{http_code}' --max-time 10 \
  -X POST "http://localhost:8084/remediation/v1/plans/${remediation_plan_id}/execute" \
  -H "Authorization: Bearer ${agent_token}")
test "${approve_status}" = 403
test "${execute_status}" = 403

curl -fsS --max-time 10 -X POST "http://localhost:8084/remediation/v1/plans/${remediation_plan_id}/approve" \
  -H "Authorization: Bearer ${remediation_approver_token}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS --max-time 10 -X POST "http://localhost:8084/remediation/v1/plans/${remediation_plan_id}/execute" \
  -H "Authorization: Bearer ${admin_token}" | jq -e '.verified == true and .plan.status == "EXECUTED"' >/dev/null

verified=$(curl -fsS --max-time 10 http://localhost:8082/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'content-type: application/json' \
  -d '{"model":"chat-default","messages":[{"role":"user","content":"delegated rollback verified"}],"max_tokens":4}')
test "$(jq -r '.x_backend' <<<"${verified}")" = onnx-stable-v1

for _ in $(seq 1 30); do
  if curl -sS --max-time 5 --data-urlencode \
    'query=sum(inference_gateway_agent_tool_calls_total{outcome="ALLOWED"})' \
    http://localhost:9090/api/v1/query | jq -e '.data.result[0]?.value[1] | tonumber? >= 2' >/dev/null; then
    break
  fi
  sleep 2
done
curl -sS --max-time 5 --data-urlencode \
  'query=sum(inference_gateway_agent_tool_calls_total{outcome="ALLOWED"})' \
  http://localhost:9090/api/v1/query | jq -e '.data.result[0]?.value[1] | tonumber? >= 2' >/dev/null

"${compose[@]}" restart agent-tools >/dev/null
for _ in $(seq 1 30); do
  curl -fsS --max-time 5 http://localhost:8085/healthz >/dev/null 2>&1 && break
  sleep 1
done
audit=$(curl -fsS --max-time 10 http://localhost:8085/agent/v1/audit -H "Authorization: Bearer ${agent_token}")
jq -e '[.events[].event] | index("TOOLS_DISCOVERED") and index("TOOL_CALLED") and index("CROSS_TENANT_READ_DENIED")' <<<"${audit}" >/dev/null

echo "Delegated-agent tools demo passed: filtered discovery, same-tenant evidence, cross-tenant denial, agent-created plan ${remediation_plan_id}, independent approval/execution, durable metadata-only audit, and stable rollback were verified."
