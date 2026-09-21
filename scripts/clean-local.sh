#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
docker compose -f "${repo_root}/docker-compose.yml" down --volumes --remove-orphans
rm -rf "${repo_root}/.venv" "${repo_root}/models"
echo 'Removed only multi-tenant-ai-inference-platform Compose resources and local generated artifacts.'
