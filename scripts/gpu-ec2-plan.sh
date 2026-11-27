#!/usr/bin/env bash
set -euo pipefail

: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID}"
: "${GPU_EC2_AZ:?set GPU_EC2_AZ to an offered us-east-1 zone}"
: "${GPU_EC2_EXPIRES_AT:?set the exact approved UTC expiry, no more than 12 hours away}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export GPU_EC2_INSTANCE_TYPE="g6.xlarge"
"$root/scripts/gpu-ec2-preflight.sh"

state_bucket="multi-tenant-ai-inference-platform-tfstate-${EXPECTED_AWS_ACCOUNT_ID}"
lock_table="multi-tenant-ai-inference-platform-pilot-terraform-locks"
state_key="gpu-ec2/us-east-1/terraform.tfstate"
terraform_root="$root/infrastructure/terraform/environments/gpu-ec2"
plan_file="${GPU_EC2_PLAN_FILE:-$root/.local/gpu-ec2.tfplan}"
plan_file="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$plan_file")"
mkdir -p "$(dirname "$plan_file")"

terraform -chdir="$terraform_root" init -reconfigure -input=false \
  -backend-config="bucket=${state_bucket}" \
  -backend-config="key=${state_key}" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${lock_table}" \
  -backend-config="encrypt=true" \
  -backend-config="use_lockfile=true"

terraform -chdir="$terraform_root" plan -input=false \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" \
  -var="availability_zone=${GPU_EC2_AZ}" \
  -var="instance_type=g6.xlarge" \
  -var="expires_at=${GPU_EC2_EXPIRES_AT}" \
  -out="$plan_file"

python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$plan_file"
echo "Review this exact plan and its cost/resource scope before any apply. The saved plan is local and must not be committed."
