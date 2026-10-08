#!/usr/bin/env bash
set -euo pipefail

: "${IMAGE_TAG:?set IMAGE_TAG to an immutable build identifier}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$root/scripts/pilot-cloud-guard.sh"

repository="${ECR_REPOSITORY:?set ECR_REPOSITORY to the Terraform output repository URL}"
registry="${repository%%/*}"
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$registry"
docker build -t "${repository}:${IMAGE_TAG}" -f "$root/gateway/Dockerfile" "$root"
docker push "${repository}:${IMAGE_TAG}"
echo "Resolve and record the pushed image digest before changing desired state."
