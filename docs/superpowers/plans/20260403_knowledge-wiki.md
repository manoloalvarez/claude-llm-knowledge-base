# Knowledge Wiki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `/knowledge-wiki` skill that compiles raw source directories into structured Obsidian wikis using any LLM engine (Codex/Claude/Gemini).

**Architecture:** Skill-only. SKILL.md defines all commands. Claude orchestrates pipelines: scripts for manifest/batch operations, engine dispatch for LLM compilation, Obsidian CLI for vault management and tagging.

**Tech Stack:** Python 3 scripts, Obsidian CLI v1.12+, Claude Code skills system, `/codex:rescue` + `gemini` CLI + native Claude for engine dispatch.

**Spec:** `docs/superpowers/specs/20260403_knowledge-wiki-design.md`

---

## File Structure

```
/Users/manolo/.claude/skills/knowledge-wiki/
├── SKILL.md                                  ← orchestration: all commands, pipelines, engine dispatch
├── scripts/
│   ├── scan_raw.py                           ← walk raw/ + wiki/, compute manifest + delta
│   ├── obsidian_ingest.py                    ← set properties on new raw files via obsidian CLI
│   └── obsidian_post_compile.py              ← batch tag/property/MOC update via obsidian CLI
└── references/
    ├── program-template.md                   ← PROGRAM.md template with {{placeholders}}
    ├── compilation-prompts.md                ← engine-agnostic prompt templates (compile, query, health)
    └── wiki-structure.md                     ← directory conventions, naming rules, frontmatter schema
```

---

### Task 1: Create reference files

These are static documentation/template files that the skill and engines reference. No executable code.

**Files:**
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/references/wiki-structure.md`
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/references/program-template.md`
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/references/compilation-prompts.md`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p /Users/manolo/.claude/skills/knowledge-wiki/scripts
mkdir -p /Users/manolo/.claude/skills/knowledge-wiki/references
```

- [ ] **Step 2: Create wiki-structure.md**

Create `/Users/manolo/.claude/skills/knowledge-wiki/references/wiki-structure.md` with the directory layout conventions, naming rules (slug format for filenames, title case in frontmatter), frontmatter schema for each article type (concept, author, theme, connection), and Obsidian property types used (tags, date, number, text).

Content must cover:
- Project directory layout (raw/, wiki/, outputs/)
- wiki.config.json schema with all fields documented
- Slug naming: lowercase, hyphens, no special characters (e.g., `stoic-discipline.md`)
- Frontmatter schema per article type:
  - **Concept:** title, aliases, tags, sources (wikilinks list), related (wikilinks list), compiled_date
  - **Author:** title, tags, books (wikilinks list), compiled_date
  - **Theme:** title, tags, sources (wikilinks list), concepts (wikilinks list), compiled_date
  - **Connection:** title, tags, concepts (wikilinks list), compiled_date
- Obsidian property type mapping: tags→tags, compiled_date→date, source_count→number, status→text

- [ ] **Step 3: Create program-template.md**

Create `/Users/manolo/.claude/skills/knowledge-wiki/references/program-template.md` with the full PROGRAM.md template from the spec. Use `{{name}}`, `{{language}}`, `{{source_count}}`, `{{source_groups}}`, `{{source_types_section}}` as placeholders. Include:
- Project header with name/language/stats
- Directory layout rules (raw/ read-only, wiki/ writable, MOC updates)
- Source type parsing hints section (one block per `{{source_type}}`)
- Compilation rules (9 rules from spec)
- Frontmatter schema (reference wiki-structure.md format)
- Quality standards (concept 500+ words, author bio + summaries, theme 5+ sources, connection explains WHY)
- Compilation modes (FULL, INCREMENTAL, TOPIC)

Include these source type hint blocks that get included conditionally:

**kindle-highlights:**
```
Files follow Glasp Kindle export format:
- H1 = book title
- ### Metadata section: Title, Author, Book URL, Kindle link, Last Updated
- ### Highlights & Notes section: blockquoted passages (> ...)
Extract: book title, author name, all highlighted passages with context.
```

**markdown:**
```
Generic markdown files. Extract title from H1 or filename.
Parse any YAML frontmatter for metadata. Content is the full file body.
```

**pdf:**
```
PDF files. Extract text content. Title from first heading or filename.
```

**mixed:**
```
Mixed file types. Detect format per-file and extract accordingly.
```

- [ ] **Step 4: Create compilation-prompts.md**

Create `/Users/manolo/.claude/skills/knowledge-wiki/references/compilation-prompts.md` with four prompt templates:

**Compile prompt:**
```
You are a knowledge wiki compiler. Your working directory is {{project_root}}.

Read PROGRAM.md for full compilation instructions.

Mode: {{scope}}
Language: {{language}}

{{#if manifest}}
Manifest (files to process):
{{manifest_json}}
{{/if}}

{{#if topic}}
Topic filter: {{topic}}
Only process files related to this topic.
{{/if}}

Compile the wiki:
1. Read all files in scope from raw/
2. Identify concepts, themes, authors, and connections
3. Create or update .md articles in wiki/ with proper [[wikilinks]] and YAML frontmatter
4. Update MOC - Knowledge Wiki.md with links to all articles

Write files directly to the wiki/ directory. Do NOT modify anything in raw/.
```

**Query prompt:**
```
You are a knowledge researcher. Your working directory is {{project_root}}.

Read PROGRAM.md for context about this knowledge wiki.

Question: {{question}}

Relevant articles found by search:
{{search_results}}

Research this question by reading the relevant wiki articles and raw sources.
Synthesize a comprehensive answer with citations using [[wikilinks]].

{{#if format_slides}}
Output as a Marp slide deck (--- between slides, marp: true in frontmatter).
Save to outputs/slides/{{date}}_{{slug}}.md
{{/if}}
{{#if format_md}}
Output as a markdown report.
Save to outputs/reports/{{date}}_{{slug}}.md
{{/if}}
{{#if format_terminal}}
Output your answer directly. Do not save to file.
{{/if}}
```

**Health prompt:**
```
You are a knowledge wiki quality analyst. Your working directory is {{project_root}}.

Read PROGRAM.md for context about this knowledge wiki.

Structural analysis from Obsidian CLI:
{{structural_results}}

Your task:
1. Read wiki articles and find INCONSISTENT information across articles
2. Suggest NEW CONNECTIONS between concepts that are not yet linked
3. Identify CANDIDATE TOPICS for new articles based on coverage gaps
4. Flag information that could be ENRICHED with web research
5. Rate overall wiki COHERENCE (1-10) with justification

Save your report to outputs/reports/{{date}}_health.md
```

**Enrich prompt (for web-researcher):**
```
Research the following knowledge gap identified in a wiki health check:

Gap: {{gap_description}}
Wiki context: {{wiki_context}}

Provide comprehensive information that could fill this gap.
Focus on factual, well-sourced content.
```

- [ ] **Step 5: Initialize git repo and commit**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git init
git add docs/superpowers/ .claude/skills/knowledge-wiki/references/
git commit -m "feat: add knowledge-wiki design spec and reference files"
```

---

### Task 2: Create scan_raw.py

The manifest generator. Pure filesystem logic — no Obsidian CLI dependency. Fully testable.

**Files:**
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/scripts/scan_raw.py`

- [ ] **Step 1: Write the test**

Create `/Users/manolo/dev/ai-tools/knowledge-wikis/tests/test_scan_raw.py`:

```python
#!/usr/bin/env python3
"""Tests for scan_raw.py manifest generation."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = str(Path(__file__).resolve().parents[1] / ".claude" / "skills" / "knowledge-wiki" / "scripts" / "scan_raw.py")


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
        assert "compiled_date" in article


if __name__ == "__main__":
    test_empty_project()
    test_raw_files_detected()
    test_delta_all_new()
    test_delta_with_last_compiled()
    test_wiki_articles_detected()
    print("All tests passed!")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
python3 tests/test_scan_raw.py
```

Expected: FAIL — `scan_raw.py` doesn't exist yet.

- [ ] **Step 3: Implement scan_raw.py**

Create `/Users/manolo/.claude/skills/knowledge-wiki/scripts/scan_raw.py`:

```python
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


def extract_title(content, filepath):
    """Extract title from H1 heading or fall back to filename."""
    match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filepath.stem


def extract_author(content):
    """Extract author from Glasp Kindle metadata format."""
    match = re.search(r"^-\s+Author:\s+(.+)$", content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def extract_frontmatter(content):
    """Extract YAML frontmatter as a dict. Returns empty dict if none."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line and not line.startswith("-") and not line.startswith("#"):
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
            result[key] = value
    return result


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
    """Split raw files into new, modified, and unchanged based on lastCompiled."""
    if last_compiled is None:
        return {"new": [f["path"] for f in raw_files], "modified": [], "unchanged": []}
    try:
        cutoff = datetime.fromisoformat(last_compiled)
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
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
python3 tests/test_scan_raw.py
```

Expected: "All tests passed!"

- [ ] **Step 5: Test against real Kindle highlights**

```bash
# Create a temporary project pointing at real data
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/raw/kindle" "$TMPDIR/wiki/concepts"
ln -s "/Users/manolo/Documents/Documents - Manolos MacBook Pro/notas-libros/raw-highlights" "$TMPDIR/raw/kindle/highlights"
echo '{"name":"test","language":"en","defaultEngine":"codex","sources":[],"lastCompiled":null,"compilationCount":0}' > "$TMPDIR/wiki.config.json"
python3 /Users/manolo/.claude/skills/knowledge-wiki/scripts/scan_raw.py "$TMPDIR" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Raw: {d[\"stats\"][\"total_raw\"]} files, {d[\"stats\"][\"total_raw_words\"]} words')"
rm -rf "$TMPDIR"
```

Expected: "Raw: 246 files, NNNNN words" (some large word count).

- [ ] **Step 6: Commit**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git add .claude/skills/knowledge-wiki/scripts/scan_raw.py tests/test_scan_raw.py
git commit -m "feat: add scan_raw.py manifest generator with tests"
```

---

### Task 3: Create obsidian_ingest.py

Sets properties on newly ingested raw files via Obsidian CLI.

**Files:**
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/scripts/obsidian_ingest.py`

- [ ] **Step 1: Implement obsidian_ingest.py**

Create `/Users/manolo/.claude/skills/knowledge-wiki/scripts/obsidian_ingest.py`:

```python
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
```

- [ ] **Step 2: Manual verification**

This script depends on Obsidian CLI, so we verify manually against a real vault:

```bash
echo '{"vault": "notas-libros", "files": [{"path": "raw-highlights/Ego Is the Enemy.md", "source_type": "kindle-highlights", "title": "Ego Is the Enemy", "author": "Ryan Holiday"}]}' | python3 /Users/manolo/.claude/skills/knowledge-wiki/scripts/obsidian_ingest.py
```

Expected: JSON output with `files_processed: 1` and property set results. Verify with:

```bash
obsidian property:read file="Ego Is the Enemy" name=source_type vault="notas-libros"
```

Expected: `kindle-highlights`

Then clean up the test property:

```bash
obsidian property:remove file="Ego Is the Enemy" name=source_type vault="notas-libros"
obsidian property:remove file="Ego Is the Enemy" name=ingested_date vault="notas-libros"
obsidian property:remove file="Ego Is the Enemy" name=author vault="notas-libros"
```

- [ ] **Step 3: Commit**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git add .claude/skills/knowledge-wiki/scripts/obsidian_ingest.py
git commit -m "feat: add obsidian_ingest.py for property setting on raw files"
```

---

### Task 4: Create obsidian_post_compile.py

Batch post-processing after engine writes wiki articles: reads frontmatter, applies properties, rebuilds MOC, checks links.

**Files:**
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/scripts/obsidian_post_compile.py`

- [ ] **Step 1: Implement obsidian_post_compile.py**

Create `/Users/manolo/.claude/skills/knowledge-wiki/scripts/obsidian_post_compile.py`:

```python
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


def extract_frontmatter(content):
    """Extract YAML frontmatter as key-value pairs."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    fm_text = content[3:end].strip()
    result = {}
    current_key = None
    current_list = None
    for line in fm_text.split("\n"):
        stripped = line.strip()
        # List item under a key
        if stripped.startswith("- ") and current_key:
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip().strip('"').strip("'"))
            result[current_key] = current_list
            continue
        # Inline list: key: [a, b, c]
        if ":" in stripped and not stripped.startswith("-") and not stripped.startswith("#"):
            if current_key and current_list is not None:
                current_list = None
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            current_key = key
            if value.startswith("[") and value.endswith("]"):
                result[key] = [v.strip().strip('"').strip("'") for v in value[1:-1].split(",") if v.strip()]
                current_list = result[key]
            elif value:
                result[key] = value
                current_list = None
            else:
                current_list = []
    return result


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
```

- [ ] **Step 2: Test frontmatter extraction in isolation**

Add to `/Users/manolo/dev/ai-tools/knowledge-wikis/tests/test_post_compile.py`:

```python
#!/usr/bin/env python3
"""Tests for obsidian_post_compile.py frontmatter extraction."""

import sys
from pathlib import Path

# Import the module directly for unit testing
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / ".claude" / "skills" / "knowledge-wiki" / "scripts"))
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
```

- [ ] **Step 3: Run tests**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
python3 tests/test_post_compile.py
```

Expected: "All tests passed!"

- [ ] **Step 4: Commit**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git add .claude/skills/knowledge-wiki/scripts/obsidian_post_compile.py tests/test_post_compile.py
git commit -m "feat: add obsidian_post_compile.py for batch tagging and MOC rebuild"
```

---

### Task 5: Create SKILL.md

The main skill file that ties everything together. This is the orchestration brain.

**Files:**
- Create: `/Users/manolo/.claude/skills/knowledge-wiki/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

Create `/Users/manolo/.claude/skills/knowledge-wiki/SKILL.md` with the full skill definition. This is the largest file — it contains:

**Frontmatter:**
```yaml
---
name: knowledge-wiki
description: >
  Build and maintain LLM-compiled knowledge wikis from raw sources.
  Point at any directory (Kindle highlights, articles, papers, notes)
  and compile a structured Obsidian wiki with concepts, cross-references,
  backlinks, and MOCs. Engine-agnostic: Codex (default), Claude, or Gemini.
  Uses Obsidian CLI for vault management, tagging, and health analysis.
  Triggers: 'knowledge wiki', 'knowledge base', 'compile wiki',
  'wiki from sources', 'build knowledge base', 'karpathy wiki'.
---
```

**Body must include:**

1. **Overview** — one-paragraph description of what this skill does
2. **Prerequisites** — Obsidian CLI v1.12+ installed and running, at least one engine available
3. **Project detection** — how to find the wiki project (walk up from cwd looking for `wiki.config.json`)
4. **Engine configuration** — table of engines with dispatch methods:
   - Codex: `/codex:rescue --effort high "<prompt>"`
   - Claude: native (read files with Read tool, write with Write tool)
   - Gemini: `gemini -p '<prompt>'` via Bash
   - Default from wiki.config.json, overridable with `--engine`
5. **Command: init** — full step-by-step with Obsidian CLI commands, script calls, source type detection logic
6. **Command: ingest** — URL detection (starts with http), WebFetch usage, file/dir handling, `obsidian_ingest.py` call
7. **Command: compile** — full pipeline: scan_raw.py → build prompt from references/compilation-prompts.md → dispatch to engine → obsidian_post_compile.py → update config
8. **Command: query** — Obsidian search → build prompt → dispatch → save output
9. **Command: health** — Phase 1 Obsidian CLI commands (exact commands listed) → Phase 2 engine dispatch → Phase 3 save
10. **Command: enrich** — read health report → dispatch to /web-researcher → save to raw/ → prompt for compile
11. **Command: status** — exact Obsidian CLI commands for summary
12. **Script invocation patterns** — how to call each script (stdin JSON format, expected output)

Key instruction for Claude: "When the user invokes any compile/query/health/enrich command, follow the pipeline exactly. Do NOT skip the post-compile step. Do NOT skip the manifest scan before compile."

Load `references/compilation-prompts.md` when building prompts for engine dispatch.
Load `references/wiki-structure.md` when creating new projects or articles.
Reference the obsidian skill's `references/commands.md` for Obsidian CLI syntax details.

- [ ] **Step 2: Verify skill loads**

After creating SKILL.md, the user should reload skills and verify:

```
/skills
```

Expected: `knowledge-wiki` appears in the skill list with the description.

- [ ] **Step 3: Commit**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git add .claude/skills/knowledge-wiki/SKILL.md
git commit -m "feat: add SKILL.md orchestration for knowledge-wiki"
```

---

### Task 6: End-to-end integration test

Test the full init → compile → status flow against real data.

**Files:**
- No new files. Uses everything built in Tasks 1-5.

- [ ] **Step 1: Init a wiki project**

```
/knowledge-wiki init ~/Desktop/test-knowledge-wiki --source "/Users/manolo/Documents/Documents - Manolos MacBook Pro/notas-libros/raw-highlights" --lang en --engine codex
```

Verify:
- Directory structure created at `~/Desktop/test-knowledge-wiki/`
- `.obsidian/` directory exists
- `raw/raw-highlights` symlink points to Kindle files
- `wiki.config.json` has correct config
- `PROGRAM.md` generated with Kindle-highlights parsing hints
- `MOC - Knowledge Wiki.md` exists
- scan_raw.py reports 246 files

- [ ] **Step 2: Check status**

```
/knowledge-wiki status --into ~/Desktop/test-knowledge-wiki
```

Verify: Shows 246 raw files, 0 wiki articles, 0 orphans.

- [ ] **Step 3: Compile a topic subset**

```
/knowledge-wiki compile --scope topic --topic stoicism --into ~/Desktop/test-knowledge-wiki
```

Verify:
- Codex creates wiki articles in `wiki/concepts/` (e.g., `stoic-discipline.md`, `ego-as-enemy.md`)
- Articles have YAML frontmatter with tags, sources, related
- `obsidian_post_compile.py` ran and set properties
- `MOC - Knowledge Wiki.md` updated with new articles
- `wiki.config.json` has updated `lastCompiled` and `compilationCount: 1`

- [ ] **Step 4: Verify in Obsidian**

```bash
obsidian files folder=wiki/ ext=md vault="test-knowledge-wiki"
obsidian tags sort=count counts vault="test-knowledge-wiki"
obsidian orphans vault="test-knowledge-wiki"
obsidian unresolved vault="test-knowledge-wiki"
```

Verify: Articles listed, tags applied, minimal orphans/unresolved links.

Open the vault in Obsidian GUI and check graph view shows connected nodes.

- [ ] **Step 5: Test a query**

```
/knowledge-wiki query "What do the Stoics teach about ego and ambition?" --format md --into ~/Desktop/test-knowledge-wiki
```

Verify: Report saved to `outputs/reports/20260403_stoics-ego-ambition.md` with citations.

- [ ] **Step 6: Run health check**

```
/knowledge-wiki health --into ~/Desktop/test-knowledge-wiki
```

Verify: Structural analysis + semantic analysis report saved.

- [ ] **Step 7: Clean up test project**

```bash
rm -rf ~/Desktop/test-knowledge-wiki
```

- [ ] **Step 8: Final commit**

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git add -A
git commit -m "feat: knowledge-wiki skill complete — init, compile, query, health, status"
```
