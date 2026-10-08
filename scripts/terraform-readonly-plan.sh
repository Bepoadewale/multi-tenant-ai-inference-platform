#!/usr/bin/env bash
set -euo pipefail

configuration="${1:?pass a Terraform configuration directory}"
shift

[[ -d "$configuration" ]] || { echo "Terraform configuration not found: $configuration" >&2; exit 1; }

# The repository deliberately declares an S3 backend for apply/destroy. Before the
# bootstrap bucket exists, a safe plan still needs real provider reads but must not
# create state or alter the checked-in configuration. Plan from an ephemeral copy
# with the backend declaration removed, then delete that copy on exit.
workdir="$(mktemp -d "${TMPDIR:-/tmp}/multi-tenant-ai-platform-plan.XXXXXX")"
trap 'rm -rf "$workdir"' EXIT
cp -R "$configuration/." "$workdir/"
rm -rf "$workdir/.terraform"
perl -0pi -e 's/\n[ \t]*backend[ \t]+"s3"[ \t]*\{[ \t]*\}[ \t]*\n/\n/g' "$workdir/versions.tf"

if grep -q 'backend "s3"' "$workdir/versions.tf"; then
  echo "refusing read-only plan: unable to remove the temporary S3 backend declaration" >&2
  exit 1
fi

terraform -chdir="$workdir" init -backend=false -input=false
terraform -chdir="$workdir" plan -input=false -lock=false "$@"
