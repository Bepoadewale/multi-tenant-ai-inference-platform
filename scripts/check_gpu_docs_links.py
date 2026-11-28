"""Check relative Markdown links and heading fragments in selected project docs."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK = re.compile(r"(?<!!)\[[^\]]*\]\((<[^>]+>|[^)]+)\)")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")


def _slug(text: str) -> str:
    """Create the heading fragment format GitHub uses for ordinary headings."""
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"\s+", "-", text)


def _headings(markdown: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    in_fence = False
    for line in markdown.splitlines():
        if line.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING.match(line)
        if not match:
            continue
        base = _slug(match.group(1))
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def check_files(root: Path, files: list[Path]) -> list[str]:
    """Return missing local Markdown targets with source line numbers."""
    errors: list[str] = []
    for source in files:
        source = source if source.is_absolute() else root / source
        source = source.resolve()
        try:
            text = source.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"{source}: cannot read file ({exc.__class__.__name__})")
            continue

        in_fence = False
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for raw_target in LINK.findall(line):
                target = raw_target.strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                else:
                    target = target.split(maxsplit=1)[0]
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("//"):
                    continue

                path_part = unquote(parsed.path)
                destination = (source.parent / path_part).resolve() if path_part else source
                if path_part and not destination.exists():
                    errors.append(f"{source}:{line_number}: missing local target {path_part}")
                    continue
                if not parsed.fragment or destination.suffix.lower() != ".md":
                    continue
                try:
                    target_text = destination.read_text(encoding="utf-8")
                except OSError:
                    errors.append(f"{source}:{line_number}: cannot read linked file {path_part}")
                    continue
                if unquote(parsed.fragment) not in _headings(target_text):
                    errors.append(
                        f"{source}:{line_number}: missing heading #{parsed.fragment} in {path_part or source.name}"
                    )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path, help="Markdown files to validate")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root")
    args = parser.parse_args(argv)
    errors = check_files(args.root.resolve(), args.files)
    if errors:
        print("Markdown link validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Validated local Markdown links and heading fragments in {len(args.files)} files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
