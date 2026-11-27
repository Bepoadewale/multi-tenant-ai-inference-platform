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
preview_name="${GPU_EC2_PREVIEW_NAME:-gpu-ec2-bootstrap-preview}"
[[ "$preview_name" =~ ^[a-z0-9-]+$ ]] || { echo "refusing preview: GPU_EC2_PREVIEW_NAME must use lowercase letters, digits, and hyphens" >&2; exit 1; }
preview="$root/.local/${preview_name}"
plan_file="$root/.local/${preview_name}.tfplan"
[[ ! -e "$preview" && ! -e "$plan_file" ]] || {
  echo "refusing preview: ${preview} or ${plan_file} already exists; inspect it and choose a new path" >&2
  exit 1
}
mkdir -p "$preview"
python3 - "$root/infrastructure/terraform/bootstrap" "$preview" <<'PY'
from pathlib import Path
import re
import shutil
import sys

source, destination = map(Path, sys.argv[1:])
for item in source.iterdir():
    if item.is_file() and item.suffix in {".tf", ".hcl"}:
        target = destination / item.name
        shutil.copy2(item, target)
        if item.name == "versions.tf":
            content = target.read_text()
            content, count = re.subn(r'\n\s*backend\s+"s3"\s*\{\s*\}\s*\n', "\n", content)
            if count != 1:
                raise SystemExit("refusing preview: could not remove exactly one temporary S3 backend block")
            target.write_text(content)
PY

terraform -chdir="$preview" init -backend=false -input=false
terraform -chdir="$preview" plan -input=false \
  -var="expected_account_id=${EXPECTED_AWS_ACCOUNT_ID}" \
  -var='budget_alert_email=operator@example.invalid' \
  -out="$plan_file"
python3 -c 'import hashlib,pathlib,sys; print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())' "$plan_file"
echo "Preview only: this plan uses a placeholder alert address and local state; it is not suitable for apply. No quota request or cloud mutation was made."
