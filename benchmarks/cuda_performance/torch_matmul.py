"""Measure synchronized CPU/GPU PyTorch matrix multiplication and transfer time."""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path

DEFAULT_OUTPUT = Path("/var/tmp/gpu-lab/cuda-performance/matmul.json")
DEFAULT_SIZES = (256, 512, 1024)
DEFAULT_MAX_RUNTIME_SECONDS = 600


def validate_parameters(
    sizes: list[int], warmups: int, repeats: int, max_runtime_seconds: int
) -> None:
    if not sizes or any(size < 16 or size > 2048 for size in sizes):
        raise ValueError("matrix sizes must be between 16 and 2048")
    if warmups < 0 or repeats < 1 or repeats > 100:
        raise ValueError("warmups must be nonnegative; repeats must be between 1 and 100")
    if max_runtime_seconds < 1 or max_runtime_seconds > DEFAULT_MAX_RUNTIME_SECONDS:
        raise ValueError("maximum runtime must be between 1 and 600 seconds")


def plan_record(
    sizes: list[int], warmups: int, repeats: int, max_runtime_seconds: int
) -> dict:
    validate_parameters(sizes, warmups, repeats, max_runtime_seconds)
    return {
        "mode": "dry-run",
        "workload": "square matrix multiplication and host/device transfer",
        "sizes": sizes,
        "warmups": warmups,
        "repeats": repeats,
        "max_runtime_seconds": max_runtime_seconds,
        "planned_compute_dtypes": ["float32", "float16", "bfloat16 when supported"],
        "network_requests": 0,
        "gpu_operations": 0,
    }


def median_and_gflops(samples_ms: list[float], size: int) -> dict:
    median_ms = statistics.median(samples_ms)
    return {
        "samples_ms": [round(value, 6) for value in samples_ms],
        "median_ms": round(median_ms, 6),
        "median_gflops": round((2 * size**3 / (median_ms / 1000)) / 1e9, 4),
    }


def check_deadline(deadline: float) -> None:
    if time.monotonic() >= deadline:
        raise RuntimeError("CUDA performance batch reached its runtime limit")


def cpu_benchmark(
    torch, a, b, warmups: int, repeats: int, deadline: float
) -> tuple[list[float], object]:
    output = torch.empty((a.shape[0], b.shape[1]), dtype=a.dtype, device="cpu")
    for _ in range(warmups):
        check_deadline(deadline)
        torch.mm(a, b, out=output)
    samples = []
    for _ in range(repeats):
        check_deadline(deadline)
        started = time.perf_counter()
        torch.mm(a, b, out=output)
        samples.append((time.perf_counter() - started) * 1000)
    return samples, output.clone()


def cuda_benchmark(
    torch, a, b, warmups: int, repeats: int, deadline: float
) -> tuple[list[float], object]:
    output = torch.empty((a.shape[0], b.shape[1]), dtype=a.dtype, device="cuda")
    for _ in range(warmups):
        check_deadline(deadline)
        torch.mm(a, b, out=output)
    torch.cuda.synchronize()
    samples = []
    for _ in range(repeats):
        check_deadline(deadline)
        start_event = torch.cuda.Event(enable_timing=True)
        end_event = torch.cuda.Event(enable_timing=True)
        start_event.record()
        torch.mm(a, b, out=output)
        end_event.record()
        torch.cuda.synchronize()
        samples.append(start_event.elapsed_time(end_event))
    return samples, output


def transfer_benchmark(torch, host_tensor, repeats: int, deadline: float) -> dict:
    pinned = host_tensor.pin_memory()
    host_destination = torch.empty_like(pinned, device="cpu", pin_memory=True)
    device_tensor = torch.empty_like(pinned, device="cuda")
    h2d, d2h = [], []
    for _ in range(repeats):
        check_deadline(deadline)
        torch.cuda.synchronize()
        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record()
        device_tensor.copy_(pinned, non_blocking=True)
        end.record()
        torch.cuda.synchronize()
        h2d.append(start.elapsed_time(end))

        start, end = torch.cuda.Event(enable_timing=True), torch.cuda.Event(enable_timing=True)
        start.record()
        host_destination.copy_(device_tensor, non_blocking=True)
        end.record()
        torch.cuda.synchronize()
        d2h.append(start.elapsed_time(end))
    return {
        "bytes": host_tensor.numel() * host_tensor.element_size(),
        "host_to_device_median_ms": round(statistics.median(h2d), 6),
        "device_to_host_median_ms": round(statistics.median(d2h), 6),
        "samples_per_direction": repeats,
    }


def driver_version() -> str | None:
    try:
        return subprocess.check_output(
            ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
            text=True,
            timeout=3,
        ).splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def execute(
    torch, sizes: list[int], warmups: int, repeats: int, max_runtime_seconds: int
) -> dict:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; refusing to silently run a CPU-only GPU benchmark")
    device = torch.cuda.get_device_properties(0)
    if "L4" not in device.name:
        raise RuntimeError(f"expected one NVIDIA L4, observed {device.name!r}")
    if torch.cuda.device_count() != 1:
        raise RuntimeError(f"expected one visible GPU, found {torch.cuda.device_count()}")
    deadline = time.monotonic() + max_runtime_seconds
    dtypes = [("float32", torch.float32), ("float16", torch.float16)]
    if torch.cuda.is_bf16_supported():
        dtypes.append(("bfloat16", torch.bfloat16))
    torch.manual_seed(4201)
    results = []
    for size in sizes:
        a_cpu = torch.randn((size, size), dtype=torch.float32)
        b_cpu = torch.randn((size, size), dtype=torch.float32)
        cpu_samples, _ = cpu_benchmark(
            torch, a_cpu, b_cpu, warmups, repeats, deadline
        )
        a_gpu_fp32 = a_cpu.to("cuda")
        b_gpu_fp32 = b_cpu.to("cuda")
        precision_results = []
        for name, dtype in dtypes:
            torch.cuda.reset_peak_memory_stats()
            a_gpu, b_gpu = a_gpu_fp32.to(dtype), b_gpu_fp32.to(dtype)
            gpu_samples, result = cuda_benchmark(
                torch, a_gpu, b_gpu, warmups, repeats, deadline
            )
            torch.cuda.synchronize()
            tolerance = {"float32": (1e-4, 1e-4), "float16": (1e-2, 1e-2), "bfloat16": (2e-2, 2e-2)}[name]
            # Compare the multiply against FP32 using the same rounded inputs.
            # This isolates multiplication error from input-quantization error.
            reference = torch.mm(a_gpu.float(), b_gpu.float()).cpu()
            torch.testing.assert_close(
                result.float().cpu(), reference, rtol=tolerance[0], atol=tolerance[1]
            )
            precision_results.append(
                {
                    "dtype": name,
                    "gpu": median_and_gflops(gpu_samples, size),
                    "max_memory_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "correctness_vs_cpu_fp32": "passed",
                }
            )
        transfers = transfer_benchmark(torch, a_cpu, repeats, deadline)
        results.append(
            {
                "matrix_size": size,
                "cpu_fp32": median_and_gflops(cpu_samples, size),
                "gpu": precision_results,
                "transfer": transfers,
            }
        )
    return {
        "schema_version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "platform": {
            "gpu_name": device.name,
            "gpu_memory_bytes": device.total_memory,
            "driver_version": driver_version(),
            "pytorch_version": torch.__version__,
            "torch_cuda_version": torch.version.cuda,
            "instance_type": os.getenv("GPU_INSTANCE_TYPE", "UNSET"),
            "region": os.getenv("AWS_REGION", "UNSET"),
            "git_sha": os.getenv("GPU_LAB_GIT_SHA", "UNSET"),
            "cpu_threads": torch.get_num_threads(),
        },
        "method": {
            "warmups": warmups,
            "repeats": repeats,
            "max_runtime_seconds": max_runtime_seconds,
            "gpu_timing": "CUDA events, synchronized before each timed series and after each sample",
            "gflops_formula": "2 * N^3 / median_seconds / 1e9",
        },
        "results": results,
        "limitations": [
            "PyTorch GEMM timings include framework launch behavior and are not a custom-kernel profile.",
            "This experiment is a single-process microbenchmark, not an inference-serving result.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sizes", type=int, nargs="+", default=list(DEFAULT_SIZES))
    parser.add_argument("--warmups", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=10)
    parser.add_argument("--max-runtime-seconds", type=int, default=DEFAULT_MAX_RUNTIME_SECONDS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        validate_parameters(args.sizes, args.warmups, args.repeats, args.max_runtime_seconds)
    except ValueError as error:
        parser.error(str(error))
    if args.dry_run:
        print(
            json.dumps(
                plan_record(args.sizes, args.warmups, args.repeats, args.max_runtime_seconds),
                indent=2,
            )
        )
        return 0
    output = args.output.resolve()
    if output.is_relative_to(Path(__file__).resolve().parents[2]):
        parser.error("benchmark output must be outside the public repository")
    try:
        import torch
    except ImportError as error:
        parser.error(f"PyTorch is not installed in this runtime: {error}")
    try:
        report = execute(
            torch, args.sizes, args.warmups, args.repeats, args.max_runtime_seconds
        )
    except (AssertionError, RuntimeError, subprocess.SubprocessError) as error:
        parser.error(str(error))
    output.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(file_descriptor, 0o600)
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as report_file:
        report_file.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"gpu": report["platform"]["gpu_name"], "sizes": args.sizes, "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
