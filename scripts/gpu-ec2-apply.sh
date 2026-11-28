#!/usr/bin/env bash
set -euo pipefail

[[ "${GPU_EC2_CONFIRM:-}" == "apply" ]] || {
  echo "refusing apply: set GPU_EC2_CONFIRM=apply only after reviewing the exact saved plan" >&2
  exit 1
}
: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID}"
: "${GPU_EC2_AZ:?set GPU_EC2_AZ}"
: "${GPU_EC2_UBUNTU_AMI_ID:?set the same reviewed Canonical Ubuntu AMI ID used to plan}"
: "${GPU_EC2_EXPIRES_AT:?set the exact UTC expiry}"
: "${GPU_EC2_PLAN_SHA256:?set the reviewed saved-plan SHA-256}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plan_file="${GPU_EC2_PLAN_FILE:-$root/.local/gpu-ec2.tfplan}"
plan_file="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$plan_file")"
[[ -f "$plan_file" ]] || { echo "refusing apply: saved plan does not exist" >&2; exit 1; }
actual="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$plan_file")"
[[ "$actual" == "$GPU_EC2_PLAN_SHA256" ]] || {
  echo "refusing apply: saved plan checksum does not match the reviewed checksum" >&2
  exit 1
}

export AWS_PROFILE="${AWS_PROFILE:-ai-platform-pilot-key}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
export GPU_EC2_INSTANCE_TYPE="g6.xlarge"
"$root/scripts/gpu-ec2-preflight.sh"
terraform_root="$root/infrastructure/terraform/environments/gpu-ec2"
terraform -chdir="$terraform_root" show -json "$plan_file" |
  GPU_EC2_UBUNTU_AMI_ID="$GPU_EC2_UBUNTU_AMI_ID" \
    GPU_EC2_AZ="$GPU_EC2_AZ" \
    GPU_EC2_EXPIRES_AT="$GPU_EC2_EXPIRES_AT" \
    python3 "$root/scripts/gpu_ec2_plan_summary.py"
terraform -chdir="$terraform_root" apply -input=false "$plan_file"
