#!/usr/bin/env bash

bootstrap_common_init() {
  set -euo pipefail
  umask 077

  local scripts_dir
  scripts_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  GPU_BOOTSTRAP_REPO_ROOT="$(cd "$scripts_dir/.." && pwd)"
  export AWS_PROFILE="${AWS_PROFILE:-ai-platform-pilot-key}"
  export AWS_REGION="${AWS_REGION:-us-east-1}"
  GPU_BOOTSTRAP_PROJECT="multi-tenant-ai-inference-platform"
  GPU_BOOTSTRAP_PREFIX="${GPU_BOOTSTRAP_PROJECT}-pilot"

  : "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID to the reviewed account}"
  [[ "$EXPECTED_AWS_ACCOUNT_ID" =~ ^[0-9]{12}$ ]] || {
    echo "refusing: expected account ID must contain 12 digits" >&2
    return 1
  }
  [[ "$AWS_REGION" == "us-east-1" ]] || {
    echo "refusing: bootstrap is limited to us-east-1" >&2
    return 1
  }

  GPU_BOOTSTRAP_RUN_ID="${GPU_EC2_BOOTSTRAP_RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)}"
  [[ "$GPU_BOOTSTRAP_RUN_ID" =~ ^[0-9]{8}T[0-9]{6}Z$ ]] || {
    echo "refusing: GPU_EC2_BOOTSTRAP_RUN_ID must use YYYYMMDDTHHMMSSZ" >&2
    return 1
  }
  GPU_BOOTSTRAP_ARTIFACT_DIR="${GPU_EC2_BOOTSTRAP_ARTIFACT_DIR:-$GPU_BOOTSTRAP_REPO_ROOT/.local}"
  GPU_BOOTSTRAP_ARTIFACT_DIR="$(python3 -c 'import pathlib,sys; print(pathlib.Path(sys.argv[1]).resolve())' "$GPU_BOOTSTRAP_ARTIFACT_DIR")"
  GPU_BOOTSTRAP_WORKDIR="$GPU_BOOTSTRAP_ARTIFACT_DIR/gpu-ec2-bootstrap-${GPU_BOOTSTRAP_RUN_ID}"
  GPU_BOOTSTRAP_PLAN_FILE="$GPU_BOOTSTRAP_ARTIFACT_DIR/gpu-ec2-bootstrap-${GPU_BOOTSTRAP_RUN_ID}.tfplan"
  GPU_BOOTSTRAP_BUCKET="${GPU_BOOTSTRAP_PROJECT}-tfstate-${EXPECTED_AWS_ACCOUNT_ID}"
  GPU_BOOTSTRAP_TABLE="${GPU_BOOTSTRAP_PREFIX}-terraform-locks"
  GPU_BOOTSTRAP_BUDGET="${GPU_BOOTSTRAP_PREFIX}-monthly-cost"
}

bootstrap_validate_budget_email() {
  [[ -n "${GPU_EC2_BOOTSTRAP_BUDGET_EMAIL:-}" ]] || {
    echo "refusing: set GPU_EC2_BOOTSTRAP_BUDGET_EMAIL privately; do not commit it" >&2
    return 1
  }
  GPU_EC2_BOOTSTRAP_BUDGET_EMAIL="$GPU_EC2_BOOTSTRAP_BUDGET_EMAIL" python3 - <<'PY'
import os
import re

value = os.environ["GPU_EC2_BOOTSTRAP_BUDGET_EMAIL"]
if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value) or value.lower().endswith(".invalid"):
    raise SystemExit("refusing: Budget recipient must be a usable email address")
PY
}

bootstrap_validate_budget_usd() {
  GPU_BOOTSTRAP_BUDGET_USD="${GPU_BOOTSTRAP_BUDGET_USD:-${GPU_EC2_BOOTSTRAP_BUDGET_USD:-10}}"
  export GPU_BOOTSTRAP_BUDGET_USD
  GPU_BOOTSTRAP_BUDGET_USD="$GPU_BOOTSTRAP_BUDGET_USD" python3 - <<'PY'
import os

try:
    value = float(os.environ["GPU_BOOTSTRAP_BUDGET_USD"])
except ValueError as exc:
    raise SystemExit("refusing: Budget amount must be numeric") from exc
if not 0 < value <= 25:
    raise SystemExit("refusing: Budget alert amount must be greater than zero and at most USD 25")
PY
}

bootstrap_verify_account() {
  local actual
  actual="$(aws sts get-caller-identity --query Account --output text)"
  [[ "$actual" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || {
    echo "refusing: authenticated AWS account does not match EXPECTED_AWS_ACCOUNT_ID" >&2
    return 1
  }
}

bootstrap_assert_resources_absent() {
  local bucket_count table_output budget_count
  bucket_count="$(aws s3api list-buckets --query "length(Buckets[?Name=='${GPU_BOOTSTRAP_BUCKET}'])" --output text)" || {
    echo "refusing: cannot verify the project Terraform bucket inventory" >&2
    return 1
  }
  [[ "$bucket_count" == "0" ]] || {
    echo "refusing: the project Terraform bucket already exists; reconcile state before continuing" >&2
    return 1
  }

  if table_output="$(aws dynamodb describe-table --table-name "$GPU_BOOTSTRAP_TABLE" --region "$AWS_REGION" --query 'Table.TableStatus' --output text 2>&1)"; then
    echo "refusing: the project lock table already exists; reconcile state before continuing" >&2
    return 1
  elif [[ "$table_output" != *ResourceNotFoundException* ]]; then
    echo "refusing: cannot verify the project lock table inventory" >&2
    return 1
  fi

  budget_count="$(aws budgets describe-budgets --account-id "$EXPECTED_AWS_ACCOUNT_ID" --region "$AWS_REGION" --query "length(Budgets[?BudgetName=='${GPU_BOOTSTRAP_BUDGET}'])" --output text)" || {
    echo "refusing: cannot verify the project Budget inventory" >&2
    return 1
  }
  [[ "$budget_count" == "0" ]] || {
    echo "refusing: the project Budget already exists; reconcile state before continuing" >&2
    return 1
  }
}

bootstrap_verify_local_state() {
  local actual expected
  actual="$(terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" state list 2>"$GPU_BOOTSTRAP_WORKDIR/state-list.log")" || {
    echo "refusing: cannot read the private bootstrap state; inspect its local log" >&2
    return 1
  }
  expected="$(printf '%s\n' \
    'aws_budgets_budget.monthly_pilot' \
    'aws_dynamodb_table.terraform_locks' \
    'aws_s3_bucket.terraform_state' \
    'aws_s3_bucket_ownership_controls.terraform_state' \
    'aws_s3_bucket_public_access_block.terraform_state' \
    'aws_s3_bucket_server_side_encryption_configuration.terraform_state' \
    'aws_s3_bucket_versioning.terraform_state' | LC_ALL=C sort)"
  actual="$(printf '%s\n' "$actual" | LC_ALL=C sort)"
  [[ "$actual" == "$expected" ]] || {
    echo "refusing: bootstrap state does not contain exactly the expected seven resources" >&2
    return 1
  }
}

bootstrap_assert_local_state_empty() {
  [[ ! -e "$GPU_BOOTSTRAP_WORKDIR/terraform.tfstate" && ! -e "$GPU_BOOTSTRAP_WORKDIR/terraform.tfstate.backup" ]] || {
    echo "refusing apply: local Terraform state already exists; reconcile it before continuing" >&2
    return 1
  }
}
