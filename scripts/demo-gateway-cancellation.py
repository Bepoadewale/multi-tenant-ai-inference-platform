"""Check request cancellation and shared Redis lease cleanup across local gateways."""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[1]
TENANT = "team-search"
LEASE_HASH = f"inference:{{{TENANT}}}:active-leases"
PROMPT = {
    "model": "chat-default",
    "stream": True,
    "messages": [{"role": "user", "content": "good cancellation recovery check"}],
    "max_tokens": 4,
}


def redis_active_lease_count() -> int:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(REPO_ROOT / "docker-compose.yml"),
            "exec",
            "-T",
            "redis",
            "redis-cli",
            "HLEN",
            LEASE_HASH,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    return int(result.stdout.strip())


async def metric_active_requests(client: httpx.AsyncClient, base_url: str) -> float:
    response = await client.get(f"{base_url}/metrics")
    response.raise_for_status()
    pattern = re.compile(
        rf'^inference_gateway_active_requests\{{tenant="{TENANT}"\}}\s+([0-9.eE+-]+)$',
        re.MULTILINE,
    )
    match = pattern.search(response.text)
    return float(match.group(1)) if match else 0.0


async def wait_for_release(client: httpx.AsyncClient, base_url: str) -> None:
    deadline = asyncio.get_running_loop().time() + 3
    while asyncio.get_running_loop().time() < deadline:
        active = await metric_active_requests(client, base_url)
        leases = await asyncio.to_thread(redis_active_lease_count)
        if active == 0 and leases == 0:
            return
        await asyncio.sleep(0.05)
    raise AssertionError(
        f"gateway cancellation did not release shared admission: active={active}, leases={leases}"
    )


async def cancel_stream(client: httpx.AsyncClient, base_url: str, token: str) -> None:
    async with client.stream(
        "POST",
        f"{base_url}/v1/chat/completions",
        headers={"Authorization": f"Bearer {token}"},
        json=PROMPT,
    ) as response:
        if response.status_code != 200:
            raise AssertionError(
                f"gateway returned HTTP {response.status_code} before cancellation"
            )
        async for line in response.aiter_lines():
            if line.startswith("data: ") and line != "data: [DONE]":
                return
        raise AssertionError("stream ended before a cancellable response chunk arrived")


async def main() -> None:
    tokens_path = REPO_ROOT / ".local" / "identity" / "tokens.json"
    token = json.loads(tokens_path.read_text(encoding="utf-8"))["search"]
    gateways = ["http://localhost:8081", "http://localhost:8082"]

    async with httpx.AsyncClient(timeout=5) as client:
        starting_leases = await asyncio.to_thread(redis_active_lease_count)
        if starting_leases != 0:
            raise AssertionError(f"expected a clean test tenant; found {starting_leases} active leases")

        for index in range(10):
            base_url = gateways[index % len(gateways)]
            await cancel_stream(client, base_url, token)
            await wait_for_release(client, base_url)

        response = await client.post(
            f"{gateways[1]}/v1/chat/completions",
            headers={"Authorization": f"Bearer {token}"},
            json={**PROMPT, "stream": False},
        )
        response.raise_for_status()

    print(
        "Cancellation drill passed: 10 client-cancelled streams across both independent "
        "gateways released their process-local active gauges and shared Redis leases."
    )


if __name__ == "__main__":
    asyncio.run(main())
