"""Measure a small Triton vector-add kernel on exactly one NVIDIA L4."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = Path("/var/tmp/gpu-lab/cuda-performance/triton-vector-add.json")
MAX_ELEMENTS = 16_777_216
MAX_RUNTIME_SECONDS = 120


def validate_parameters(
    elements: int, block_size: int, warmups: int, repeats: int, max_runtime_seconds: int
) -> None:
    if elements < 4096 or elements > MAX_ELEMENTS:
        raise ValueError(f"elements must be between 4096 and {MAX_ELEMENTS}")
    if block_size not in {128, 256, 512, 1024}:
        raise ValueError("block size must be 128, 256, 512, or 1024")
    if warmups < 1 or warmups > 20:
        raise ValueError("warmups must be between 1 and 20")
    if repeats < 3 or repeats > 50:
        raise ValueError("repeats must be between 3 and 50")
    if max_runtime_seconds < 1 or max_runtime_seconds > MAX_RUNTIME_SECONDS:
        raise ValueError(f"runtime must be between 1 and {MAX_RUNTIME_SECONDS} seconds")


def plan_record(
    elements: int, block_size: int, warmups: int, repeats: int, max_runtime_seconds: int
) -> dict:
    validate_parameters(elements, block_size, warmups, repeats, max_runtime_seconds)
    return {
        "mode": "dry-run",
        "workload": "Triton FP32 vector addition",
        "elements": elements,
        "block_size": block_size,
        "warmups": warmups,
        "repeats": repeats,
        "max_runtime_seconds": max_runtime_seconds,
        "network_requests": 0,
        "gpu_operations": 0,
    }


def _driver_version() -> str | None:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            text=True,
            timeout=3,
        ).splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def execute(
    torch,
    triton,
    elements: int,
    block_size: int,
    warmups: int,
    repeats: int,
    max_runtime_seconds: int,
) -> dict:
    validate_parameters(elements, block_size, warmups, repeats, max_runtime_seconds)
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; refusing to run this GPU experiment")
    if torch.cuda.device_count() != 1:
        raise RuntimeError(f"expected one visible GPU, found {torch.cuda.device_count()}")
    device = torch.cuda.get_device_properties(0)
    if "L4" not in device.name:
        raise RuntimeError(f"expected one NVIDIA L4, observed {device.name!r}")

    deadline = time.monotonic() + max_runtime_seconds
    torch.manual_seed(4201)
    x = torch.randn((elements,), device="cuda", dtype=torch.float32)
    y = torch.randn((elements,), device="cuda", dtype=torch.float32)
    output = torch.empty_like(x)
    reference = x + y
    # Import the JIT kernel only after this non-dry-run path reaches the GPU checks.
    from triton_vector_add_kernel import vector_add

    kernel = vector_add
    grid = (triton.cdiv(elements, block_size),)

    for _ in range(warmups):
        if time.monotonic() >= deadline:
            raise RuntimeError("Triton warm-up exceeded its runtime limit")
        kernel[grid](x, y, output, elements, BLOCK_SIZE=block_size)
    torch.cuda.synchronize()
    torch.testing.assert_close(output, reference, rtol=0, atol=0)

    samples_ms = []
    for _ in range(repeats):
        if time.monotonic() >= deadline:
            raise RuntimeError("Triton measurement exceeded its runtime limit")
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        start.record()
        kernel[grid](x, y, output, elements, BLOCK_SIZE=block_size)
        end.record()
        torch.cuda.synchronize()
        samples_ms.append(float(start.elapsed_time(end)))

    median_ms = statistics.median(samples_ms)
    # Three FP32 values per element are read/written. This is an effective byte
    # count, not a measurement of physical DRAM traffic or cache misses.
    effective_bytes = elements * 3 * torch.tensor([], dtype=torch.float32).element_size()
    median_effective_gib_per_second = effective_bytes / (median_ms / 1000) / (1024**3)
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "platform": {
            "gpu_name": device.name,
            "gpu_memory_bytes": device.total_memory,
            "compute_capability": f"{device.major}.{device.minor}",
            "driver_version": _driver_version(),
            "pytorch_version": str(torch.__version__),
            "torch_cuda_version": torch.version.cuda,
            "triton_version": triton.__version__,
            "instance_type": os.getenv("GPU_INSTANCE_TYPE", "UNSET"),
            "region": os.getenv("AWS_REGION", "UNSET"),
            "git_sha": os.getenv("GPU_LAB_GIT_SHA", "UNSET"),
        },
        "method": {
            "elements": elements,
            "dtype": "float32",
            "block_size": block_size,
            "warmups": warmups,
            "repeats": repeats,
            "max_runtime_seconds": max_runtime_seconds,
            "timing": "CUDA events; stream synchronized after every sample",
            "effective_bytes_formula": "elements * 3 * sizeof(float32)",
            "effective_gib_per_second_formula": "effective bytes / median seconds / 2^30",
        },
        "result": {
            "samples_ms": [round(value, 6) for value in samples_ms],
            "median_ms": round(median_ms, 6),
            "median_effective_gib_per_second": round(median_effective_gib_per_second, 4),
            "correctness_vs_torch": "passed",
        },
        "limitations": [
            "The effective byte count does not measure physical DRAM traffic or cache hits.",
            "This single-kernel microbenchmark does not represent LLM inference performance.",
            "The GPU result has not been executed until a genuine L4 run is recorded.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--elements", type=int, default=1_048_576)
    parser.add_argument("--block-size", type=int, default=256)
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--max-runtime-seconds", type=int, default=60)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        validate_parameters(
            args.elements, args.block_size, args.warmups, args.repeats, args.max_runtime_seconds
        )
    except ValueError as error:
        parser.error(str(error))
    if args.dry_run:
        print(
            json.dumps(
                plan_record(
                    args.elements, args.block_size, args.warmups, args.repeats,
                    args.max_runtime_seconds,
                ),
                indent=2,
            )
        )
        return 0

    output = args.output.resolve()
    if output.is_relative_to(REPOSITORY_ROOT):
        parser.error("result output must be outside the public repository")
    try:
        import torch
        import triton
    except ImportError as error:
        parser.error(f"the pinned CUDA/PyTorch environment is unavailable: {error}")
    try:
        report = execute(
            torch, triton, args.elements, args.block_size, args.warmups,
            args.repeats, args.max_runtime_seconds,
        )
    except (AssertionError, RuntimeError, subprocess.SubprocessError) as error:
        parser.error(str(error))

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(descriptor, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as report_file:
        report_file.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"gpu": report["platform"]["gpu_name"], "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
