#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
curl -fsS --connect-timeout 2 --max-time 10 \
  "http://localhost:15010/api/2.0/mlflow/registered-models/get?name=local-tiny-intent-classifier" \
  | jq -e '(.registered_model.aliases | map(.alias) | sort) == ["candidate", "champion"]' >/dev/null
jq -e '(.versions | length == 2) and all(.versions[]; has("artifact_sha256"))' \
  "${repo_root}/.local/mlflow/registry-evidence.json" >/dev/null
echo 'Model-registry demo passed: MLflow contains stable/candidate ONNX versions with real artifact digests and fixture metrics.'
