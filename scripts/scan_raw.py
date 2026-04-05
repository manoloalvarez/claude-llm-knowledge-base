#!/usr/bin/env python3
"""
Generate a JSON manifest of raw sources and wiki articles for a knowledge wiki project.

Usage:
    python3 scan_raw.py <project_root>

Output: JSON manifest to stdout with raw_files, wiki_articles, delta, and stats.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from utils import extract_frontmatter


def extract_title(content, filepath):
    """Extract title from H1 heading or fall back to filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filepath.stem


def extract_author(content):
    """Extract author from Glasp Kindle metadata format."""
    match = re.search(r"^-\s+Author:\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def word_count(content):
    """Count words in content, excluding frontmatter."""
    text = content
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            text = text[end + 3:]
    return len(text.split())


def scan_directory(base_path, relative_to):
    """Walk a directory and collect .md file info."""
    files = []
    if not base_path.exists():
        return files
    for root, _, filenames in os.walk(base_path, followlinks=True):
        for fname in sorted(filenames):
            if not fname.endswith(".md"):
                continue
            fpath = Path(root) / fname
            try:
                content = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            stat = fpath.stat()
            files.append({
                "path": str(fpath.relative_to(relative_to)),
                "title": extract_title(content, fpath),
                "author": extract_author(content),
                "words": word_count(content),
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
    return files


def scan_wiki(base_path, relative_to):
    """Walk wiki directory and collect article info with frontmatter."""
    articles = []
    if not base_path.exists():
        return articles
    for root, _, filenames in os.walk(base_path, followlinks=True):
        for fname in sorted(filenames):
            if not fname.endswith(".md"):
                continue
            fpath = Path(root) / fname
            try:
                content = fpath.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fm = extract_frontmatter(content)
            stat = fpath.stat()
            articles.append({
                "path": str(fpath.relative_to(relative_to)),
                "title": fm.get("title", extract_title(content, fpath)),
                "sources": fm.get("sources", []),
                "tags": fm.get("tags", []),
                "words": word_count(content),
                "compiled_date": fm.get("compiled_date"),
                "mtime": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            })
    return articles


def compute_delta(raw_files, last_compiled):
    """Split raw files into new, modified, and unchanged based on lastCompiled.

    Note: 'modified' is always empty — distinguishing new vs modified requires
    cross-referencing against existing wiki articles, which is deferred.
    Files newer than lastCompiled go to 'new' (safe: they get reprocessed).
    """
    if last_compiled is None:
        return {"new": [f["path"] for f in raw_files], "modified": [], "unchanged": []}
    try:
        cutoff = datetime.fromisoformat(last_compiled.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return {"new": [f["path"] for f in raw_files], "modified": [], "unchanged": []}

    new, modified, unchanged = [], [], []
    for f in raw_files:
        mtime = datetime.fromisoformat(f["mtime"])
        if mtime > cutoff:
            new.append(f["path"])
        else:
            unchanged.append(f["path"])
    return {"new": new, "modified": modified, "unchanged": unchanged}


def main():
    if len(sys.argv) != 2:
        print("Usage: scan_raw.py <project_root>", file=sys.stderr)
        sys.exit(1)

    root = Path(sys.argv[1]).resolve()
    config_path = root / "wiki.config.json"

    config = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass

    raw_files = scan_directory(root / "raw", root)
    wiki_articles = scan_wiki(root / "wiki", root)

    last_compiled = config.get("lastCompiled")
    delta = compute_delta(raw_files, last_compiled)

    total_raw = len(raw_files)
    total_wiki = len(wiki_articles)
    coverage = total_wiki / total_raw if total_raw > 0 else 0.0

    manifest = {
        "project_root": str(root),
        "raw_files": raw_files,
        "wiki_articles": wiki_articles,
        "delta": delta,
        "stats": {
            "total_raw": total_raw,
            "total_wiki": total_wiki,
            "total_raw_words": sum(f["words"] for f in raw_files),
            "total_wiki_words": sum(a["words"] for a in wiki_articles),
            "coverage": round(coverage, 3),
        }
    }

    json.dump(manifest, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
