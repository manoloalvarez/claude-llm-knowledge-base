#!/usr/bin/env python3
"""
Post-compile batch processing: read frontmatter from new wiki articles,
apply properties via Obsidian CLI, rebuild MOC, check link integrity.

Usage:
    echo '{"project_root": "...", "vault": "...", "files": [...]}' | python3 obsidian_post_compile.py

Input JSON:
{
  "project_root": "/path/to/project",
  "vault": "vault-name",
  "files": ["wiki/concepts/stoic-discipline.md", "wiki/authors/ryan-holiday.md"]
}

Output: JSON summary to stdout.
"""

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from utils import extract_frontmatter


def run_obsidian(args):
    """Run an obsidian CLI command. Returns (success, stdout)."""
    try:
        result = subprocess.run(
            ["obsidian"] + args,
            capture_output=True, text=True, timeout=15
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def set_property(file_name, name, value, prop_type, vault):
    """Set a single Obsidian property."""
    args = ["property:set", f'file={file_name}', f"name={name}", f"value={value}", f"type={prop_type}"]
    if vault:
        args.append(f'vault={vault}')
    return run_obsidian(args)


def process_wiki_file(filepath, project_root, vault):
    """Read a wiki article's frontmatter and apply properties via Obsidian CLI."""
    full_path = Path(project_root) / filepath
    if not full_path.exists():
        return {"file": filepath, "error": "file not found", "properties": []}

    content = full_path.read_text(encoding="utf-8")
    fm = extract_frontmatter(content)
    title = fm.get("title", full_path.stem)
    results = []

    # Apply tags
    tags = fm.get("tags", [])
    if tags:
        tag_str = ",".join(tags) if isinstance(tags, list) else tags
        ok, _ = set_property(title, "tags", tag_str, "tags", vault)
        results.append({"property": "tags", "value": tag_str, "success": ok})

    # Apply compiled_date
    today = date.today().isoformat()
    ok, _ = set_property(title, "compiled_date", today, "date", vault)
    results.append({"property": "compiled_date", "value": today, "success": ok})

    # Apply source_count
    sources = fm.get("sources", [])
    source_count = len(sources) if isinstance(sources, list) else 0
    ok, _ = set_property(title, "source_count", str(source_count), "number", vault)
    results.append({"property": "source_count", "value": source_count, "success": ok})

    # Apply status
    ok, _ = set_property(title, "status", "compiled", "text", vault)
    results.append({"property": "status", "value": "compiled", "success": ok})

    return {"file": filepath, "title": title, "properties": results}


def check_unresolved(vault):
    """Get unresolved links from Obsidian CLI."""
    ok, output = run_obsidian(["unresolved", "--verbose", "format=json"] + ([f'vault={vault}'] if vault else []))
    if ok and output:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output
    return []


def get_tag_distribution(vault):
    """Get tag counts from Obsidian CLI."""
    ok, output = run_obsidian(["tags", "sort=count", "counts", "format=json"] + ([f'vault={vault}'] if vault else []))
    if ok and output:
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            return output
    return []


def rebuild_moc(project_root, vault):
    """Rebuild MOC - Knowledge Wiki.md by scanning wiki/ subdirectories."""
    wiki_dir = Path(project_root) / "wiki"
    if not wiki_dir.exists():
        return False

    sections = {}
    for subdir in sorted(wiki_dir.iterdir()):
        if not subdir.is_dir():
            continue
        category = subdir.name.replace("-", " ").title()
        articles = []
        for md_file in sorted(subdir.glob("*.md")):
            name = md_file.stem.replace("-", " ").title()
            articles.append(f"- [[wiki/{subdir.name}/{md_file.stem}|{name}]]")
        if articles:
            sections[category] = articles

    if not sections:
        return False

    content = "# Knowledge Wiki\n\nAuto-generated Map of Content.\n"
    for category, articles in sections.items():
        content += f"\n## {category}\n\n"
        content += "\n".join(articles) + "\n"

    moc_path = Path(project_root) / "MOC - Knowledge Wiki.md"
    moc_path.write_text(content, encoding="utf-8")
    return True


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    project_root = data.get("project_root")
    vault = data.get("vault")
    files = data.get("files", [])

    if not project_root:
        print("Error: project_root required", file=sys.stderr)
        sys.exit(1)

    # Process each wiki file
    file_results = []
    for filepath in files:
        result = process_wiki_file(filepath, project_root, vault)
        file_results.append(result)

    # Check unresolved links
    unresolved = check_unresolved(vault)

    # Get tag distribution
    tags = get_tag_distribution(vault)

    # Rebuild MOC
    moc_rebuilt = rebuild_moc(project_root, vault)

    summary = {
        "files_processed": len(file_results),
        "file_results": file_results,
        "unresolved_links": unresolved,
        "tag_distribution": tags,
        "moc_rebuilt": moc_rebuilt,
    }

    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
