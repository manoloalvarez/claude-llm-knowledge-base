#!/usr/bin/env python3
"""Tests for obsidian_post_compile.py frontmatter extraction."""

import sys
from pathlib import Path

# Import the module directly for unit testing
sys.path.insert(0, "/Users/manolo/.claude/skills/knowledge-wiki/scripts")
from obsidian_post_compile import extract_frontmatter, rebuild_moc

import tempfile


def test_extract_frontmatter_inline_list():
    content = '---\ntitle: Stoic Discipline\ntags: [stoicism, discipline]\nsources:\n  - "[[raw/kindle/Ego Is the Enemy]]"\ncompiled_date: 2026-04-03\n---\n\nBody.\n'
    fm = extract_frontmatter(content)
    assert fm["title"] == "Stoic Discipline"
    assert fm["tags"] == ["stoicism", "discipline"]
    assert fm["compiled_date"] == "2026-04-03"
    assert len(fm["sources"]) == 1


def test_extract_frontmatter_no_frontmatter():
    content = "# Just a heading\n\nSome content.\n"
    fm = extract_frontmatter(content)
    assert fm == {}


def test_rebuild_moc():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "wiki" / "concepts").mkdir(parents=True)
        (root / "wiki" / "authors").mkdir(parents=True)
        (root / "wiki" / "concepts" / "stoic-discipline.md").write_text("---\ntitle: Stoic Discipline\n---\n\nContent.\n")
        (root / "wiki" / "authors" / "ryan-holiday.md").write_text("---\ntitle: Ryan Holiday\n---\n\nContent.\n")

        result = rebuild_moc(str(root), None)
        assert result is True

        moc = (root / "MOC - Knowledge Wiki.md").read_text()
        assert "## Concepts" in moc
        assert "## Authors" in moc
        assert "stoic-discipline" in moc
        assert "ryan-holiday" in moc


if __name__ == "__main__":
    test_extract_frontmatter_inline_list()
    test_extract_frontmatter_no_frontmatter()
    test_rebuild_moc()
    print("All tests passed!")
