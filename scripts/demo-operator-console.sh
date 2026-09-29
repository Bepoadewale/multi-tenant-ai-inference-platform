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

plan=$(curl -fsS -X POST 'http://localhost:8091/console/v1/releases/create?canary_weight=10')
plan_id=$(jq -r '.id' <<<"$plan")
curl -fsS -X POST "http://localhost:8091/console/v1/releases/approve?plan_id=${plan_id}" | jq -e '.status == "APPROVED"' >/dev/null
curl -fsS -X POST "http://localhost:8091/console/v1/releases/canary?plan_id=${plan_id}" | jq -e '.status == "CANARY"' >/dev/null
curl -fsS -X POST "http://localhost:8091/console/v1/releases/rollback?plan_id=${plan_id}" | jq -e '.status == "ROLLED_BACK"' >/dev/null

task=$(curl -fsS -X POST http://localhost:8091/console/v1/sandbox/fixture_patch)
jq -e '.task.state == "DESTROYED" and .task.hardening.network_mode == "none"' <<<"$task" >/dev/null

echo 'Operator-console demo passed: one browser control surface retrieved real cross-slice evidence, drove independently scoped release transitions, and ran a fixed hardened sandbox task.'
