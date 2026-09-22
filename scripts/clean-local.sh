#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
docker compose -f "${repo_root}/docker-compose.yml" down --volumes --remove-orphans
if [[ -n "$(docker compose -f "${repo_root}/docker-compose.yml" ps -aq)" ]]; then
  echo 'Project Compose resources still exist after cleanup.' >&2
  exit 1
fi
rm -rf "${repo_root}/.venv" "${repo_root}/models" "${repo_root}/.local"
for path in .venv models .local; do
  if [[ -e "${repo_root}/${path}" ]]; then
    echo "Project artifact remained after cleanup: ${path}" >&2
    exit 1
  fi
done
echo 'Removed only multi-tenant-ai-inference-platform Compose resources, volumes, and generated artifacts.'
