"""Bounded authenticated inference checks for the isolated one-L4 Compose host."""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from scripts.gpu_ec2_host_guard import verify_host

REPO = Path(__file__).resolve().parents[1]
TOKEN_FILE = REPO / ".local/identity/tokens.json"
GATEWAYS = ("http://127.0.0.1:8081", "http://127.0.0.1:8082")
TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 256 * 1024


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


OPENER = build_opener(NoRedirect())


def _request(url: str, *, token: str | None = None, body: dict | None = None, extra: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Accept": "application/json"}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    if body is not None:
        headers["Content-Type"] = "application/json"
    if extra:
        headers.update(extra)
    request = Request(url, data=data, headers=headers, method="POST" if body is not None else "GET")
    try:
        with OPENER.open(request, timeout=TIMEOUT_SECONDS) as response:
            response_body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(response_body) > MAX_RESPONSE_BYTES:
                raise RuntimeError("smoke response exceeded the bounded body size")
            return response.status, response_body, response.headers.get("Content-Type", "")
    except HTTPError as error:
        return error.code, b"", error.headers.get("Content-Type", "")


def _tokens(path: Path) -> dict[str, str]:
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError("tenant token file must be owner-only (mode 0600)")
    values = json.loads(path.read_text(encoding="utf-8"))
    keys = ("customer_support", "internal_engineering", "research")
    if any(not isinstance(values.get(key), str) or not values[key] for key in keys):
        raise ValueError("identity file must contain all three GPU-lab tenant tokens")
    return values


def run_smoke(*, token_file: Path = TOKEN_FILE, readiness_only: bool = False) -> dict:
    tokens = _tokens(token_file)
    checks: list[dict[str, object]] = []
    for gateway in GATEWAYS:
        status, _body, _content_type = _request(f"{gateway}/healthz")
        checks.append({"check": "gateway-readiness", "gateway": gateway.rsplit(":", 1)[1], "status": status})
        if status != 200:
            raise RuntimeError("a gateway is not ready")
    status, _body, _content_type = _request("http://127.0.0.1:8000/health")
    checks.append({"check": "vllm-readiness", "status": status})
    if status != 200:
        raise RuntimeError("vLLM is not ready")
    if readiness_only:
        return {"passed": True, "checks": checks, "inference_requests": 0}

    status, body, _content_type = _request(
        f"{GATEWAYS[0]}/v1/models",
        token=tokens["customer_support"],
        extra={"X-Tenant": "research"},
    )
    models = {item.get("id") for item in json.loads(body).get("data", [])} if status == 200 else set()
    checks.append({"check": "tenant-header-spoof", "status": status})
    if status != 200 or models != {"chat-default"}:
        raise RuntimeError("tenant model list did not remain scoped to its signed identity")

    status, _body, _content_type = _request(
        f"{GATEWAYS[0]}/v1/models", token="invalid-token", extra={"X-Tenant": "research"}
    )
    checks.append({"check": "invalid-identity", "status": status})
    if status != 401:
        raise RuntimeError("invalid identity was not rejected")

    status, _body, _content_type = _request(
        f"{GATEWAYS[0]}/v1/chat/completions",
        token=tokens["customer_support"],
        body={
            "model": "embeddings",
            "messages": [{"role": "user", "content": "synthetic access check"}],
            "max_tokens": 1,
        },
    )
    checks.append({"check": "unauthorized-model", "status": status})
    if status != 403:
        raise RuntimeError("tenant was not denied access to an unauthorized model")

    tenants = ("customer_support", "internal_engineering", "research")
    inference_count = 0
    for index, tenant_key in enumerate(tenants):
        gateway = GATEWAYS[index % len(GATEWAYS)]
        status, body, _content_type = _request(
            f"{gateway}/v1/chat/completions",
            token=tokens[tenant_key],
            body={
                "model": "chat-default",
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "max_tokens": 4,
                "temperature": 0,
            },
        )
        if status != 200:
            raise RuntimeError("authenticated tenant inference failed")
        result = json.loads(body)
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("inference returned an empty completion")
        if result.get("x_backend") != "vllm-single-l4":
            raise RuntimeError("gateway did not report the configured vLLM target")
        usage = result.get("usage", {})
        if not isinstance(usage.get("total_tokens"), int) or usage["total_tokens"] < 1:
            raise RuntimeError("vLLM usage was not reported")
        checks.append({
            "check": "tenant-inference",
            "tenant": tenant_key,
            "gateway": gateway.rsplit(":", 1)[1],
            "status": status,
            "tokens": usage["total_tokens"],
        })
        inference_count += 1

    status, body, content_type = _request(
        f"{GATEWAYS[1]}/v1/chat/completions",
        token=tokens["research"],
        body={
            "model": "chat-default",
            "messages": [{"role": "user", "content": "Reply with OK."}],
            "max_tokens": 4,
            "temperature": 0,
            "stream": True,
            "stream_options": {"include_usage": True},
        },
    )
    if status != 200 or "text/event-stream" not in content_type or b"data: [DONE]" not in body:
        raise RuntimeError("authenticated streaming inference did not complete")
    checks.append({"check": "tenant-stream", "tenant": "research", "gateway": "8082", "status": status})
    inference_count += 1

    return {"passed": True, "checks": checks, "inference_requests": inference_count}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readiness-only", action="store_true")
    parser.add_argument("--wait-seconds", type=int, default=0)
    parser.add_argument("--token-file", type=Path, default=TOKEN_FILE)
    args = parser.parse_args()
    if args.wait_seconds < 0 or args.wait_seconds > 1800:
        parser.error("--wait-seconds must be from 0 to 1800")
    if os.getenv("GPU_EC2_SMOKE_CONFIRM") != "run" and not args.readiness_only:
        parser.error("set GPU_EC2_SMOKE_CONFIRM=run to send the bounded synthetic requests")
    try:
        verify_host(require_l4=True)
        if args.wait_seconds:
            import time

            deadline = time.monotonic() + args.wait_seconds
            while True:
                try:
                    result = run_smoke(token_file=args.token_file, readiness_only=args.readiness_only)
                    break
                except (OSError, RuntimeError, URLError, HTTPError):
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(5)
        else:
            result = run_smoke(token_file=args.token_file, readiness_only=args.readiness_only)
    except (OSError, ValueError, RuntimeError, URLError, HTTPError, KeyError, json.JSONDecodeError) as error:
        print(f"GPU inference smoke failed: {type(error).__name__}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
