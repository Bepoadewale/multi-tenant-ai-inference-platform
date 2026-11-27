#!/usr/bin/env bash
set -euo pipefail

[[ "${GPU_EC2_CONFIRM:-}" == "destroy" ]] || {
  echo "refusing destroy: set GPU_EC2_CONFIRM=destroy after reviewing the exact destroy plan" >&2
  exit 1
}
: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID}"
: "${GPU_EC2_DESTROY_PLAN_SHA256:?set the reviewed destroy-plan SHA-256}"
export AWS_PROFILE="${AWS_PROFILE:-ai-platform-pilot-key}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
[[ "$AWS_REGION" == "us-east-1" ]] || { echo "refusing destroy: initial region must be us-east-1" >&2; exit 1; }
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
plan_file="${GPU_EC2_DESTROY_PLAN_FILE:-$root/.local/gpu-ec2-destroy.tfplan}"
plan_file="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$plan_file")"
[[ -f "$plan_file" ]] || { echo "refusing destroy: saved plan does not exist" >&2; exit 1; }
actual="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$plan_file")"
[[ "$actual" == "$GPU_EC2_DESTROY_PLAN_SHA256" ]] || {
  echo "refusing destroy: saved-plan checksum does not match the reviewed checksum" >&2
  exit 1
}
account_id="$(aws sts get-caller-identity --query Account --output text)"
[[ "$account_id" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || {
  echo "refusing destroy: authenticated account does not match EXPECTED_AWS_ACCOUNT_ID" >&2
  exit 1
}
terraform -chdir="$root/infrastructure/terraform/environments/gpu-ec2" apply -input=false "$plan_file"
