#!/usr/bin/env bash
set -euo pipefail
command -v kind >/dev/null || { echo 'install kind first'; exit 1; }
kind get clusters | grep -qx inference-platform-local || kind create cluster --name inference-platform-local
helm upgrade --install inference-platform platform/helm/inference-platform --namespace inference --create-namespace --set image.repository=nginx --set image.tag=1.27-alpine
kubectl get pods -n inference
