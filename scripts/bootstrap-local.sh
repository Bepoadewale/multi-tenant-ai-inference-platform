#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
command -v docker >/dev/null || { echo 'Docker Desktop is required.' >&2; exit 1; }
docker info >/dev/null 2>&1 || { echo 'Docker Desktop is not running.' >&2; exit 1; }
mkdir -p "${repo_root}/.local/mlflow" "${repo_root}/.local/release" "${repo_root}/.local/remediation" "${repo_root}/.local/agent-tools" "${repo_root}/.local/self-service" "${repo_root}/.local/edge" "${repo_root}/.local/sandbox"
lock_dir="${repo_root}/.local/.lifecycle-lock"
if ! mkdir "${lock_dir}" 2>/dev/null; then
  echo 'Another project lifecycle command is already running; wait for it to finish.' >&2
  exit 1
fi
trap 'rmdir "${lock_dir}" 2>/dev/null || true' EXIT
"${repo_root}/.venv/bin/python" "${repo_root}/scripts/generate_local_identity.py"
export LOCAL_UID="$(id -u)"
export LOCAL_GID="$(id -g)"
dead_ids=$(docker ps -aq --filter "label=com.docker.compose.project=multi-tenant-ai-inference-platform" --filter status=dead)
if [[ -n "${dead_ids}" ]]; then
  echo 'Docker Desktop has stale dead records for this project. Restart Docker Desktop; if they remain, use its Troubleshoot cleanup before bootstrapping.' >&2
  exit 1
fi
# Refresh only this project's services so mounted dependency configuration (for example
# new Prometheus scrape targets) cannot be silently inherited from an older local stack.
# A project-scoped down avoids Compose's parallel --force-recreate name collision.
# Remove only images built for this Compose project before a fresh build. This avoids
# Docker Desktop/BuildKit retaining a conflicting partial image after an interrupted
# bootstrap; base images and any unrelated local workloads are untouched.
if ! docker compose -f "${repo_root}/docker-compose.yml" down --remove-orphans --rmi local >/dev/null; then
  echo 'Warning: Compose reported stale project state during shutdown; continuing with scoped cleanup.' >&2
fi
docker network rm multi-tenant-ai-inference-platform_default >/dev/null 2>&1 || true
docker build --label com.bepoadewale.project=multi-tenant-ai-inference-platform \
  -t inference-agent-sandbox:local -f "${repo_root}/sandbox/Dockerfile" "${repo_root}"
docker compose -f "${repo_root}/docker-compose.yml" up --build --wait --wait-timeout 240
# Local delegated tokens are deliberately short-lived. Reissue them after a potentially
# long first image build so every demo begins with usable signed identities. The public
# key is retained, so already-started services do not need a key reload.
"${repo_root}/.venv/bin/python" "${repo_root}/scripts/generate_local_identity.py"
MLFLOW_TRACKING_URI=http://localhost:15010 "${repo_root}/.venv/bin/python" "${repo_root}/scripts/register_mlflow_models.py"
