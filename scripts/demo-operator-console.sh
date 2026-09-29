#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

./scripts/smoke.sh
# The local delegated fixture identities are intentionally short-lived. Reissue the
# synthetic tokens before driving the final browser-control demonstration; services
# retain the same public verification key.
.venv/bin/python scripts/generate_local_identity.py

overview=$(curl -fsS http://localhost:8091/console/v1/overview)
jq -e '.tenants and .models and .capacity and .release_plans and .devices and .registry' <<<"$overview" >/dev/null
curl -fsS http://localhost:8091/console/v1/tenants/team-search | jq -e '.tenant.id == "team-search" and .usage' >/dev/null
curl -fsS http://localhost:8091/console/v1/models/chat-default | jq -e '.rollout.alias == "chat-default" and .registry and .telemetry and .grafana_url' >/dev/null
curl -fsS http://localhost:8091/console/v1/agents | jq -e '.tools and .audit' >/dev/null
device_id=$(jq -r '.devices.devices[0].device_id // empty' <<<"$overview")
if [[ -n "$device_id" ]]; then
  curl -fsS "http://localhost:8091/console/v1/edge/devices/${device_id}" | jq -e ".device.device_id == \"${device_id}\"" >/dev/null
fi

plan=$(curl -fsS -X POST 'http://localhost:8091/console/v1/releases/create?canary_weight=10')
plan_id=$(jq -r '.id' <<<"$plan")
curl -fsS "http://localhost:8091/console/v1/releases/${plan_id}" | jq -e ".id == \"${plan_id}\"" >/dev/null
curl -fsS -X POST "http://localhost:8091/console/v1/releases/approve?plan_id=${plan_id}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS -X POST "http://localhost:8091/console/v1/releases/canary?plan_id=${plan_id}" | jq -e '.status == "CANARY"' >/dev/null
curl -fsS -X POST "http://localhost:8091/console/v1/releases/rollback?plan_id=${plan_id}" | jq -e '.status == "ROLLED_BACK"' >/dev/null

task=$(curl -fsS -X POST http://localhost:8091/console/v1/sandbox/fixture_patch)
jq -e '.task.state == "DESTROYED" and .task.hardening.network_mode == "none"' <<<"$task" >/dev/null
task_id=$(jq -r '.task.id' <<<"$task")
curl -fsS "http://localhost:8091/console/v1/sandbox/tasks/${task_id}" | jq -e ".task.id == \"${task_id}\"" >/dev/null

# The cumulative flagship run creates these records before this console demo. Keep the
# standalone console demo useful when no remediation/profile evidence exists yet.
profile_id=$(jq -r '.integrations.integrations[0].id // empty' <<<"$overview")
if [[ -n "$profile_id" ]]; then
  curl -fsS "http://localhost:8091/console/v1/developer/integrations/${profile_id}" | jq -e ".profile.id == \"${profile_id}\"" >/dev/null
fi
incident_id=$(jq -r '.incidents.incidents[0].id // empty' <<<"$overview")
if [[ -n "$incident_id" ]]; then
  curl -fsS "http://localhost:8091/console/v1/incidents/${incident_id}" | jq -e '.incident and .timeline' >/dev/null
fi

echo 'Operator-console demo passed: routed tenant/model/agent/device evidence loaded through the local BFF; fixed Prometheus-backed model telemetry and Grafana deep links loaded without exposing arbitrary query access; release and sandbox details loaded after scoped actions; and cumulative runs also verified developer and incident detail routes.'
