"""Run a bounded, metadata-rich matrix with vLLM's official serving benchmark."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import signal
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic
from urllib.request import Request, urlopen

PROFILE = Path("deployments/single-gpu")
DEFAULT_MATRIX = Path("benchmarks/gpu_inference/workloads.json")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
IMDS_BASE = "http://169.254.169.254/latest"


def ec2_metadata() -> dict[str, str]:
    """Read instance identity metadata with IMDSv2 without printing its token."""
    token_request = Request(
        f"{IMDS_BASE}/api/token",
        data=b"",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        method="PUT",
    )
    with urlopen(token_request, timeout=2) as response:
        token = response.read().decode("utf-8")
    identity = {}
    for name, path in (
        ("instance_type", "meta-data/instance-type"),
        ("region", "meta-data/placement/region"),
    ):
        request = Request(
            f"{IMDS_BASE}/{path}", headers={"X-aws-ec2-metadata-token": token}
        )
        with urlopen(request, timeout=2) as response:
            identity[name] = response.read().decode("utf-8").strip()
    return identity


def load_matrix(path: Path, allow_16: bool) -> tuple[dict, list[dict]]:
    matrix = json.loads(path.read_text(encoding="utf-8"))
    if matrix.get("schema_version") != 1:
        raise ValueError("workload matrix schema_version must be 1")
    for field in ("model_alias", "model_id"):
        if not isinstance(matrix.get(field), str) or not matrix[field].strip():
            raise ValueError(f"workload matrix {field} must be a non-empty string")
    context = matrix["context_length"]
    margin = matrix.get("context_safety_margin_tokens", 0)
    if context < 1 or margin < 0:
        raise ValueError("context length must be positive and the safety margin cannot be negative")
    if matrix["num_prompts"] < 1 or matrix["num_warmups"] < 0:
        raise ValueError("num_prompts must be positive and num_warmups cannot be negative")
    selected = []
    names = set()
    for workload in matrix["workloads"]:
        name = workload["name"]
        if not SAFE_ID.fullmatch(name) or name in names:
            raise ValueError(f"workload name is invalid or duplicated: {name!r}")
        names.add(name)
        input_tokens = workload["input_tokens"]
        output_tokens = workload["output_tokens"]
        if min(input_tokens, output_tokens) < 1:
            raise ValueError(f"{name}: input and output token lengths must be positive")
        if input_tokens + output_tokens + margin > context:
            raise ValueError(
                f"{name}: input + output + {margin} safety tokens exceeds {context}-token context"
            )
        concurrency_values = workload["concurrency"]
        if len(concurrency_values) != len(set(concurrency_values)):
            raise ValueError(f"{name}: concurrency values must not be duplicated")
        for concurrency in concurrency_values:
            if concurrency not in {1, 2, 4, 8, 16}:
                raise ValueError(f"{name}: unsupported concurrency {concurrency}")
            if concurrency == 16 and not allow_16:
                continue
            selected.append(
                {
                    "name": name,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "concurrency": concurrency,
                }
            )
    if not selected:
        raise ValueError("matrix contains no runnable workloads")
    return matrix, selected


def benchmark_container_name(case: dict, repetition: int) -> str:
    return f"gpu-lab-bench-{case['name']}-c{case['concurrency']}-r{repetition}"


def benchmark_command(
    case: dict, matrix: dict, repetition: int, metadata: dict, output_dir: Path
) -> list[str]:
    run_id = f"{case['name']}-c{case['concurrency']}-r{repetition}"
    cli_metadata = {
        **metadata,
        "workload": case["name"],
        "concurrency": str(case["concurrency"]),
        "input_tokens": str(case["input_tokens"]),
        "output_tokens": str(case["output_tokens"]),
        "repetition": str(repetition),
    }
    command = [
        "docker",
        "compose",
        "--env-file",
        str(PROFILE / ".env"),
        "-f",
        str(PROFILE / "compose.yaml"),
        "--profile",
        "gpu-benchmark",
        "run",
        "--rm",
        "--no-deps",
        "--volume",
        f"{output_dir}:/results:rw",
        "--name",
        benchmark_container_name(case, repetition),
        "benchmark",
        "bench",
        "serve",
        "--backend",
        "openai-chat",
        "--base-url",
        "http://vllm:8000",
        "--endpoint",
        "/v1/chat/completions",
        "--model",
        matrix["model_alias"],
        "--tokenizer",
        matrix["model_id"],
        "--dataset-name",
        "random",
        "--random-input-len",
        str(case["input_tokens"]),
        "--random-output-len",
        str(case["output_tokens"]),
        "--num-prompts",
        str(matrix["num_prompts"]),
        "--num-warmups",
        str(matrix["num_warmups"]),
        "--max-concurrency",
        str(case["concurrency"]),
        "--ready-check-timeout-sec",
        "30",
        "--request-rate",
        "inf",
        "--percentile-metrics",
        "ttft,tpot,itl,e2el",
        "--metric-percentiles",
        "50,95,99",
        "--seed",
        "4201",
        "--save-result",
        "--result-dir",
        "/results",
        "--result-filename",
        f"{run_id}.json",
        "--label",
        "single-l4-lab",
        "--metadata",
        *[f"{key}={value}" for key, value in sorted(cli_metadata.items())],
    ]
    return command


def stop_benchmark_container(name: str) -> None:
    try:
        subprocess.run(
            ["docker", "stop", "--time", "10", name],
            check=False,
            timeout=15,
            capture_output=True,
        )
    except subprocess.TimeoutExpired:
        print(f"Could not confirm benchmark container stop: {name}", file=sys.stderr)


def base_metadata(args: argparse.Namespace) -> dict[str, str]:
    if args.dry_run:
        return {
            "git_sha": "DRY_RUN",
            "region": args.region or "UNSET",
            "instance_type": args.instance_type or "UNSET",
            "gpu_name": "NOT_READ",
            "driver_version": "NOT_READ",
            "model_revision": args.model_revision or "UNSET",
        }
    required = {
        "AWS_REGION": args.region,
        "GPU_INSTANCE_TYPE": args.instance_type,
        "GPU_MODEL_REVISION": args.model_revision,
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        raise ValueError(f"required metadata is missing: {', '.join(missing)}")
    if args.region != "us-east-1":
        raise ValueError("the initial single-L4 experiment is limited to us-east-1")
    if args.instance_type not in {"g6.xlarge", "g6.2xlarge"}:
        raise ValueError("GPU_INSTANCE_TYPE must be g6.xlarge or g6.2xlarge")
    identity = ec2_metadata()
    if identity["region"] != args.region or identity["instance_type"] != args.instance_type:
        raise ValueError(
            "provided region/instance type do not match IMDSv2: "
            f"{identity['region']} / {identity['instance_type']}"
        )
    gpu = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total",
            "--format=csv,noheader,nounits",
        ],
        text=True,
    ).strip()
    gpu_parts = [part.strip() for part in gpu.split(",", maxsplit=2)]
    if len(gpu.splitlines()) != 1 or len(gpu_parts) != 3 or "L4" not in gpu_parts[0]:
        raise ValueError(f"expected an NVIDIA L4, observed GPU metadata: {gpu}")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    compose = [
        "docker",
        "compose",
        "--env-file",
        str(PROFILE / ".env"),
        "-f",
        str(PROFILE / "compose.yaml"),
    ]
    container = subprocess.check_output([*compose, "ps", "-q", "vllm"], text=True).strip()
    if not container:
        raise ValueError("the vLLM Compose service is not running")
    image = subprocess.check_output(
        ["docker", "inspect", "--format", "{{.Config.Image}}", container], text=True
    ).strip()
    engine_args = json.loads(
        subprocess.check_output(
            ["docker", "inspect", "--format", "{{json .Config.Cmd}}", container], text=True
        )
    )

    def engine_argument(flag: str) -> str:
        try:
            return engine_args[engine_args.index(flag) + 1]
        except (ValueError, IndexError) as error:
            raise ValueError(f"running vLLM command does not include {flag}") from error

    versions = json.loads(
        subprocess.check_output(
            [
                *compose,
                "exec",
                "-T",
                "vllm",
                "python",
                "-c",
                "import json, torch, vllm; print(json.dumps({'vllm': vllm.__version__, 'pytorch': torch.__version__, 'torch_cuda': torch.version.cuda}))",
            ],
            text=True,
        )
    )
    return {
        "git_sha": commit,
        "region": args.region,
        "instance_type": args.instance_type,
        "gpu_name": gpu_parts[0],
        "driver_version": gpu_parts[1],
        "gpu_memory_mib": gpu_parts[2],
        "model_revision": args.model_revision,
        "vllm_image": image,
        "vllm_version": versions["vllm"],
        "pytorch_version": versions["pytorch"],
        "torch_cuda_version": versions["torch_cuda"] or "NONE",
        "vllm_max_num_seqs": engine_argument("--max-num-seqs"),
        "vllm_max_model_len": engine_argument("--max-model-len"),
        "vllm_gpu_memory_utilization": engine_argument("--gpu-memory-utilization"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("/var/tmp/gpu-lab/benchmark-results")
    )
    parser.add_argument("--region", default=os.getenv("AWS_REGION"))
    parser.add_argument("--instance-type", default=os.getenv("GPU_INSTANCE_TYPE"))
    parser.add_argument("--model-revision", default=os.getenv("GPU_MODEL_REVISION"))
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--max-runtime-minutes", type=int, default=120)
    parser.add_argument("--per-run-timeout-seconds", type=int, default=600)
    parser.add_argument("--allow-concurrency-16", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    try:
        matrix, cases = load_matrix(args.matrix, args.allow_concurrency_16)
        repetitions = args.repetitions if args.repetitions is not None else matrix["repetitions"]
        if repetitions < 1 or repetitions > 10:
            raise ValueError("repetitions must be between 1 and 10")
        if not 1 <= args.max_runtime_minutes <= 120:
            raise ValueError("max runtime must be between 1 and 120 minutes")
        if args.per_run_timeout_seconds < 1:
            raise ValueError("per-run timeout must be positive")
        metadata = base_metadata(args)
    except (OSError, KeyError, json.JSONDecodeError, ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))

    output_dir = args.output_dir.resolve()
    commands = []
    for case in cases:
        for repetition in range(1, repetitions + 1):
            command = benchmark_command(case, matrix, repetition, metadata, output_dir)
            container_name = benchmark_container_name(case, repetition)
            commands.append((command, container_name))

    run_record = {
        "created_at": datetime.now(UTC).isoformat(),
        "mode": "dry-run" if args.dry_run else "execution",
        "matrix": str(args.matrix),
        "context_length_tokens": matrix["context_length"],
        "context_safety_margin_tokens": matrix.get("context_safety_margin_tokens", 0),
        "number_of_cases": len(cases),
        "repetitions": repetitions,
        "max_runtime_minutes": args.max_runtime_minutes,
        "per_run_timeout_seconds": args.per_run_timeout_seconds,
        "expected_runs": len(commands),
        "metadata": metadata,
        "commands": [shlex.join(command) for command, _ in commands],
    }
    if args.dry_run:
        print(json.dumps(run_record, indent=2))
        return 0

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "run-metadata.json").write_text(
        json.dumps(run_record, indent=2) + "\n", encoding="utf-8"
    )
    deadline = monotonic() + args.max_runtime_minutes * 60
    for index, (command, container_name) in enumerate(commands, start=1):
        remaining = deadline - monotonic()
        if remaining <= 0:
            print(f"Runtime limit reached; preserve partial results in {output_dir}", file=sys.stderr)
            return 124
        timeout = min(args.per_run_timeout_seconds, remaining)
        print(f"[{index}/{len(commands)}] {shlex.join(command)}", flush=True)
        process = subprocess.Popen(command, start_new_session=True)
        try:
            return_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            stop_benchmark_container(container_name)
            print(
                f"Benchmark timed out at run {index}; preserve partial results in {output_dir}",
                file=sys.stderr,
            )
            return 124
        except KeyboardInterrupt:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            stop_benchmark_container(container_name)
            print(f"Benchmark interrupted at run {index}; partial results are preserved", file=sys.stderr)
            return 130
        if return_code:
            print(
                f"Benchmark stopped at run {index}; preserve partial results in {output_dir}",
                file=sys.stderr,
            )
            return return_code
    print(f"Completed {len(commands)} benchmark runs. Results: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
