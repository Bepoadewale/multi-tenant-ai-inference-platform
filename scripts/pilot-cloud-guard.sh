#!/usr/bin/env bash
set -euo pipefail

command -v aws >/dev/null || { echo "aws CLI is required" >&2; exit 1; }
command -v terraform >/dev/null || { echo "terraform is required" >&2; exit 1; }

: "${EXPECTED_AWS_ACCOUNT_ID:?set EXPECTED_AWS_ACCOUNT_ID to the approved 12-digit account}"
: "${AWS_REGION:=us-east-1}"
export AWS_REGION

identity="$(aws sts get-caller-identity --query Account --output text)"
if [[ "$identity" != "$EXPECTED_AWS_ACCOUNT_ID" ]]; then
  echo "refusing pilot operation: authenticated account $identity is not expected account $EXPECTED_AWS_ACCOUNT_ID" >&2
  exit 1
fi

case "${EXPECTED_AWS_ACCOUNT_ID}" in
  [0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]) ;;
  *) echo "EXPECTED_AWS_ACCOUNT_ID must be 12 digits" >&2; exit 1 ;;
esac

export PILOT_STATE_BUCKET="multi-tenant-ai-inference-platform-tfstate-${EXPECTED_AWS_ACCOUNT_ID}"
export PILOT_LOCK_TABLE="multi-tenant-ai-inference-platform-pilot-terraform-locks"
