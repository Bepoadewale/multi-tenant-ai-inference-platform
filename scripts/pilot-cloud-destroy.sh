#!/usr/bin/env bash
set -euo pipefail

[[ "${PILOT_CLOUD_CONFIRM:-}" == "destroy" ]] || {
  echo "refusing destroy: set PILOT_CLOUD_CONFIRM=destroy after reviewing the destroy plan" >&2
  exit 1
}

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$root/.local"
source "$root/scripts/pilot-cloud-guard.sh"

terraform -chdir="$root/infrastructure/terraform/environments/aws" init \
  -backend-config="bucket=${PILOT_STATE_BUCKET}" \
  -backend-config="key=pilot/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${PILOT_LOCK_TABLE}" \
  -backend-config="encrypt=true"
terraform -chdir="$root/infrastructure/terraform/environments/aws" plan -destroy \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" \
  -out="$root/.local/pilot-cloud-destroy.tfplan"
terraform -chdir="$root/infrastructure/terraform/environments/aws" apply "$root/.local/pilot-cloud-destroy.tfplan"
