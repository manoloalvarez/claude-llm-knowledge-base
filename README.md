# Knowledge Wiki

A Claude Code skill that builds LLM-compiled knowledge wikis from raw source directories. Inspired by [Andrej Karpathy's "LLM Knowledge Bases"](https://x.com/karpathy) workflow: ingest raw sources (Kindle highlights, articles, papers, notes), compile a structured Obsidian wiki with concepts, themes, cross-domain connections, and author profiles — then query, health-check, and enrich it over time.

## How It Works

```
User: /knowledge-wiki <command>
  │
  ▼
SKILL.md (Claude orchestrates)
  ├── init, ingest, status       → Obsidian CLI + Python scripts (local, fast)
  ├── compile                    → scan_raw.py → LLM subagent dispatch → obsidian_post_compile.py
  ├── query                      → Obsidian search → LLM synthesis → terminal / markdown / Marp slides
  ├── health                     → Obsidian CLI analysis → Opus semantic review → gap report
  └── enrich                     → web research → save to raw/ → incremental compile
```

The skill auto-selects the optimal Claude model per task — Haiku for classification and translation, Sonnet for mechanical compilation, Opus for cross-domain synthesis and deep analysis. The orchestrating session stays lean by dispatching heavy work to focused subagents.

## Prerequisites

| Tool | Install | Verify |
|------|---------|--------|
| [Obsidian CLI](https://github.com/Acylation/obsidian-cli) v1.12+ | See docs | `obsidian --version` |
| Python 3 | System or homebrew | `python3 --version` |
| [Marp CLI](https://github.com/marp-team/marp-cli) | `npm i -g @marp-team/marp-cli` | `marp --version` |

## Installation

Copy the skill into your Claude Code skills directory:

```bash
cp -r . ~/.claude/skills/knowledge-wiki/
```

Or symlink it:

```bash
ln -s $(pwd) ~/.claude/skills/knowledge-wiki
```

Then register the skill in your Claude Code settings (`~/.claude/settings.json` or project-level):

```json
{
  "skills": {
    "knowledge-wiki": {
      "path": "~/.claude/skills/knowledge-wiki/SKILL.md"
    }
  }
}
```

## Commands

### `init` — Create a new wiki project

```
/knowledge-wiki init <path> --source <dir> [--source <dir2>] [--lang en|es]
```

Creates an Obsidian vault, symlinks source directories into `raw/`, auto-detects source types (Kindle highlights, markdown, PDF, mixed), generates `PROGRAM.md` and `wiki.config.json`.

### `ingest` — Add new sources

```
/knowledge-wiki ingest <url|file|dir> [--group <name>]
```

Accepts URLs (fetched and converted to markdown), local files, or directories. Sets Obsidian properties on ingested files.

### `compile` — Build the wiki

```
/knowledge-wiki compile [--scope full|incremental|topic|library] [--topic <name>]
```

| Scope | Description |
|-------|-------------|
| `incremental` (default) | Process only new/changed files since last compile |
| `full` | Rebuild all wiki articles from scratch |
| `topic` | Focus on files matching a keyword/tag cluster |
| `library` | Full library compilation: classify into topic clusters → batch-compile each → cross-topic synthesis. Supports pause/resume via `.compile-state.json` |

**Library scope** is designed for large collections (100+ sources). It classifies sources into 12-20 topic clusters, compiles each sequentially (extending existing articles rather than overwriting), then runs a cross-topic synthesis pass with Opus for deep connections.

### `query` — Ask questions against your wiki

```
/knowledge-wiki query <question> [--format terminal|md|slides]
```

Searches the wiki via Obsidian CLI, reads relevant articles, and dispatches to Sonnet (factual) or Opus (synthesis) based on question complexity. Output formats:

- **terminal** (default) — answer displayed directly
- **md** — saved to `outputs/reports/`
- **slides** — Marp presentation saved to `outputs/slides/`, auto-converted to HTML + PDF

### `health` — Check wiki quality

```
/knowledge-wiki health
```

Two-phase analysis:
1. **Structural** — orphans, dead ends, unresolved links, tag distribution (via Obsidian CLI)
2. **Semantic** — inconsistencies, missing connections, coverage gaps, enrichment candidates (via Opus)

Saves report to `outputs/reports/YYYYMMDD_health.md`.

### `enrich` — Fill knowledge gaps

```
/knowledge-wiki enrich [--topic <name>]
```

Reads the latest health report, identifies gaps, runs web research to fill them, and saves results as new raw sources. Run `compile` afterward to integrate.

### `translate` — Translate the wiki

```
/knowledge-wiki translate --lang <code> [--scope full|changed]
```

Translates the English wiki into a parallel directory tree (`wiki-es/`, `wiki-fr/`, etc.) using Haiku. Preserves wikilinks, frontmatter structure, and cross-language links.

### `status` — Project overview

```
/knowledge-wiki status
```

Shows source count, article counts by type, last compiled date, coverage ratio, and compilation history.

## Project Structure

Each knowledge wiki is a self-contained Obsidian vault:

```
<project-root>/
├── .obsidian/                        ← vault config
├── PROGRAM.md                        ← compilation instructions (read by every subagent)
├── wiki.config.json                  ← project config
├── .compile-state.json               ← library compilation progress (pause/resume)
├── MOC - Knowledge Wiki.md           ← master Map of Content
│
├── raw/                              ← symlinks to source directories (READ ONLY)
│   └── <source-group>/
│
├── wiki/                             ← compiled output
│   ├── concepts/                     ← one article per key idea (500+ words, 3+ citations)
│   ├── authors/                      ← author profiles with book-by-book summaries
│   ├── themes/                       ← cross-source synthesis (5+ sources)
│   └── connections/                  ← cross-domain links (explains WHY, not just THAT)
│
└── outputs/
    ├── slides/                       ← Marp presentations (.md, .html, .pdf)
    ├── reports/                      ← query answers and health reports
    └── charts/                       ← visualizations
```

## Skill Repo Structure

```
knowledge-wikis/
├── SKILL.md                          ← main skill definition
├── references/
│   ├── compilation-prompts.md        ← prompt templates for compile/query/health/enrich
│   ├── program-template.md           ← template for generating PROGRAM.md per project
│   └── wiki-structure.md             ← Obsidian structure reference
├── scripts/
│   ├── scan_raw.py                   ← manifest generator (raw files, wiki articles, delta)
│   ├── obsidian_post_compile.py      ← post-compile: tagging, MOC rebuild, link checking
│   ├── obsidian_ingest.py            ← set properties on ingested files
│   └── utils.py                      ← shared frontmatter parsing utilities
├── tests/
│   ├── test_scan_raw.py
│   └── test_post_compile.py
└── docs/
    └── superpowers/
        ├── specs/                    ← design specification
        └── plans/                    ← implementation plan
```

## Example: 235-Book Wiki

The skill was built and tested against a library of 235 Kindle highlight exports. The compilation produced:

- **205** concept articles
- **175** author profiles
- **37** theme syntheses
- **11** cross-domain connections
- **24** topic clusters
- **Coherence score**: 8.2/10 (Opus health analysis)

Query example — "How do these books connect discipline and freedom?":

> Searched wiki → read 15 relevant articles → Opus synthesized a 2,000-word answer citing Epictetus, Ryan Holiday, Morgan Housel, Steven Pressfield, and Seth Godin → generated a 10-slide Marp presentation with dark theme.

## Model Selection

| Task | Model | Reasoning |
|------|-------|-----------|
| Source classification | Haiku | Simple categorization from titles |
| Article compilation | Sonnet | Structured extraction, mechanical output |
| Connection articles | Opus | Cross-domain insight requires deeper reasoning |
| Cross-topic synthesis | Opus | Full-library reasoning |
| Factual queries | Sonnet | Pattern matching against existing wiki |
| Deep synthesis queries | Opus | Argument construction, nuanced answers |
| Health analysis | Opus | Judgment across hundreds of articles |
| Translation | Haiku | Mechanical translation, preserves structure |

## License

MIT
