#!/usr/bin/env python3
"""Minimal standard-library client for the local OpenAI-compatible gateway."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    token = os.getenv("INFERENCE_API_TOKEN")
    if not token:
        print("INFERENCE_API_TOKEN is required; see examples/README.md", file=sys.stderr)
        return 2
    base_url = os.getenv("INFERENCE_BASE_URL", "http://localhost:8081").rstrip("/")
    payload = {
        "model": os.getenv("INFERENCE_MODEL", "chat-default"),
        "messages": [{"role": "user", "content": "good and safe"}],
        "max_tokens": 4,
    }
    request = urllib.request.Request(
        f"{base_url}/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            print(response.read().decode())
    except urllib.error.HTTPError as error:
        print(error.read().decode(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
