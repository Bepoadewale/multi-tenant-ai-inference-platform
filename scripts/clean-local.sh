#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
docker compose -f "${repo_root}/docker-compose.yml" down --volumes --remove-orphans --rmi local
project_name="multi-tenant-ai-inference-platform"
# Compose can leave containers in Created state after an interrupted network/start
# operation. Remove only containers labeled as belonging to this Compose project.
container_ids=$(docker ps -aq --filter "label=com.docker.compose.project=${project_name}")
if [[ -n "${container_ids}" ]]; then
  docker rm -f ${container_ids}
fi
network_ids=$(docker network ls -q --filter "label=com.docker.compose.project=${project_name}")
if [[ -n "${network_ids}" ]]; then
  docker network rm ${network_ids}
fi
if [[ -n "$(docker ps -aq --filter "label=com.docker.compose.project=${project_name}")" ]]; then
  echo 'Project Compose resources still exist after cleanup.' >&2
  exit 1
fi
image_ids=$(docker image ls -q --filter "label=com.bepoadewale.project=${project_name}")
if [[ -n "${image_ids}" ]]; then
  docker image rm -f ${image_ids}
fi
volume_ids=$(docker volume ls -q --filter "label=com.bepoadewale.project=${project_name}")
if [[ -n "${volume_ids}" ]]; then
  docker volume rm -f ${volume_ids}
fi
if [[ -n "$(docker ps -aq --filter "label=com.bepoadewale.project=${project_name}")" ]] || [[ -n "$(docker volume ls -q --filter "label=com.bepoadewale.project=${project_name}")" ]]; then
  echo 'Project sandbox resources still exist after cleanup.' >&2
  exit 1
fi
rm -rf "${repo_root}/.venv" "${repo_root}/models" "${repo_root}/.local"
for path in .venv models .local; do
  if [[ -e "${repo_root}/${path}" ]]; then
    echo "Project artifact remained after cleanup: ${path}" >&2
    exit 1
  fi
done
echo 'Removed only multi-tenant-ai-inference-platform Compose resources, locally built images, volumes, and generated artifacts.'
