#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"
./scripts/smoke.sh

# Restarting only the two project edge agents exercises registration/heartbeat rather
# than depending on counters created during an earlier bootstrap.
docker compose restart edge-device-search edge-device-constrained >/dev/null
for port in 8088 8089; do
  for _ in $(seq 1 30); do
    if curl -fsS "http://localhost:${port}/healthz" >/dev/null 2>&1; then break; fi
    sleep 1
  done
done

search_token=$(jq -r '.search' .local/identity/tokens.json)
request='{"request":{"model":"chat-default","messages":[{"role":"user","content":"safe local edge request"}],"max_tokens":4},"data_classification":"public","routing_profile":"LOCAL_PREFERRED"}'

devices=$(curl -fsS http://localhost:8087/edge/v1/devices)
echo "$devices" | jq -e '
  .hardware == "SIMULATED" and
  ([.devices[].device_id] | sort) == ["edge-constrained-001", "edge-search-001"] and
  (.devices[] | select(.device_id == "edge-search-001") | .local_models == ["chat-default"]) and
  (.devices[] | select(.device_id == "edge-constrained-001") | .local_models == [])
' >/dev/null

local_result=$(curl -fsS http://localhost:8088/edge/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'Content-Type: application/json' -d "$request")
echo "$local_result" | jq -e '.edge.route == "LOCAL" and .edge.execution_provider == "CPUExecutionProvider" and (.choices[0].message.content | startswith("classification="))' >/dev/null

cloud_result=$(curl -fsS http://localhost:8089/edge/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'Content-Type: application/json' -d "$request")
echo "$cloud_result" | jq -e '.edge.route == "CLOUD" and .edge.reason == "local_model_unavailable" and (.choices[0].message.content | startswith("classification="))' >/dev/null

restricted='{"request":{"model":"chat-default","messages":[{"role":"user","content":"restricted record"}],"max_tokens":4},"data_classification":"restricted","routing_profile":"LOCAL_PREFERRED"}'
status=$(curl -sS -o /tmp/edge-privacy-denial.json -w '%{http_code}' http://localhost:8089/edge/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'Content-Type: application/json' -d "$restricted")
test "$status" = 403
jq -e '.detail == "cloud fallback denied by privacy policy or offline state"' /tmp/edge-privacy-denial.json >/dev/null
rm -f /tmp/edge-privacy-denial.json

local_only='{"request":{"model":"chat-default","messages":[{"role":"user","content":"restricted record"}],"max_tokens":4},"data_classification":"public","routing_profile":"LOCAL_ONLY"}'
status=$(curl -sS -o /tmp/edge-local-only-denial.json -w '%{http_code}' http://localhost:8089/edge/v1/chat/completions \
  -H "Authorization: Bearer ${search_token}" -H 'Content-Type: application/json' -d "$local_only")
test "$status" = 403
rm -f /tmp/edge-local-only-denial.json

# Evidence is checked before the intentional restart because Prometheus counters are
# process-local in this lightweight adapter; durable device state is the recovery proof.
curl -fsS http://localhost:8087/metrics | awk '
  /inference_gateway_edge_device_registrations_total\{tenant="team-search"\}/ { if ($2 >= 2) found=1 }
  END { exit(found ? 0 : 1) }
'

# The registry is durable: a control-plane restart does not require agents to recreate devices.
docker compose restart edge-control >/dev/null
for _ in $(seq 1 30); do
  if curl -fsS http://localhost:8087/healthz >/dev/null 2>&1; then break; fi
  sleep 1
done
curl -fsS http://localhost:8087/edge/v1/devices | jq -e '.devices | length == 2' >/dev/null

echo 'Edge adapter demo passed: two independent simulated device agents registered durably; compatible public traffic ran real local CPU ONNX; constrained public traffic used the central gateway; restricted and LOCAL_ONLY traffic without a local model were denied without fallback; registry survived control restart.'
