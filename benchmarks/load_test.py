"""Async benchmark client. Local mock values are platform-smoke results, never GPU claims."""

import argparse
import asyncio
import csv
import json
import statistics
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx


async def one(client, url):
    start = perf_counter()
    response = await client.post(
        f"{url}/v1/chat/completions",
        headers={"Authorization": "Bearer local-search-token"},
        json={
            "model": "chat-default",
            "messages": [{"role": "user", "content": "benchmark prompt"}],
            "max_tokens": 16,
        },
    )
    return (
        (perf_counter() - start) * 1000,
        response.status_code,
        response.json().get("usage", {}).get("total_tokens", 0),
    )


async def run(args):
    async with httpx.AsyncClient(timeout=20) as client:
        results = await asyncio.gather(*[one(client, args.url) for _ in range(args.requests)])
    latency = [x[0] for x in results]
    tokens = sum(x[2] for x in results)
    ok = sum(x[1] == 200 for x in results)
    report = {
        "timestamp": datetime.now(UTC).isoformat(),
        "mode": "local-mock",
        "gpu": "not executed",
        "concurrency": args.concurrency,
        "requests": args.requests,
        "success": ok,
        "error_rate": 1 - ok / args.requests,
        "e2e_latency_ms": {
            "p50": statistics.median(latency),
            "p95": sorted(latency)[int(0.95 * (len(latency) - 1))],
            "p99": sorted(latency)[int(0.99 * (len(latency) - 1))],
        },
        "total_tokens": tokens,
        "warning": "TTFT/TPOT/GPU metrics are unavailable for mock backend.",
    }
    Path(args.output).mkdir(parents=True, exist_ok=True)
    Path(args.output, "report.json").write_text(json.dumps(report, indent=2))
    with Path(args.output, "report.csv").open("w") as f:
        csv.writer(f).writerows([["latency_ms", "status", "tokens"], *results])
    Path(args.output, "report.md").write_text(
        "# Benchmark report\n\n```json\n" + json.dumps(report, indent=2) + "\n```\n"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8080")
    p.add_argument("--requests", type=int, default=10)
    p.add_argument("--concurrency", type=int, default=1)
    p.add_argument("--output", default="benchmark-results/local")
    asyncio.run(run(p.parse_args()))
