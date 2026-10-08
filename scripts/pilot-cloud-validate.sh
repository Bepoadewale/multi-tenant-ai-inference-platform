#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
"$root/scripts/pilot-cloud-plan.sh"
"$root/scripts/pilot-cloud-smoke.sh"
echo "Record CloudWatch/Prometheus, Tempo, Grafana, alert, rollback, and cost-query results in docs/governance/VALIDATION.md."
