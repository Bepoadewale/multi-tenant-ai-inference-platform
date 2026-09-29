#!/usr/bin/env bash
set -euo pipefail

# Execute the narrow golden path a developer portal/template would call. It creates a
# durable tenant-bound integration profile, writes the generated token-free client,
# and proves that client reaches the real gateway without receiving platform authority.

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
compose=(docker compose -f "${repo_root}/docker-compose.yml")
"${repo_root}/scripts/smoke.sh"

tokens="${repo_root}/.local/identity/tokens.json"
search_token=$(jq -r '.search' "${tokens}")
reporting_token=$(jq -r '.reporting' "${tokens}")
agent_token=$(jq -r '.delegated_agent' "${tokens}")
work_dir=$(mktemp -d)
trap 'rm -rf "${work_dir}"' EXIT
key="golden-path-$(uuidgen | tr '[:upper:]' '[:lower:]')"

created=$(curl -fsS --max-time 10 -X POST http://localhost:8086/developer/v1/inference-integrations \
  -H "Authorization: Bearer ${search_token}" \
  -H "Idempotency-Key: ${key}" \
  -H 'content-type: application/json' \
  -d '{"service_name":"search-assistant","model":"chat-default","owner":"search-team","environment":"staging"}')
profile_id=$(jq -r '.profile.id' <<<"${created}")
jq -e '.idempotent_replay == false and .profile.tenant == "team-search" and .profile.model == "chat-default"' <<<"${created}" >/dev/null
jq -r '.files["inference_client.py"]' <<<"${created}" >"${work_dir}/inference_client.py"
jq -r '.files["inference-integration.yaml"]' <<<"${created}" >"${work_dir}/inference-integration.yaml"
! rg -q 'Bearer eyJ|tenant.*header|redis://' "${work_dir}"

# The generated artifact has no credential. The developer supplies a signed runtime
# token only at execution time; it performs real tenant-bound ONNX inference.
INFERENCE_API_TOKEN="${search_token}" "${repo_root}/.venv/bin/python" "${work_dir}/inference_client.py" \
  | jq -e '.x_backend == "onnx-stable-v1" or .x_backend == "onnx-candidate-v2"' >/dev/null

replay=$(curl -fsS --max-time 10 -X POST http://localhost:8086/developer/v1/inference-integrations \
  -H "Authorization: Bearer ${search_token}" \
  -H "Idempotency-Key: ${key}" \
  -H 'content-type: application/json' \
  -d '{"service_name":"search-assistant","model":"chat-default","owner":"search-team","environment":"staging"}')
jq -e --arg id "${profile_id}" '.idempotent_replay == true and .profile.id == $id' <<<"${replay}" >/dev/null

model_denial=$(curl -sS -o /tmp/self-service-model-denial.json -w '%{http_code}' --max-time 10 \
  -X POST http://localhost:8086/developer/v1/inference-integrations \
  -H "Authorization: Bearer ${search_token}" -H "Idempotency-Key: denied-model-${key}" \
  -H 'content-type: application/json' \
  -d '{"service_name":"search-unsafe","model":"chat-cpu-fallback-demo","owner":"search-team"}')
test "${model_denial}" = 403

cross_tenant=$(curl -sS -o /tmp/self-service-cross-tenant.json -w '%{http_code}' --max-time 10 \
  "http://localhost:8086/developer/v1/inference-integrations/${profile_id}" \
  -H "Authorization: Bearer ${reporting_token}")
test "${cross_tenant}" = 403

agent_denial=$(curl -sS -o /tmp/self-service-agent-denial.json -w '%{http_code}' --max-time 10 \
  -X POST http://localhost:8086/developer/v1/inference-integrations \
  -H "Authorization: Bearer ${agent_token}" -H "Idempotency-Key: agent-${key}" \
  -H 'content-type: application/json' \
  -d '{"service_name":"agent-attempt","model":"chat-default","owner":"search-team"}')
test "${agent_denial}" = 403

# Prometheus counters are process-local. Prove the created-profile metric before the
# persistence restart below intentionally resets the process metrics.
for _ in $(seq 1 30); do
  if curl -sS --max-time 5 --data-urlencode \
    'query=sum(inference_gateway_developer_integration_profiles_total{outcome="CREATED"})' \
    http://localhost:9090/api/v1/query \
    | jq -e '.data.result[0]?.value[1] | tonumber? > 0' >/dev/null; then
    break
  fi
  sleep 2
done
curl -sS --max-time 5 --data-urlencode \
  'query=sum(inference_gateway_developer_integration_profiles_total{outcome="CREATED"})' \
  http://localhost:9090/api/v1/query \
  | jq -e '.data.result[0]?.value[1] | tonumber? > 0' >/dev/null

# Profile persistence is a contract: restart the service, then retrieve exactly the
# same tenant-bound profile and generated artifacts.
"${compose[@]}" restart developer-self-service >/dev/null
for _ in $(seq 1 30); do
  if curl -fsS --max-time 3 http://localhost:8086/healthz >/dev/null 2>&1; then break; fi
  sleep 1
done
restored=$(curl -fsS --max-time 10 "http://localhost:8086/developer/v1/inference-integrations/${profile_id}" \
  -H "Authorization: Bearer ${search_token}")
jq -e --arg id "${profile_id}" '.profile.id == $id and (.files["inference_client.py"] | contains("INFERENCE_API_TOKEN"))' <<<"${restored}" >/dev/null

echo "Developer self-service demo passed: profile ${profile_id}; generated token-free client reached real ONNX inference; idempotency, model policy, tenant isolation, agent denial, durable restart, and Prometheus evidence were verified."
