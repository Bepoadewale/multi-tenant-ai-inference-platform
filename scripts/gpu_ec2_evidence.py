"""Collect a small private host snapshot without copying prompts, tokens, or logs."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from scripts.gpu_ec2_host_guard import verify_host

ROOT = Path(__file__).resolve().parents[1]


def _run(command: list[str], *, timeout: int = 15) -> dict[str, object]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"ok": False, "error_class": type(error).__name__}
    if result.returncode:
        return {"ok": False, "exit_code": result.returncode}
    return {"ok": True, "output": result.stdout.strip()}


def collect(destination: Path | None = None) -> Path:
    identity = verify_host(require_l4=True)
    now = datetime.now(UTC)
    if destination is None:
        destination = Path("/var/tmp/gpu-lab/evidence") / now.strftime("%Y%m%dT%H%M%S.%fZ")
    destination = destination.resolve()
    if destination.is_relative_to(ROOT.resolve()):
        raise ValueError("evidence directory must be outside the public repository")
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.chmod(destination, 0o700)
    commands = {
        "kernel": ["uname", "-srvm"],
        "host_memory": ["free", "-h"],
        "root_disk": ["df", "-h", "/"],
        "gpu": [
            "nvidia-smi",
            "--query-gpu=name,driver_version,memory.total,memory.used,utilization.gpu,temperature.gpu,power.draw",
            "--format=csv,noheader",
        ],
        "cuda_toolkit": ["nvcc", "--version"],
        "docker_version": ["docker", "version", "--format", "{{.Server.Version}}"],
    }
    captured = {name: _run(command) for name, command in commands.items()}
    compose = [
        "docker", "compose", "--env-file", str(ROOT / "deployments/single-gpu/.env"),
        "-f", str(ROOT / "deployments/single-gpu/compose.yaml"), "ps", "--format", "json",
    ]
    ps = _run(compose)
    service_status = []
    if ps["ok"]:
        raw = str(ps["output"])
        try:
            parsed = json.loads(raw)
            rows = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            rows = []
            for line in raw.splitlines():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            service_status.append({
                "service": row.get("Service"),
                "state": row.get("State"),
                "health": row.get("Health"),
            })
    captured["compose_services"] = {"ok": bool(ps["ok"]), "services": service_status}
    captured["readiness_http_status"] = {}
    from urllib.error import HTTPError, URLError
    from urllib.request import HTTPRedirectHandler, Request, build_opener

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, request, response, code, message, headers, new_url):
            return None

    opener = build_opener(NoRedirect())
    for name, url in (
        ("vllm", "http://127.0.0.1:8000/health"),
        ("gateway_1", "http://127.0.0.1:8081/healthz"),
        ("gateway_2", "http://127.0.0.1:8082/healthz"),
    ):
        try:
            with opener.open(Request(url), timeout=5) as response:
                status = response.status
        except HTTPError as error:
            status = error.code
        except URLError:
            status = None
        captured["readiness_http_status"][name] = status

    record = {
        "captured_at_utc": now.isoformat(),
        "source_commit": _run(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        "region": identity["region"],
        "instance_type": identity["instance_type"],
        "gpu": identity["gpu"],
        "evidence_scope": "sanitized host/version/device/service status; no application logs or request content",
        "commands": captured,
    }
    output = destination / "host-snapshot.json"
    fd = os.open(output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as file:
        json.dump(record, file, indent=2)
        file.write("\n")
    return output


def main() -> int:
    try:
        path = collect(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f"evidence capture failed: {type(error).__name__}", file=sys.stderr)
        return 1
    print(f"Sanitized host evidence written privately: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
