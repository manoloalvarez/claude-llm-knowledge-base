# Knowledge Wiki — Design Spec

## Overview

A general-purpose Claude Code skill that builds LLM-compiled knowledge wikis from raw source directories. Inspired by Andrej Karpathy's "LLM Knowledge Bases" workflow: ingest raw sources, compile a structured wiki with concepts/themes/connections, query against it, health-check for gaps, and enrich with web research. All output lives in an Obsidian vault with wikilinks, tags, properties, and Maps of Content.

## Architecture

**Skill-only** — SKILL.md defines all commands and pipelines. Claude orchestrates every step: running scripts, dispatching to LLM engines, executing Obsidian CLI. No plugin or separate agent needed.

**Engine-agnostic** — Codex is the default compilation engine. User can choose Claude or Gemini per-project (`wiki.config.json`) or per-command (`--engine` flag). All engines receive the same PROGRAM.md instructions.

```
User: /knowledge-wiki <command>
  │
  ▼
SKILL.md (Claude orchestrates)
  ├── init, ingest, status       → Obsidian CLI + scripts (local, fast)
  ├── compile                    → scan_raw.py → engine dispatch → obsidian_post_compile.py
  ├── query                      → Obsidian search → engine dispatch → save report
  ├── health                     → Obsidian CLI analysis → engine dispatch → save report
  └── enrich                     → web-researcher → save to raw/ → incremental compile
```

## Project Structure

Each knowledge wiki is a self-contained Obsidian vault. New vault per project.

```
<project-root>/
├── .obsidian/                        ← vault config
├── PROGRAM.md                        ← engine-agnostic compilation instructions
├── wiki.config.json                  ← project config
├── MOC - Knowledge Wiki.md           ← master Map of Content
│
├── raw/                              ← symlinks to source directories (read-only)
│   ├── <source-group-1>/
│   └── <source-group-N>/
│
├── wiki/                             ← compiled output
│   ├── concepts/                     ← one article per key idea
│   ├── authors/                      ← author profiles (3+ sources)
│   ├── themes/                       ← cross-source synthesis
│   └── connections/                  ← cross-domain links
│
└── outputs/
    ├── slides/                       ← Marp presentations
    ├── reports/                      ← Q&A and health reports
    └── charts/                       ← mermaid/matplotlib visuals
```

### wiki.config.json

```json
{
  "name": "My Knowledge Wiki",
  "language": "en",
  "defaultEngine": "codex",
  "sources": [
    { "name": "kindle", "path": "/absolute/path", "type": "kindle-highlights" },
    { "name": "articles", "path": "/absolute/path", "type": "markdown" }
  ],
  "lastCompiled": null,
  "compilationCount": 0
}
```

- `language`: `"en"` or `"es"` — all wiki output in this language
- `defaultEngine`: `"codex"`, `"claude"`, or `"gemini"` — overridable per command
- `sources[].type`: auto-detected during init. Options: `kindle-highlights`, `markdown`, `pdf`, `mixed`. Guides parsing hints in PROGRAM.md.

## Skill Commands

### init

```
/knowledge-wiki init <path> --source <dir> [--source <dir2>] [--lang en|es] [--engine codex|claude|gemini]
```

1. Create project directory + subdirs (raw/, wiki/concepts/, wiki/authors/, wiki/themes/, wiki/connections/, outputs/)
2. Create `.obsidian/` to register as Obsidian vault
3. For each `--source`: validate exists, auto-detect type, create symlink `raw/<name>/ → <path>`
4. Generate `wiki.config.json`
5. Generate `PROGRAM.md` from `references/program-template.md` (templated with project config)
6. Run `scan_raw.py` to count sources and detect topic clusters
7. Create `MOC - Knowledge Wiki.md` via Obsidian CLI with vault overview
8. Set MOC properties via Obsidian CLI

**Source type detection:**
- Has `### Highlights & Notes` + `>` blockquotes → `kindle-highlights`
- `.pdf` files → `pdf`
- `.md` files → `markdown`
- Mixed → `mixed`
- User can override with `--type <custom>`

### ingest

```
/knowledge-wiki ingest <url|file|dir> [--group <name>] [--into <project-path>]
```

| Input | Method | Destination |
|-------|--------|-------------|
| Single URL | WebFetch → save as markdown | `raw/articles/YYYYMMDD_<slug>.md` |
| Local file | Copy with metadata frontmatter | `raw/<group>/` |
| Local directory | Symlink | `raw/<group>/` |

Runs `obsidian_ingest.py` to set properties (source_url, ingested_date, source_type) on new files.

### compile

```
/knowledge-wiki compile [--scope full|incremental|topic] [--topic <name>] [--engine codex|claude|gemini]
```

Default scope: `incremental`.

**Pipeline:**
1. Run `scan_raw.py <project-root>` → JSON manifest with delta
2. Read PROGRAM.md + wiki.config.json
3. Build prompt from `references/compilation-prompts.md`
4. Dispatch to engine:
   - Codex: `/codex:rescue --effort high "<prompt>"`
   - Claude: native execution (read files, write output)
   - Gemini: `gemini -p '<prompt>'`
5. Engine reads raw files, writes wiki articles to `wiki/`
6. Run `obsidian_post_compile.py`:
   - Set properties per file (tags, compiled_date, source_count, status)
   - `obsidian unresolved` to verify links
   - Rebuild MOC by scanning wiki/ subdirectories
   - Report tag distribution
7. Update wiki.config.json (lastCompiled, compilationCount++)
8. Return summary

### query

```
/knowledge-wiki query <question> [--format md|slides|terminal] [--engine codex|claude|gemini]
```

1. Search wiki via Obsidian CLI: `obsidian search query="<keywords>" format=json`
2. Read relevant articles via `obsidian read`
3. Build query prompt with question + article context
4. Dispatch to engine
5. If format is `md`: save as `outputs/reports/YYYYMMDD_<slug>.md`
6. If format is `slides`: save as Marp in `outputs/slides/`
7. If `terminal`: return directly

### health

```
/knowledge-wiki health [--into <project-path>]
```

**Phase 1 — Obsidian CLI structural analysis:**
```bash
obsidian orphans format=json              # disconnected articles
obsidian deadends format=json             # no outgoing links
obsidian unresolved --verbose format=json # broken wikilinks
obsidian tags sort=count counts format=json
obsidian files folder=wiki/ ext=md --total
obsidian files folder=raw/ ext=md --total
```

**Phase 2 — Engine semantic analysis:**
Dispatch Phase 1 results + "find inconsistencies, suggest connections, identify gaps, rate coherence 1-10" to chosen engine.

**Phase 3 — Save report:**
Save to `outputs/reports/YYYYMMDD_health.md` via Obsidian CLI.

### enrich

```
/knowledge-wiki enrich [--topic <name>] [--into <project-path>]
```

1. Read latest health report
2. Extract gaps/suggestions
3. Dispatch each gap to `/web-researcher` (Gemini engine, Deep depth)
4. Save results as new raw sources in `raw/articles/`
5. Run `obsidian_ingest.py` on each
6. Prompt user to run `/knowledge-wiki compile` to integrate

### status

```
/knowledge-wiki status [--into <project-path>]
```

Pure Obsidian CLI calls — vault info, source count, article count, orphan count, unresolved links, top tags. Compact table output.

## PROGRAM.md Template

Generated during init, lives in project root. Engine-agnostic — any LLM reads it.

```markdown
# Knowledge Wiki — Compilation Program

## Project: {{name}}
Language: {{language}}
Sources: {{source_count}} files across {{source_groups}} groups

## Directory Layout
- raw/ — Source materials. READ ONLY.
- wiki/concepts/ — One article per key idea
- wiki/authors/ — Author profiles (3+ sources by same author)
- wiki/themes/ — Cross-source theme synthesis
- wiki/connections/ — Cross-domain links
- MOC - Knowledge Wiki.md — Master index. Update after every compilation.

## Source Types
{{per-source parsing hints}}

## Compilation Rules
1. Read ALL files in the specified scope
2. Identify key concepts across multiple sources
3. Create wiki/concepts/<slug>.md per concept
4. Use Obsidian [[wikilinks]] for all cross-references
5. Use #tags for categorization
6. Include YAML frontmatter on every article
7. Quote from sources with attribution
8. Flag conflicts with >[!warning] callouts
9. Depth over breadth — rich articles > stubs

## Frontmatter Schema
title, aliases, tags, sources (as [[wikilinks]]), related (as [[wikilinks]]), compiled_date

## Quality Standards
- Concept: 500+ words, 3+ source citations, 2+ related concepts
- Author: bio context, key ideas, book summaries
- Theme: synthesis across 5+ sources, practical applications
- Connection: explain WHY ideas connect

## Compilation Modes
- FULL: Rebuild all wiki articles from scratch
- INCREMENTAL: Only process delta files from manifest
- TOPIC: Focus on files matching keyword/tag
```

## Scripts

### scan_raw.py
- **Input:** `sys.argv[1]` = project root
- **Output:** JSON to stdout
- Walks `raw/`: title, author (if detectable), word count, mtime per file
- Walks `wiki/`: title, sources from frontmatter, word count, compiled_date per file
- Reads `wiki.config.json` for `lastCompiled`
- Computes delta: new, modified, unchanged
- Returns manifest with stats

### obsidian_post_compile.py
- **Input:** JSON via stdin — project root, vault name, list of new/modified wiki file paths
- **Output:** JSON summary to stdout
- Per file: reads YAML frontmatter that the engine wrote (title, tags, sources, related), then applies those values as Obsidian properties via `obsidian property:set`. Also sets compiled_date and source_count. This ensures Obsidian indexes properties that the engine embedded in frontmatter.
- Batch: `obsidian unresolved`, rebuild MOC by scanning wiki/ subdirs, `obsidian tags sort=count counts`
- Returns: files processed, properties set, unresolved links, tag distribution

### obsidian_ingest.py
- **Input:** JSON via stdin — file path, detected type, metadata
- **Output:** JSON confirmation to stdout
- Sets properties via Obsidian CLI: source_url, ingested_date, source_type
- If Kindle format: extracts author + title into properties

## Obsidian CLI Integration

| Phase | Commands Used |
|-------|-------------|
| Init | `vaults verbose`, `create`, `property:set` |
| Ingest | `create`, `property:set` (via obsidian_ingest.py) |
| Post-compile | `property:set`, `unresolved`, `orphans`, `deadends`, `tags`, `append` (via obsidian_post_compile.py) |
| Health | `orphans`, `deadends`, `unresolved`, `tags`, `files --total`, `backlinks --total`, `wordcount` |
| Query | `search`, `read` |
| Status | `vault`, `files --total`, `orphans --total`, `unresolved --total`, `tags` |

## Engine Dispatch

| Engine | Dispatch method |
|--------|----------------|
| Codex (default) | `/codex:rescue --effort high "<prompt>"` |
| Claude | Native execution (read files, write output directly) |
| Gemini | `gemini -p '<prompt>'` via Bash |

All engines receive the same prompt, which includes "Read PROGRAM.md at `<root>`" plus manifest and scope.

## File Inventory

```
/Users/manolo/.claude/skills/knowledge-wiki/
├── SKILL.md
├── scripts/
│   ├── scan_raw.py
│   ├── obsidian_post_compile.py
│   └── obsidian_ingest.py
└── references/
    ├── program-template.md
    ├── compilation-prompts.md
    └── wiki-structure.md
```

6 files. Reuses: obsidian skill, /codex:rescue, gemini CLI, WebFetch, /web-researcher.

## Decisions Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Skill-only | Claude orchestrates; no plugin complexity needed |
| Engine | Agnostic, Codex default | User always chooses; same prompts to all engines |
| Vault | New vault per project | Clean isolation, independent graph |
| Ingestion | URLs (WebFetch) + local files | web-researcher reserved for enrich only |
| Compile default | Incremental | Faster, cheaper; full available as flag |
| File writing | Engine writes, Claude post-processes | Engine does creative work; Obsidian CLI does structural indexing |
| Language | Per-project config | Stored in wiki.config.json |
| Source types | Auto-detected, overridable | Kindle-highlights, markdown, pdf, mixed |
