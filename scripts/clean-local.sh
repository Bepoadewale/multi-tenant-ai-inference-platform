#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
project_name="multi-tenant-ai-inference-platform"
mkdir -p "${repo_root}/.local"
lock_dir="${repo_root}/.local/.lifecycle-lock"
if ! mkdir "${lock_dir}" 2>/dev/null; then
  lock_pid=$(cat "${lock_dir}/pid" 2>/dev/null || true)
  if [[ -z "${lock_pid}" ]] || ! kill -0 "${lock_pid}" 2>/dev/null; then
    rm -f "${lock_dir}/pid"
    rmdir "${lock_dir}" 2>/dev/null || true
  fi
  if ! mkdir "${lock_dir}" 2>/dev/null; then
    echo 'Another project lifecycle command is already running; wait for it to finish.' >&2
    exit 1
  fi
fi
printf '%s\n' "$$" > "${lock_dir}/pid"
trap 'rm -f "${lock_dir}/pid"; rmdir "${lock_dir}" 2>/dev/null || true' EXIT
dead_ids=$(docker ps -aq --filter "label=com.docker.compose.project=${project_name}" --filter status=dead)
if [[ -n "${dead_ids}" ]]; then
  echo 'Docker Desktop has stale dead records for this project. Restart Docker Desktop; if they remain, use its Troubleshoot cleanup before retrying project cleanup.' >&2
  exit 1
fi
if ! docker compose -f "${repo_root}/docker-compose.yml" down --volumes --remove-orphans --rmi local; then
  echo 'Warning: Compose reported stale project state during shutdown; continuing with scoped cleanup.' >&2
fi
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
docker network rm "${project_name}_default" >/dev/null 2>&1 || true
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
