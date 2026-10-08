#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$root/scripts/pilot-cloud-guard.sh"

terraform -chdir="$root/infrastructure/terraform/environments/aws" init \
  -backend-config="bucket=${PILOT_STATE_BUCKET}" \
  -backend-config="key=pilot/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${PILOT_LOCK_TABLE}" \
  -backend-config="encrypt=true"
terraform -chdir="$root/infrastructure/terraform/environments/aws" plan \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" \
  "$@"
