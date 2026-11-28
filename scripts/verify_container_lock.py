"""Check that every container runtime input has a hash-locked version."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "requirements-container.txt"
LOCK = ROOT / "requirements-container.lock"
PACKAGE_LINE = re.compile(r"^([A-Za-z0-9_.-]+)==[^\s;]+(?:\s*;.*)?(?:\s+\\)?$")
DIRECT_LINE = re.compile(r"^([A-Za-z0-9_.-]+)(?:\[[^]]+\])?")


def normalized(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def main() -> int:
    direct = {
        normalized(match.group(1))
        for line in INPUT.read_text(encoding="utf-8").splitlines()
        if (match := DIRECT_LINE.match(line.strip()))
    }
    locked: set[str] = set()
    missing_hash: list[str] = []
    current: str | None = None
    hashes: set[str] = set()

    def finish() -> None:
        if current and not hashes:
            missing_hash.append(current)

    for line in LOCK.read_text(encoding="utf-8").splitlines():
        match = PACKAGE_LINE.match(line.strip())
        if match:
            finish()
            current = normalized(match.group(1))
            if current in locked:
                raise SystemExit(f"duplicate locked package: {current}")
            locked.add(current)
            hashes = set()
            continue
        if current and line.strip().startswith("--hash=sha256:"):
            hashes.add(line.strip().removeprefix("--hash=sha256:"))
    finish()

    missing = sorted(direct - locked)
    if missing or missing_hash:
        if missing:
            print("unlocked direct requirements: " + ", ".join(missing))
        if missing_hash:
            print("locked packages without hashes: " + ", ".join(missing_hash))
        return 1
    print(f"container dependency lock covers {len(locked)} pinned packages with hashes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
