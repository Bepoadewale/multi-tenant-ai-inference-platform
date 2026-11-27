"""Validate the private provenance and credential fields needed for GPU Compose."""

from __future__ import annotations

import re
import stat
import sys
from pathlib import Path


def validate_environment(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise ValueError("GPU Compose environment must be a regular, non-symlink file")
    if stat.S_IMODE(path.stat().st_mode) != 0o600:
        raise ValueError("deployments/single-gpu/.env must have mode 0600")

    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key in values:
            raise ValueError(f"duplicate environment key: {key}")
        values[key] = value

    required = (
        "GPU_MODEL_ARTIFACT_SHA256",
        "GPU_SOURCE_COMMIT",
        "GRAFANA_ADMIN_PASSWORD",
    )
    if any(not values.get(key) or values[key].startswith("replace-") for key in required):
        raise ValueError("GPU model provenance and Grafana password must be configured")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", values["GPU_MODEL_ARTIFACT_SHA256"]):
        raise ValueError("GPU_MODEL_ARTIFACT_SHA256 must be a 64-character SHA-256 hex digest")
    if not re.fullmatch(r"[0-9a-fA-F]{40}", values["GPU_SOURCE_COMMIT"]):
        raise ValueError("GPU_SOURCE_COMMIT must be a 40-character Git commit ID")
    if len(values["GRAFANA_ADMIN_PASSWORD"]) < 32:
        raise ValueError("GRAFANA_ADMIN_PASSWORD must be at least 32 characters")


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise ValueError("provide the private GPU Compose environment path")
        validate_environment(Path(sys.argv[1]))
    except (OSError, ValueError) as error:
        print(f"refusing GPU Compose deployment: {error}", file=sys.stderr)
        return 2
    print("private GPU Compose environment validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
