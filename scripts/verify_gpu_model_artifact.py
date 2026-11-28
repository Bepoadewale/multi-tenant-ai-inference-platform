#!/usr/bin/env python3
"""Verify the pinned Qwen model file in a Hugging Face Hub cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

MODEL_REPO_ID = "Qwen/Qwen2.5-1.5B-Instruct"
MODEL_REVISION = "989aa7980e4cf806f80c7fef2b1adb7bc71aa306"
MODEL_FILENAME = "model.safetensors"
MODEL_SIZE_BYTES = 3_087_467_144
MODEL_SHA256 = "dd924a11b4c220f385b51ffa522daea7c9f3d850e31b162bb5661df483c6d3ee"


def snapshot_file(cache_dir: Path) -> Path:
    """Return the pinned file path in a Hugging Face Hub cache."""
    repo_cache_name = "models--" + MODEL_REPO_ID.replace("/", "--")
    return cache_dir / repo_cache_name / "snapshots" / MODEL_REVISION / MODEL_FILENAME


def verify_file(path: Path, expected_size: int, expected_sha256: str) -> dict[str, int | str]:
    """Check a regular file or cache symlink without loading it all into memory."""
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise ValueError("expected SHA-256 must contain 64 lowercase hexadecimal characters")
    if expected_size <= 0:
        raise ValueError("expected file size must be positive")
    if not path.is_file():
        raise FileNotFoundError(f"model artifact is missing or not a file: {path.name}")

    digest = hashlib.sha256()
    size_bytes = 0
    with path.open("rb") as artifact:
        for chunk in iter(lambda: artifact.read(8 * 1024 * 1024), b""):
            size_bytes += len(chunk)
            digest.update(chunk)

    actual_sha256 = digest.hexdigest()
    if size_bytes != expected_size:
        raise ValueError(f"model artifact has {size_bytes} bytes; expected {expected_size}")
    if actual_sha256 != expected_sha256:
        raise ValueError("model artifact SHA-256 does not match the pinned value")

    return {"size_bytes": size_bytes, "sha256": actual_sha256}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify the pinned Qwen artifact after it has been downloaded."
    )
    parser.add_argument(
        "--cache-dir",
        required=True,
        type=Path,
        help="Hugging Face Hub cache root, normally $HF_HOME/hub",
    )
    args = parser.parse_args(argv)
    path = snapshot_file(args.cache_dir)

    try:
        result = verify_file(path, MODEL_SIZE_BYTES, MODEL_SHA256)
    except FileNotFoundError:
        print("model artifact verification failed: model artifact is missing or not a file", file=sys.stderr)
        return 1
    except PermissionError:
        print("model artifact verification failed: filesystem permissions prevent reading the artifact", file=sys.stderr)
        return 1
    except OSError as exc:
        print(
            f"model artifact verification failed: filesystem error ({type(exc).__name__})",
            file=sys.stderr,
        )
        return 1
    except ValueError as exc:
        print(f"model artifact verification failed: {exc}", file=sys.stderr)
        return 1

    print(
        json.dumps(
            {
                "repo_id": MODEL_REPO_ID,
                "revision": MODEL_REVISION,
                "filename": MODEL_FILENAME,
                "size_bytes": result["size_bytes"],
                "sha256": result["sha256"],
                "verified": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
