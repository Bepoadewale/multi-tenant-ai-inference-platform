#!/usr/bin/env bash
set -euo pipefail

: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID}"
export AWS_PROFILE="${AWS_PROFILE:-ai-platform-pilot-key}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
[[ "$AWS_REGION" == "us-east-1" ]] || { echo "refusing: initial region must be us-east-1" >&2; exit 1; }
account_id="$(aws sts get-caller-identity --query Account --output text)"
[[ "$account_id" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || {
  echo "refusing: authenticated account does not match EXPECTED_AWS_ACCOUNT_ID" >&2
  exit 1
}

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
state_bucket="multi-tenant-ai-inference-platform-tfstate-${EXPECTED_AWS_ACCOUNT_ID}"
lock_table="multi-tenant-ai-inference-platform-pilot-terraform-locks"
terraform_root="$root/infrastructure/terraform/environments/gpu-ec2"
plan_file="${GPU_EC2_DESTROY_PLAN_FILE:-$root/.local/gpu-ec2-destroy.tfplan}"
plan_file="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$plan_file")"
mkdir -p "$(dirname "$plan_file")"
destroy_plan_expiry="$(python3 - <<'PY'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) + timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ"))
PY
)"

terraform -chdir="$terraform_root" init -reconfigure -input=false \
  -backend-config="bucket=${state_bucket}" \
  -backend-config="key=gpu-ec2/us-east-1/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${lock_table}" \
  -backend-config="encrypt=true" \
  -backend-config="use_lockfile=true"
terraform -chdir="$terraform_root" plan -destroy -input=false \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" \
  -var="availability_zone=${GPU_EC2_AZ:?set GPU_EC2_AZ from the deployment record}" \
  -var="expires_at=${destroy_plan_expiry}" \
  -out="$plan_file"
python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$plan_file"
echo "Destroy-only planning uses a temporary future expiry to satisfy input validation; the plan must show destroys only. This root must not destroy the shared repository state bucket, lock table, or budget."
