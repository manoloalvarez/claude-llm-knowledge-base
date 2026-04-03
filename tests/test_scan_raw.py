#!/usr/bin/env python3
"""Tests for scan_raw.py manifest generation."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path.home() / ".claude" / "skills" / "knowledge-wiki" / "scripts" / "scan_raw.py")


def make_project(tmp, raw_files=None, wiki_files=None, config=None):
    """Create a minimal wiki project structure in tmp dir."""
    root = Path(tmp)
    (root / "raw" / "kindle").mkdir(parents=True)
    (root / "wiki" / "concepts").mkdir(parents=True)

    if config is None:
        config = {"name": "test", "language": "en", "defaultEngine": "codex",
                  "sources": [], "lastCompiled": None, "compilationCount": 0}
    (root / "wiki.config.json").write_text(json.dumps(config), encoding="utf-8")

    for name, content in (raw_files or {}).items():
        p = root / "raw" / "kindle" / name
        p.write_text(content, encoding="utf-8")

    for name, content in (wiki_files or {}).items():
        p = root / "wiki" / "concepts" / name
        p.write_text(content, encoding="utf-8")

    return root


def run_scan(project_root):
    result = subprocess.run(
        [sys.executable, SCRIPT, str(project_root)],
        capture_output=True, text=True
    )
    assert result.returncode == 0, f"scan_raw.py failed: {result.stderr}"
    return json.loads(result.stdout)


def test_empty_project():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_project(tmp)
        manifest = run_scan(root)
        assert manifest["raw_files"] == []
        assert manifest["wiki_articles"] == []
        assert manifest["stats"]["total_raw"] == 0
        assert manifest["stats"]["total_wiki"] == 0
        assert manifest["stats"]["coverage"] == 0.0


def test_raw_files_detected():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_project(tmp, raw_files={
            "Ego Is the Enemy.md": "# Ego Is the Enemy\n\n### Metadata\n\n- Author: Ryan Holiday\n\n### Highlights & Notes\n\n> Some quote\n> Another quote\n",
            "Zero to One.md": "# Zero to One\n\nSome content here with words.\n",
        })
        manifest = run_scan(root)
        assert manifest["stats"]["total_raw"] == 2
        titles = {f["title"] for f in manifest["raw_files"]}
        assert "Ego Is the Enemy" in titles
        assert "Zero to One" in titles
        # Check author detection for kindle format
        ego = next(f for f in manifest["raw_files"] if f["title"] == "Ego Is the Enemy")
        assert ego["author"] == "Ryan Holiday"


def test_delta_all_new():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_project(tmp, raw_files={
            "Book.md": "# Book\n\nContent\n",
        })
        manifest = run_scan(root)
        assert len(manifest["delta"]["new"]) == 1
        assert len(manifest["delta"]["modified"]) == 0
        assert len(manifest["delta"]["unchanged"]) == 0


def test_delta_with_last_compiled():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_project(tmp, raw_files={
            "Old Book.md": "# Old Book\n\nContent\n",
        }, config={
            "name": "test", "language": "en", "defaultEngine": "codex",
            "sources": [], "lastCompiled": "2099-01-01T00:00:00Z",
            "compilationCount": 1
        })
        manifest = run_scan(root)
        assert len(manifest["delta"]["new"]) == 0
        assert len(manifest["delta"]["unchanged"]) == 1


def test_wiki_articles_detected():
    with tempfile.TemporaryDirectory() as tmp:
        root = make_project(tmp, wiki_files={
            "stoic-discipline.md": "---\ntitle: Stoic Discipline\ntags: [stoicism]\nsources:\n  - \"[[raw/kindle/Ego Is the Enemy]]\"\ncompiled_date: 2026-04-03\n---\n\nArticle content here.\n",
        })
        manifest = run_scan(root)
        assert manifest["stats"]["total_wiki"] == 1
        article = manifest["wiki_articles"][0]
        assert article["title"] == "Stoic Discipline"
        assert article["compiled_date"] == "2026-04-03"
        assert article["sources"] == ["[[raw/kindle/Ego Is the Enemy]]"]


if __name__ == "__main__":
    test_empty_project()
    test_raw_files_detected()
    test_delta_all_new()
    test_delta_with_last_compiled()
    test_wiki_articles_detected()
    print("All tests passed!")
