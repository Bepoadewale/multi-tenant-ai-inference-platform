import os
import subprocess
import sys
from pathlib import Path

import pytest

from benchmarks.cuda_performance.triton_vector_add import (
    MAX_ELEMENTS,
    MAX_RUNTIME_SECONDS,
    plan_record,
    validate_parameters,
)


def test_triton_vector_add_plan_is_bounded_and_has_no_gpu_side_effects():
    plan = plan_record(1_048_576, 256, 3, 10, 60)

    assert plan == {
        "mode": "dry-run",
        "workload": "Triton FP32 vector addition",
        "elements": 1_048_576,
        "block_size": 256,
        "warmups": 3,
        "repeats": 10,
        "max_runtime_seconds": 60,
        "network_requests": 0,
        "gpu_operations": 0,
    }


def test_triton_vector_add_cli_dry_run_needs_no_cuda_libraries():
    script = Path("benchmarks/cuda_performance/triton_vector_add.py")
    completed = subprocess.run(
        [sys.executable, str(script), "--dry-run"],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert '"gpu_operations": 0' in completed.stdout
    assert '"network_requests": 0' in completed.stdout


def test_triton_host_wrapper_requires_confirmation_before_host_metadata():
    wrapper = Path("scripts/gpu-ec2-triton.sh")
    completed = subprocess.run(
        ["bash", str(wrapper)], capture_output=True, text=True, timeout=5
    )

    assert completed.returncode == 1
    assert "set GPU_EC2_TRITON_CONFIRM=run" in completed.stderr
    assert "metadata" not in completed.stderr.lower()


def test_triton_host_wrapper_rejects_oversized_runtime_before_host_metadata():
    wrapper = Path("scripts/gpu-ec2-triton.sh")
    completed = subprocess.run(
        ["bash", str(wrapper)],
        env={
            **os.environ,
            "GPU_EC2_TRITON_CONFIRM": "run",
            "GPU_EC2_TRITON_MAX_RUNTIME_SECONDS": "121",
        },
        capture_output=True,
        text=True,
        timeout=5,
    )

    assert completed.returncode == 1
    assert "must be an integer from 1 to 120" in completed.stderr


@pytest.mark.parametrize(
    ("elements", "block_size", "warmups", "repeats", "runtime"),
    [
        (4095, 256, 3, 10, 60),
        (MAX_ELEMENTS + 1, 256, 3, 10, 60),
        (4096, 64, 3, 10, 60),
        (4096, 256, 0, 10, 60),
        (4096, 256, 3, 51, 60),
        (4096, 256, 3, 10, MAX_RUNTIME_SECONDS + 1),
    ],
)
def test_triton_vector_add_rejects_unbounded_or_invalid_parameters(
    elements, block_size, warmups, repeats, runtime
):
    with pytest.raises(ValueError):
        validate_parameters(elements, block_size, warmups, repeats, runtime)
