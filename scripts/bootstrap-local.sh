#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
command -v docker >/dev/null || { echo 'Docker Desktop is required.' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Docker Desktop is not running.' >&2; exit 1; }
mkdir -p "${repo_root}/.local/mlflow" "${repo_root}/.local/release" "${repo_root}/.local/remediation" "${repo_root}/.local/agent-tools"
"${repo_root}/.venv/bin/python" "${repo_root}/scripts/generate_local_identity.py"
export LOCAL_UID="$(id -u)"
export LOCAL_GID="$(id -g)"
docker compose -f "${repo_root}/docker-compose.yml" up --build --quiet-build --wait --wait-timeout 240
MLFLOW_TRACKING_URI=http://localhost:15010 "${repo_root}/.venv/bin/python" "${repo_root}/scripts/register_mlflow_models.py"
