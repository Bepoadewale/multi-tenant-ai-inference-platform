"""Measure authenticated gateway latency and tenant admission without saving content."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import statistics
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen

TENANTS = {
    "customer-support": "customer_support",
    "internal-engineering": "internal_engineering",
    "research": "research",
}
PROMPT = "Reply with the single word READY."


class RejectRedirect(HTTPRedirectHandler):
    """Never forward a tenant bearer token to a redirect destination."""

    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        raise HTTPError(request.full_url, code, "redirect refused", headers, file_pointer)


def percentile(values: list[float], rank: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = max(0.0, min(float(len(ordered) - 1), (len(ordered) - 1) * rank))
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return round(ordered[lower] + (ordered[upper] - ordered[lower]) * fraction, 3)


def summarize(rows: list[dict], elapsed_seconds: float) -> dict:
    latencies = [row["latency_ms"] for row in rows if row["latency_ms"] is not None]
    queue_waits = [row["client_queue_wait_ms"] for row in rows]
    statuses = Counter(str(row["status"]) for row in rows)
    successful = [row for row in rows if row["status"] == 200]
    return {
        "requests": len(rows),
        "successful": len(successful),
        "failed": len(rows) - len(successful),
        "status_counts": dict(sorted(statuses.items())),
        "latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "mean": round(statistics.fmean(latencies), 3) if latencies else None,
        },
        "client_queue_wait_ms": {
            "p50": percentile(queue_waits, 0.50),
            "p95": percentile(queue_waits, 0.95),
        },
        "successful_requests_per_second": round(
            len(successful) / elapsed_seconds, 3
        )
        if elapsed_seconds > 0
        else 0,
        "reported_prompt_tokens": sum(row.get("prompt_tokens", 0) for row in successful),
        "reported_completion_tokens": sum(
            row.get("completion_tokens", 0) for row in successful
        ),
    }


def require_l4() -> dict[str, str]:
    """Check instance identity through IMDSv2 and require one visible NVIDIA L4."""
    token_request = Request(
        "http://169.254.169.254/latest/api/token",
        data=b"",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "60"},
        method="PUT",
    )
    with urlopen(token_request, timeout=2) as response:
        token = response.read().decode()
    identity: dict[str, str] = {}
    for key, path in (("instance_type", "instance-type"), ("region", "placement/region")):
        request = Request(
            f"http://169.254.169.254/latest/meta-data/{path}",
            headers={"X-aws-ec2-metadata-token": token},
        )
        with urlopen(request, timeout=2) as response:
            identity[key] = response.read().decode().strip()
    if identity["region"] != "us-east-1" or identity["instance_type"] not in {
        "g6.xlarge",
        "g6.2xlarge",
    }:
        raise ValueError("--require-l4 requires an allowed g6 instance in us-east-1")
    gpu = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=name,driver_version", "--format=csv,noheader"],
        text=True,
        timeout=10,
    ).strip().splitlines()
    if len(gpu) != 1 or "L4" not in gpu[0]:
        raise ValueError("--require-l4 expected exactly one visible NVIDIA L4")
    identity["gpu"] = gpu[0]
    return identity


def post_json(url: str, model: str, token: str | None, timeout: float) -> tuple[int, dict]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 8,
        "temperature": 0,
    }
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(
        f"{url.rstrip('/')}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    opener = build_opener(RejectRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except HTTPError as error:
        # Preserve only the status; do not read or log an upstream error body.
        return error.code, {}


async def request_one(
    url: str,
    model: str,
    tenant: str,
    token: str | None,
    semaphore: asyncio.Semaphore,
    timeout: float,
) -> dict:
    queued_at = perf_counter()
    async with semaphore:
        started_at = perf_counter()
        try:
            status, body = await asyncio.to_thread(
                post_json, url, model, token, timeout
            )
            latency = (perf_counter() - started_at) * 1000
            usage = body.get("usage", {}) if status == 200 else {}
            return {
                "tenant": tenant,
                "status": status,
                "latency_ms": round(latency, 3),
                "client_queue_wait_ms": round((started_at - queued_at) * 1000, 3),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            }
        except (URLError, TimeoutError, OSError, ValueError, TypeError):
            return {
                "tenant": tenant,
                "status": "transport_error",
                "latency_ms": round((perf_counter() - started_at) * 1000, 3),
                "client_queue_wait_ms": round((started_at - queued_at) * 1000, 3),
            }


async def run_phase(
    *,
    jobs: list[tuple[str, str, str, str | None]],
    concurrency: int,
    timeout: float,
) -> tuple[list[dict], float]:
    semaphore = asyncio.Semaphore(concurrency)
    started = perf_counter()
    rows = await asyncio.gather(
        *(
            request_one(url, model, tenant, token, semaphore, timeout)
            for url, model, tenant, token in jobs
        )
    )
    return rows, perf_counter() - started


def load_tokens(path: Path) -> dict[str, str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        tokens = {tenant: raw[key] for tenant, key in TENANTS.items()}
    except (OSError, ValueError, TypeError, KeyError) as error:
        raise ValueError("identity file must contain all three GPU-lab tenant tokens") from error
    if any(not isinstance(value, str) or not value for value in tokens.values()):
        raise ValueError("identity file contains an empty tenant token")
    return tokens


async def run(args: argparse.Namespace) -> dict:
    if args.dry_run:
        return {
            "mode": "dry-run",
            "tenants": list(TENANTS),
            "gateway_urls": args.gateway_url,
            "gateway_model": args.gateway_model,
            "direct_url_configured": bool(args.direct_url),
            "requests": args.requests,
            "concurrency": args.concurrency,
            "content_saved": False,
        }
    if args.concurrency < 2 or args.requests < 3 or args.timeout <= 0:
        raise ValueError("requests must be >= 3, concurrency >= 2, and timeout positive")
    tokens = load_tokens(args.identity_file)
    hardware = require_l4() if args.require_l4 else {"gpu": "not verified by this run"}
    if args.require_l4 and not args.model_revision:
        raise ValueError("set GPU_MODEL_REVISION or pass --model-revision for an L4 run")
    try:
        source_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, timeout=5
        ).strip()
    except (OSError, subprocess.SubprocessError):
        source_commit = "unknown"
    timestamp = datetime.now(UTC).isoformat()
    phases: dict[str, dict] = {}

    # Sequential paired-shape baselines provide a rough overhead comparison. They
    # are not an isolated measurement because runtime and cache state can differ.
    baseline_count = min(5, max(3, args.requests // 3))
    if args.direct_url:
        direct_jobs = [
            (args.direct_url, args.direct_model, "direct-vllm", None)
            for _ in range(baseline_count)
        ]
        direct, elapsed = await run_phase(
            jobs=direct_jobs, concurrency=1, timeout=args.timeout
        )
        phases["direct_baseline"] = {"summary": summarize(direct, elapsed)}
        support_jobs = [
            (args.gateway_url[0], args.gateway_model, "customer-support", tokens["customer-support"])
            for _ in range(baseline_count)
        ]
        gateway_base, elapsed = await run_phase(
            jobs=support_jobs, concurrency=1, timeout=args.timeout
        )
        phases["gateway_sequential_baseline"] = {
            "summary": summarize(gateway_base, elapsed)
        }
        direct_p50 = phases["direct_baseline"]["summary"]["latency_ms"]["p50"]
        gateway_p50 = phases["gateway_sequential_baseline"]["summary"]["latency_ms"]["p50"]
        phases["rough_gateway_overhead_p50_ms"] = (
            round(gateway_p50 - direct_p50, 3)
            if direct_p50 is not None and gateway_p50 is not None
            else None
        )

    workload = []
    tenant_names = list(TENANTS)
    for index in range(args.requests):
        tenant = tenant_names[index % len(tenant_names)]
        workload.append(
            (
                args.gateway_url[index % len(args.gateway_url)],
                args.gateway_model,
                tenant,
                tokens[tenant],
            )
        )
    rows, elapsed = await run_phase(
        jobs=workload,
        concurrency=args.concurrency,
        timeout=args.timeout,
    )
    by_tenant = {
        tenant: summarize([row for row in rows if row["tenant"] == tenant], elapsed)
        for tenant in tenant_names
    }
    phases["concurrent_gateway"] = {
        "summary": summarize(rows, elapsed),
        "by_tenant": by_tenant,
        "results": rows,
    }
    report = {
        "created_at": timestamp,
        "mode": "authenticated-gateway-benchmark",
        "source_commit": source_commit,
        "python_version": sys.version.split()[0],
        "model_revision": args.model_revision or "UNSET",
        "gateway_urls": args.gateway_url,
        "gateway_model": args.gateway_model,
        "direct_model": args.direct_model if args.direct_url else None,
        "direct_url_configured": bool(args.direct_url),
        "request_count": args.requests,
        "max_output_tokens": 8,
        "request_timeout_seconds": args.timeout,
        "concurrency": args.concurrency,
        "gpu_metadata": hardware,
        "content_saved": False,
        "limitations": [
            "Synthetic fixed prompt; prompt and completion text are never written.",
            "Client queue wait is generated by this benchmark semaphore, not a server queue metric.",
            "Gateway versus direct p50 is an exploratory difference, not isolated overhead attribution.",
            "Cancellation recovery is exercised separately by make demo-gateway-cancellation.",
        ],
        "phases": phases,
    }
    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output, 0o700)
    path = output / "gateway-benchmark.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    path.chmod(0o600)
    print(json.dumps({"output": str(path), "phases": list(phases), "content_saved": False}))
    return report


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--gateway-url", action="append", default=[])
    result.add_argument("--gateway-model", default="chat-default")
    result.add_argument("--direct-url")
    result.add_argument("--direct-model", default="gpu-default")
    result.add_argument("--model-revision", default=os.getenv("GPU_MODEL_REVISION"))
    result.add_argument("--identity-file", type=Path, default=Path(".local/identity/tokens.json"))
    result.add_argument("--output-dir", type=Path, default=Path(".local/gpu-lab/gateway-benchmark"))
    result.add_argument("--requests", type=int, default=18)
    result.add_argument("--concurrency", type=int, default=6)
    result.add_argument("--timeout", type=float, default=15)
    result.add_argument("--require-l4", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    return result


if __name__ == "__main__":
    arguments = parser().parse_args()
    if not arguments.gateway_url:
        parser().error("supply at least one --gateway-url")
    if arguments.requests < 3 or arguments.requests > 60:
        parser().error("--requests must be between 3 and 60")
    if arguments.concurrency < 2 or arguments.concurrency > 16:
        parser().error("--concurrency must be between 2 and 16")
    if arguments.timeout <= 0 or arguments.timeout > 15:
        parser().error("--timeout must be above zero and at most 15 seconds")
    for value in [*arguments.gateway_url, *([arguments.direct_url] if arguments.direct_url else [])]:
        parsed = urlparse(value)
        if parsed.scheme != "https" and not (
            parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1", "::1", "vllm"}
        ):
            parser().error("use HTTPS, loopback HTTP, or the internal Compose host vllm")
    result = asyncio.run(run(arguments))
    if arguments.dry_run:
        print(json.dumps(result, indent=2))
