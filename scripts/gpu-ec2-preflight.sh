#!/usr/bin/env bash
set -euo pipefail

: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID to the approved 12-digit AWS account}"
: "${GPU_EC2_AZ:?set GPU_EC2_AZ to an offered us-east-1 availability zone}"
: "${GPU_EC2_EXPIRES_AT:?set GPU_EC2_EXPIRES_AT to the exact approved UTC expiry}"

export AWS_PROFILE="${AWS_PROFILE:-ai-platform-pilot-key}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
project="multi-tenant-ai-inference-platform"
instance_type="${GPU_EC2_INSTANCE_TYPE:-g6.xlarge}"

[[ "$AWS_REGION" == "us-east-1" ]] || { echo "refusing: initial region must be us-east-1" >&2; exit 1; }
[[ "$GPU_EC2_AZ" =~ ^us-east-1[a-z]$ ]] || { echo "refusing: GPU_EC2_AZ must be an us-east-1 zone name" >&2; exit 1; }
[[ "$EXPECTED_AWS_ACCOUNT_ID" =~ ^[0-9]{12}$ ]] || { echo "refusing: expected account ID must be 12 digits" >&2; exit 1; }
[[ "$GPU_EC2_EXPIRES_AT" =~ ^20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$ ]] || {
  echo "refusing: expiry must be an exact UTC timestamp ending in Z" >&2
  exit 1
}
python3 - "$GPU_EC2_EXPIRES_AT" <<'PY'
from datetime import datetime, timezone
import sys

expiry = datetime.fromisoformat(sys.argv[1].replace("Z", "+00:00"))
remaining = (expiry - datetime.now(timezone.utc)).total_seconds()
if not 0 < remaining <= 12 * 60 * 60:
    raise SystemExit("refusing: exact expiry must be in the future and no more than 12 hours away")
PY
case "$instance_type" in
  g6.xlarge) required_vcpus=4 ;;
  *) echo "refusing: this first infrastructure package permits only one g6.xlarge" >&2; exit 1 ;;
esac

account_id="$(aws sts get-caller-identity --query Account --output text)"
[[ "$account_id" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || {
  echo "refusing: authenticated account does not match EXPECTED_AWS_ACCOUNT_ID" >&2
  exit 1
}

quota="$(aws service-quotas get-service-quota \
  --service-code ec2 --quota-code L-DB2E81BA \
  --query 'Quota.Value' --output text)"
awk -v have="$quota" -v need="$required_vcpus" 'BEGIN { if (have + 0 < need + 0) exit 1 }' || {
  echo "refusing: On-Demand G/VT quota is ${quota} vCPUs; ${required_vcpus} are required" >&2
  exit 1
}

offering="$(aws ec2 describe-instance-type-offerings \
  --location-type availability-zone \
  --filters "Name=instance-type,Values=${instance_type}" "Name=location,Values=${GPU_EC2_AZ}" \
  --query 'InstanceTypeOfferings[0].InstanceType' --output text)"
[[ "$offering" == "$instance_type" ]] || {
  echo "refusing: ${instance_type} is not listed in ${GPU_EC2_AZ}" >&2
  exit 1
}

existing="$(aws ec2 describe-instances \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=gpu-ec2" \
  --query 'Reservations[].Instances[?State.Name != `terminated`].InstanceId[]' --output text)"
[[ -z "$existing" || "$existing" == "None" ]] || {
  echo "refusing: a non-terminated project GPU instance already exists; inspect it before any operation" >&2
  exit 1
}

bucket="${project}-tfstate-${EXPECTED_AWS_ACCOUNT_ID}"
table="${project}-pilot-terraform-locks"
aws s3api head-bucket --bucket "$bucket" >/dev/null
aws dynamodb describe-table --table-name "$table" --query 'Table.TableStatus' --output text >/dev/null
budget="${project}-pilot-monthly-cost"
budget_count="$(aws budgets describe-budgets --account-id "$EXPECTED_AWS_ACCOUNT_ID" \
  --query "length(Budgets[?BudgetName=='${budget}'])" --output text)"
[[ "$budget_count" == "1" ]] || {
  echo "refusing: the repository budget guardrail is not present; bootstrap it through its reviewed Terraform root" >&2
  exit 1
}

echo "Read-only preflight passed for the expected account, region, quota, type offering, and repository guardrails."
echo "No quota request or cloud mutation was made. Instance capacity is not reserved by this check."
