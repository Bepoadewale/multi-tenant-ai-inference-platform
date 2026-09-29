#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

run_demo() {
  local target="$1"
  printf '\n=== flagship: %s ===\n' "$target"
  make "$target"
}

# The order makes the platform story observable: real tenant inference first, then
# policy failures, model lifecycle, evidence/remediation, constrained agent/device
# boundaries, and finally bounded sandbox execution. Every child demo has its own
# assertions; this orchestrator only establishes the reproducible cumulative route.
run_demo demo-local
run_demo demo-overload
run_demo demo-routing
run_demo demo-metering
run_demo demo-observability
run_demo demo-failure
run_demo demo-timeout
run_demo demo-recovery
run_demo demo-model-registry
run_demo demo-release-control
run_demo demo-capacity
run_demo demo-operational-evidence
run_demo demo-self-service
run_demo demo-agent-tools
run_demo demo-remediation
run_demo demo-edge-adapter
run_demo demo-sandboxed-agent

echo 'Flagship demo passed: authenticated tenant inference, shared admission and failure paths, model release/capacity/evidence/remediation, delegated tools, developer self-service, edge routing, and bounded sandboxed execution all completed against one local stack.'
