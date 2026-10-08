#!/usr/bin/env bash
set -euo pipefail

[[ "${PILOT_CLOUD_CONFIRM:-}" == "apply" ]] || {
  echo "refusing apply: set PILOT_CLOUD_CONFIRM=apply after reviewing a plan" >&2
  exit 1
}

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$root/.local"
source "$root/scripts/pilot-cloud-guard.sh"
aws s3api head-bucket --bucket "$PILOT_STATE_BUCKET" >/dev/null 2>&1 || {
  echo "refusing apply: bootstrap and migrate the dedicated state bucket first" >&2
  exit 1
}
"$root/scripts/pilot-cloud-plan.sh" -out="$root/.local/pilot-cloud.tfplan"
terraform -chdir="$root/infrastructure/terraform/environments/aws" apply "$root/.local/pilot-cloud.tfplan"
