#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/gpu-ec2-bootstrap-common.sh"
bootstrap_common_init
[[ "${GPU_EC2_BOOTSTRAP_CONFIRM:-}" == "migrate" ]] || {
  echo "refusing state migration: set GPU_EC2_BOOTSTRAP_CONFIRM=migrate after reviewing the backend settings" >&2
  exit 1
}
[[ -d "$GPU_BOOTSTRAP_WORKDIR" ]] || {
  echo "refusing state migration: private bootstrap workspace is missing" >&2
  exit 1
}
bootstrap_verify_account
bootstrap_verify_local_state

backend_metadata="$GPU_BOOTSTRAP_WORKDIR/.terraform/terraform.tfstate"
if [[ -f "$backend_metadata" ]] && python3 - "$backend_metadata" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as stream:
        data = json.load(stream)
except (OSError, json.JSONDecodeError):
    raise SystemExit(1)
raise SystemExit(0 if data.get("backend", {}).get("type") == "s3" else 1)
PY
then
  echo "refusing state migration: workspace already records an S3 backend; verify remote state before continuing" >&2
  exit 1
fi

bucket_encryption="$(aws s3api get-bucket-encryption --bucket "$GPU_BOOTSTRAP_BUCKET" --region "$AWS_REGION" --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text 2>/dev/null || true)"
bucket_versioning="$(aws s3api get-bucket-versioning --bucket "$GPU_BOOTSTRAP_BUCKET" --region "$AWS_REGION" --query 'Status' --output text 2>/dev/null || true)"
table_status="$(aws dynamodb describe-table --table-name "$GPU_BOOTSTRAP_TABLE" --region "$AWS_REGION" --query 'Table.TableStatus' --output text 2>/dev/null || true)"
[[ "$bucket_encryption" == "AES256" && "$bucket_versioning" == "Enabled" && "$table_status" == "ACTIVE" ]] || {
  echo "refusing state migration: remote backend is missing encryption, versioning, or an active lock table" >&2
  exit 1
}

key="bootstrap/us-east-1/terraform.tfstate"
migration_log="$GPU_BOOTSTRAP_WORKDIR/state-migration.log"
if ! terraform -chdir="$GPU_BOOTSTRAP_WORKDIR" init -migrate-state -force-copy -input=false \
  -backend-config="bucket=${GPU_BOOTSTRAP_BUCKET}" \
  -backend-config="key=${key}" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${GPU_BOOTSTRAP_TABLE}" \
  -backend-config="encrypt=true" \
  -backend-config="use_lockfile=true" >"$migration_log" 2>&1; then
  echo "state migration failed or had an uncertain outcome; inspect remote state and the private log before retrying: $migration_log" >&2
  exit 1
fi
bootstrap_verify_local_state
echo "Bootstrap state migration completed to the encrypted, versioned S3 backend."
echo "A private local state copy remains at $GPU_BOOTSTRAP_WORKDIR; do not commit it."
echo "Migration log: $migration_log"
