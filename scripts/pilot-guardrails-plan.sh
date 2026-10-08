#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$root/scripts/pilot-cloud-guard.sh"

"$root/scripts/terraform-readonly-plan.sh" "$root/infrastructure/terraform/bootstrap" \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" "$@"
