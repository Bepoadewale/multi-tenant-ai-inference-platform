#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gpu-ec2-bootstrap-common.sh"
bootstrap_common_init
[[ "${GPU_EC2_BOOTSTRAP_CONFIRM:-}" == "apply" ]] || {
  echo "refusing apply: set GPU_EC2_BOOTSTRAP_CONFIRM=apply after reviewing the exact saved plan" >&2
  exit 1
}
: "${GPU_EC2_BOOTSTRAP_PLAN_SHA256:?set the reviewed bootstrap plan SHA-256}"
[[ -d "$GPU_BOOTSTRAP_WORKDIR" && -f "$GPU_BOOTSTRAP_PLAN_FILE" ]] || {
  echo "refusing apply: bootstrap workspace or saved plan is missing" >&2
  exit 1
}
actual_digest="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$GPU_BOOTSTRAP_PLAN_FILE")"
[[ "$actual_digest" == "$GPU_EC2_BOOTSTRAP_PLAN_SHA256" ]] || {
  echo "refusing apply: saved plan SHA-256 does not match the reviewed digest" >&2
  exit 1
}
bootstrap_verify_account
bootstrap_assert_resources_absent
bootstrap_assert_local_state_empty
terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" show -json "$GPU_BOOTSTRAP_PLAN_FILE" |
  EXPECTED_AWS_ACCOUNT_ID="$EXPECTED_AWS_ACCOUNT_ID" \
    python3 "$GPU_BOOTSTRAP_REPO_ROOT/scripts/gpu_ec2_bootstrap_plan_summary.py"

apply_log="$GPU_BOOTSTRAP_WORKDIR/apply.log"
if ! terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" apply -input=false "$GPU_BOOTSTRAP_PLAN_FILE" >"$apply_log" 2>&1; then
  echo "bootstrap apply failed or had an uncertain outcome; do not retry. Reconcile AWS resources and inspect the private log at $apply_log" >&2
  exit 1
fi
bootstrap_verify_local_state
echo "Bootstrap apply completed. Its local state remains private at $GPU_BOOTSTRAP_WORKDIR."
echo "Migrate that state to the encrypted S3 backend before planning the GPU root."
echo "Apply log: $apply_log"
