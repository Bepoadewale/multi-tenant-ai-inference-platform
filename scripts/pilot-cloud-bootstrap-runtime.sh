#!/usr/bin/env bash
set -euo pipefail

: "${PILOT_CLOUD_CONFIRM:?set PILOT_CLOUD_CONFIRM=bootstrap after reviewed Terraform apply}"
[[ "$PILOT_CLOUD_CONFIRM" == "bootstrap" ]] || { echo "refusing runtime bootstrap" >&2; exit 1; }
: "${CLUSTER_NAME:?set CLUSTER_NAME from Terraform output}"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$root/scripts/pilot-cloud-guard.sh"
command -v kubectl >/dev/null || { echo "kubectl is required" >&2; exit 1; }
command -v helm >/dev/null || { echo "helm is required" >&2; exit 1; }

# The EKS endpoint is private by design. Run from the approved private operator
# path (for example a temporary SSM-connected operator host), never by exposing it.
aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION"
kubectl get nodes
echo "Runtime bootstrap is intentionally incomplete until CP6 supplies immutable ECR and IRSA values."
echo "Apply only a reviewed GitOps PR; do not use this script to bypass desired-state review."
