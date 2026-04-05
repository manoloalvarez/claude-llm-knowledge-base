#!/usr/bin/env python3
"""
Set Obsidian properties on newly ingested raw files.

Usage:
    echo '{"vault": "...", "files": [...]}' | python3 obsidian_ingest.py

Input JSON:
{
  "vault": "vault-name",
  "files": [
    {
      "path": "raw/kindle/Book Title.md",
      "source_url": "https://...",    (optional)
      "source_type": "kindle-highlights",
      "title": "Book Title",
      "author": "Author Name"         (optional)
    }
  ]
}

Output: JSON summary to stdout.
"""

import json
import subprocess
import sys
from datetime import date


def run_obsidian(args):
    """Run an obsidian CLI command. Returns (success, stdout)."""
    try:
        result = subprocess.run(
            ["obsidian"] + args,
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, str(e)


def set_property(file_name, name, value, prop_type, vault):
    """Set a single Obsidian property on a file."""
    args = ["property:set", f'file={file_name}', f"name={name}", f"value={value}", f"type={prop_type}"]
    if vault:
        args.append(f'vault={vault}')
    return run_obsidian(args)


def ingest_file(file_info, vault):
    """Set properties on a single ingested file."""
    title = file_info.get("title", "Unknown")
    results = []
    today = date.today().isoformat()

    # Set ingested_date
    ok, _ = set_property(title, "ingested_date", today, "date", vault)
    results.append({"property": "ingested_date", "success": ok})

    # Set source_type
    source_type = file_info.get("source_type", "markdown")
    ok, _ = set_property(title, "source_type", source_type, "text", vault)
    results.append({"property": "source_type", "success": ok})

    # Set source_url if present
    if file_info.get("source_url"):
        ok, _ = set_property(title, "source_url", file_info["source_url"], "text", vault)
        results.append({"property": "source_url", "success": ok})

    # Set author if present
    if file_info.get("author"):
        ok, _ = set_property(title, "author", file_info["author"], "text", vault)
        results.append({"property": "author", "success": ok})

    return {"file": title, "properties": results}


def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    vault = data.get("vault")
    files = data.get("files", [])

    if not files:
        print("Error: No files provided", file=sys.stderr)
        sys.exit(1)

    results = []
    for file_info in files:
        result = ingest_file(file_info, vault)
        results.append(result)

    summary = {
        "files_processed": len(results),
        "results": results,
    }

    json.dump(summary, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
