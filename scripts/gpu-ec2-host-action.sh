#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
profile="${repo_root}/deployments/single-gpu"
identity_guard=(python3 "${repo_root}/scripts/gpu_ec2_host_guard.py")
gpu_guard=(python3 "${repo_root}/scripts/gpu_ec2_host_guard.py" --require-l4)

require_confirmation() {
  local variable="$1" expected="$2"
  [[ "${!variable:-}" == "$expected" ]] || {
    echo "refusing host operation: set ${variable}=${expected} after reviewing the runbook" >&2
    exit 1
  }
}

compose() {
  docker compose --env-file "${profile}/.env" -f "${profile}/compose.yaml" "$@"
}

case "${1:-}" in
  configure)
    require_confirmation GPU_EC2_CONFIGURE_CONFIRM apply
    # The first Ansible pass installs the driver, so nvidia-smi cannot be required yet.
    "${identity_guard[@]}"
    ansible_dir="${repo_root}/infrastructure/ansible"
    ansible="${ansible_dir}/.venv/bin/ansible-playbook"
    [[ -x "$ansible" ]] || { echo "missing pinned Ansible environment; follow infrastructure/ansible/README.md" >&2; exit 1; }
    cd "$ansible_dir"
    timeout 90m env ANSIBLE_CONFIG=ansible.cfg "$ansible" playbooks/configure-gpu-host.yml
    ;;
  deploy)
    require_confirmation GPU_EC2_DEPLOY_CONFIRM deploy
    [[ "${EUID}" -eq 0 ]] || { echo "run Compose from a root shell; Docker socket access is root-level" >&2; exit 1; }
    "${gpu_guard[@]}"
    python3 "${repo_root}/scripts/gpu_ec2_deploy_preflight.py" "${profile}/.env"
    compose config --quiet
    if ! timeout 45m docker compose --env-file "${profile}/.env" \
      -f "${profile}/compose.yaml" up --build --detach; then
      compose stop vllm gateway-1 gateway-2 >/dev/null 2>&1 || true
      echo "Compose build or startup failed or exceeded 45 minutes; inference services were stopped" >&2
      exit 1
    fi
    if ! python3 "${repo_root}/scripts/gpu_ec2_smoke.py" --readiness-only --wait-seconds 1200; then
      compose stop vllm gateway-1 gateway-2
      echo "inference readiness timed out; inference services were stopped for cost control" >&2
      exit 1
    fi
    ;;
  evaluate)
    require_confirmation GPU_EC2_EVALUATE_CONFIRM run
    [[ "${EUID}" -eq 0 ]] || { echo "run the Docker evaluation from a root shell" >&2; exit 1; }
    "${gpu_guard[@]}"
    timeout 20m docker compose --env-file "${profile}/.env" \
      -f "${profile}/compose.yaml" --profile gpu-evaluation run --build --rm evaluator
    ;;
  benchmark)
    require_confirmation GPU_EC2_BENCHMARK_CONFIRM run
    [[ "${EUID}" -eq 0 ]] || { echo "run the Docker benchmark from a root shell" >&2; exit 1; }
    "${gpu_guard[@]}"
    max_minutes="${GPU_EC2_BENCHMARK_MAX_MINUTES:-60}"
    [[ "$max_minutes" =~ ^[0-9]+$ ]] && (( max_minutes >= 1 && max_minutes <= 120 )) || {
      echo "GPU_EC2_BENCHMARK_MAX_MINUTES must be an integer from 1 to 120" >&2
      exit 1
    }
    GPU_BENCHMARK_MAX_RUNTIME_MINUTES="$max_minutes" timeout "$((max_minutes + 10))m" \
      make -C "$repo_root" gpu-benchmark
    make -C "$repo_root" gpu-gateway-benchmark
    ;;
  *)
    echo "usage: $0 {configure|deploy|evaluate|benchmark}" >&2
    exit 2
    ;;
esac
