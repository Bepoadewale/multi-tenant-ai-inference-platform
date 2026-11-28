from __future__ import annotations

from pathlib import Path

from scripts.check_gpu_docs_links import check_files


def test_link_checker_accepts_relative_file_and_heading_links(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# First Heading\n\n# First Heading\n", encoding="utf-8")
    (docs / "index.md").write_text(
        "[guide](guide.md#first-heading-1)\n", encoding="utf-8"
    )

    assert check_files(tmp_path, [Path("docs/index.md")]) == []


def test_link_checker_reports_missing_files_and_heading_fragments(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Existing\n", encoding="utf-8")
    (docs / "index.md").write_text(
        "[missing](absent.md)\n[bad anchor](guide.md#not-here)\n",
        encoding="utf-8",
    )

    errors = check_files(tmp_path, [Path("docs/index.md")])

    assert len(errors) == 2
    assert "missing local target absent.md" in errors[0]
    assert "missing heading #not-here" in errors[1]


def test_link_checker_ignores_links_inside_fenced_code(tmp_path: Path) -> None:
    doc = tmp_path / "guide.md"
    doc.write_text("```markdown\n[example](missing.md)\n```\n", encoding="utf-8")

    assert check_files(tmp_path, [Path("guide.md")]) == []
