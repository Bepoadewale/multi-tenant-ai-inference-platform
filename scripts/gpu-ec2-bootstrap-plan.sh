#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gpu-ec2-bootstrap-common.sh"
bootstrap_common_init
bootstrap_validate_budget_email
bootstrap_validate_budget_usd
bootstrap_verify_account
bootstrap_assert_resources_absent

terraform_root="$GPU_BOOTSTRAP_REPO_ROOT/infrastructure/terraform/bootstrap"
mkdir -p "$GPU_BOOTSTRAP_ARTIFACT_DIR"
chmod 700 "$GPU_BOOTSTRAP_ARTIFACT_DIR"
[[ ! -e "$GPU_BOOTSTRAP_WORKDIR" && ! -e "$GPU_BOOTSTRAP_PLAN_FILE" ]] || {
  echo "refusing: this bootstrap run ID already has files; inspect them and choose a new run ID" >&2
  exit 1
}
mkdir -m 700 "$GPU_BOOTSTRAP_WORKDIR"
while IFS= read -r -d '' file; do
  cp "$file" "$GPU_BOOTSTRAP_WORKDIR/"
done < <(find "$terraform_root" -maxdepth 1 -type f -name '*.tf' -print0)
[[ -f "$GPU_BOOTSTRAP_WORKDIR/main.tf" ]] || {
  echo "refusing: bootstrap Terraform source files were not copied" >&2
  exit 1
}

init_log="$GPU_BOOTSTRAP_WORKDIR/init.log"
plan_log="$GPU_BOOTSTRAP_WORKDIR/plan.log"
terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" init -backend=false -input=false >"$init_log" 2>&1 || {
  echo "bootstrap Terraform init failed; inspect the private log at $init_log" >&2
  exit 1
}
export TF_VAR_budget_alert_email="$GPU_EC2_BOOTSTRAP_BUDGET_EMAIL"
terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" plan -input=false \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" \
  -var="monthly_budget_usd=${GPU_BOOTSTRAP_BUDGET_USD}" \
  -out="$GPU_BOOTSTRAP_PLAN_FILE" >"$plan_log" 2>&1 || {
  echo "bootstrap plan failed; inspect the private log at $plan_log" >&2
  exit 1
}

terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" show -json "$GPU_BOOTSTRAP_PLAN_FILE" |
  EXPECTED_AWS_ACCOUNT_ID="$EXPECTED_AWS_ACCOUNT_ID" \
    python3 "$GPU_BOOTSTRAP_REPO_ROOT/scripts/gpu_ec2_bootstrap_plan_summary.py"
digest="$(python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$GPU_BOOTSTRAP_PLAN_FILE")"
echo "Run ID: $GPU_BOOTSTRAP_RUN_ID"
echo "Plan SHA-256: $digest"
echo "Saved plan: $GPU_BOOTSTRAP_PLAN_FILE"
echo "Private logs: $init_log and $plan_log"
echo "No apply occurred. Review this exact plan and confirm the private Budget recipient before authorizing apply."
