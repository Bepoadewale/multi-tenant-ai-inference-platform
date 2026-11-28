#!/usr/bin/env bash
set -euo pipefail

: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID to the approved 12-digit AWS account}"
export AWS_PROFILE="${AWS_PROFILE:-ai-platform-pilot-key}"
export AWS_REGION="${AWS_REGION:-us-east-1}"
[[ "$AWS_REGION" == "us-east-1" ]] || { echo "refusing: initial region must be us-east-1" >&2; exit 1; }

account_id="$(aws sts get-caller-identity --query Account --output text)"
[[ "$account_id" == "$EXPECTED_AWS_ACCOUNT_ID" ]] || {
  echo "refusing: authenticated account does not match EXPECTED_AWS_ACCOUNT_ID" >&2
  exit 1
}

project="multi-tenant-ai-inference-platform"
environment="gpu-ec2"
failures=0
check_empty() {
  local label="$1"
  shift
  local found
  found="$("$@")"
  if [[ -n "$found" && "$found" != "None" ]]; then
    printf 'REMAINS: %s\n' "$label"
    failures=1
  else
    printf 'absent: %s\n' "$label"
  fi
}

check_empty "non-terminated project instances" aws ec2 describe-instances \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'Reservations[].Instances[?State.Name != `terminated`].InstanceId[]' --output text
check_empty "tagged EBS volumes" aws ec2 describe-volumes \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'Volumes[].VolumeId' --output text
check_empty "tagged VPCs" aws ec2 describe-vpcs \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'Vpcs[].VpcId' --output text
check_empty "tagged subnets" aws ec2 describe-subnets \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'Subnets[].SubnetId' --output text
check_empty "tagged route tables" aws ec2 describe-route-tables \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'RouteTables[].RouteTableId' --output text
check_empty "tagged security groups" aws ec2 describe-security-groups \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'SecurityGroups[].GroupId' --output text
check_empty "tagged internet gateways" aws ec2 describe-internet-gateways \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'InternetGateways[].InternetGatewayId' --output text
check_empty "tagged NAT gateways" aws ec2 describe-nat-gateways \
  --filter "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'NatGateways[?State != `deleted`].NatGatewayId' --output text
check_empty "tagged network interfaces" aws ec2 describe-network-interfaces \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'NetworkInterfaces[].NetworkInterfaceId' --output text
check_empty "tagged elastic IP addresses" aws ec2 describe-addresses \
  --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'Addresses[].AllocationId' --output text
check_empty "tagged EBS snapshots" aws ec2 describe-snapshots \
  --owner-ids self --filters "Name=tag:project,Values=${project}" "Name=tag:environment,Values=${environment}" \
  --query 'Snapshots[].SnapshotId' --output text

role="${project}-gpu-ec2-expiry"
role_found="$(aws iam list-roles --query "length(Roles[?RoleName=='${role}'])" --output text)"
if [[ "$role_found" == "0" ]]; then
  echo "absent: project expiry role"
else
  echo "REMAINS: project expiry role"
  failures=1
fi

role="${project}-gpu-ec2-ssm"
role_found="$(aws iam list-roles --query "length(Roles[?RoleName=='${role}'])" --output text)"
if [[ "$role_found" == "0" ]]; then
  echo "absent: project instance role"
else
  echo "REMAINS: project instance role"
  failures=1
fi

profile="${project}-gpu-ec2"
profile_found="$(aws iam list-instance-profiles --query "length(InstanceProfiles[?InstanceProfileName=='${profile}'])" --output text)"
if [[ "$profile_found" == "0" ]]; then
  echo "absent: project instance profile"
else
  echo "REMAINS: project instance profile"
  failures=1
fi

schedule_group="${project}-gpu-ec2"
schedule_found="$(aws scheduler list-schedule-groups --name-prefix "$schedule_group" \
  --query "length(ScheduleGroups[?Name=='${schedule_group}'])" --output text)"
if [[ "$schedule_found" == "0" ]]; then
  echo "absent: project expiry schedule group"
  echo "absent: project one-time expiry schedule (schedule group is absent)"
else
  echo "REMAINS: project expiry schedule group"
  failures=1
  schedule="$(aws scheduler list-schedules --group-name "$schedule_group" \
    --query 'Schedules[].Name' --output text)"
  if [[ -z "$schedule" || "$schedule" == "None" ]]; then
    echo "absent: project one-time expiry schedule"
  else
    echo "REMAINS: project one-time expiry schedule"
    failures=1
  fi
fi

if [[ "$failures" -ne 0 ]]; then
  echo "Project GPU resources remain. Inspect them; this verifier never deletes resources." >&2
  exit 1
fi
echo "All queried GPU-environment resources are absent. Shared state, locks, and budget guardrails are outside this verifier's scope; it neither checks nor modifies them."
