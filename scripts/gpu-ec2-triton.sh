#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

[[ "${GPU_EC2_TRITON_CONFIRM:-}" == "run" ]] || {
  echo "refusing Triton work: set GPU_EC2_TRITON_CONFIRM=run after reviewing the GPU batch plan" >&2
  exit 1
}

max_seconds="${GPU_EC2_TRITON_MAX_RUNTIME_SECONDS:-60}"
[[ "$max_seconds" =~ ^[0-9]+$ ]] && (( max_seconds >= 1 && max_seconds <= 120 )) || {
  echo "GPU_EC2_TRITON_MAX_RUNTIME_SECONDS must be an integer from 1 to 120" >&2
  exit 1
}

python3 "${repo_root}/scripts/gpu_ec2_host_guard.py" --require-l4
python="/opt/gpu-lab/torch-venv/bin/python"
[[ -x "$python" ]] || {
  echo "missing pinned CUDA/PyTorch environment; follow the GPU installation manifest" >&2
  exit 1
}

timeout "$((max_seconds + 10))s" "$python" \
  "${repo_root}/benchmarks/cuda_performance/triton_vector_add.py" \
  --max-runtime-seconds "$max_seconds"
