#!/usr/bin/env bash
set -euo pipefail

: "${CLUSTER_NAME:?set CLUSTER_NAME from Terraform output}"
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$root/scripts/pilot-cloud-guard.sh"
command -v kubectl >/dev/null || { echo "kubectl is required" >&2; exit 1; }

aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION"
kubectl -n platform rollout status deployment/inference-gateway --timeout=5m
kubectl -n platform get pods,svc,pdb
echo "Smoke requires separately recorded tenant, release, policy-denial, and failure evidence."
