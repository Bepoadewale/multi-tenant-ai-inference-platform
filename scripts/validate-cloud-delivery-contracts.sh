#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

command -v helm >/dev/null || { echo "helm is required" >&2; exit 1; }

helm lint platform/helm/inference-platform
rendered="$(mktemp)"
trap 'rm -f "$rendered"' EXIT
helm template multi-tenant-ai-platform platform/helm/inference-platform >"$rendered"

grep -q 'kind: PodDisruptionBudget' "$rendered" || {
  echo "expected gateway PodDisruptionBudget was not rendered" >&2
  exit 1
}
grep -q 'automountServiceAccountToken: false' "$rendered" || {
  echo "expected service-account token hardening was not rendered" >&2
  exit 1
}
grep -q 'kind: Application' platform/gitops/inference-platform-application.yaml || {
  echo "expected Argo CD Application contract is missing" >&2
  exit 1
}

echo "Cloud delivery contracts validate. No cluster or AWS resource was contacted."
