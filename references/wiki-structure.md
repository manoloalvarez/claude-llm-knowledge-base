# Wiki Structure Reference

## Project Directory Layout

```
<project-root>/
├── .obsidian/                  # Vault config. Makes this directory an Obsidian vault.
├── raw/                        # Source materials. READ ONLY. Never modify.
│   └── <source-group>/         # One subdirectory per source group
│       └── ...                 # Source files (Kindle exports, markdown, PDFs, etc.)
├── wiki/                       # Compiled knowledge articles
│   ├── concepts/               # One article per key idea
│   ├── authors/                # Author profiles for every source author
│   ├── themes/                 # Cross-source theme synthesis
│   └── connections/            # Surprising cross-domain links
├── outputs/                    # Generated outputs (slides, reports, charts)
│   ├── slides/                 # Marp slide decks
│   ├── reports/                # Markdown reports and health checks
│   └── charts/                 # Mermaid/matplotlib visuals
├── wiki.config.json            # Project configuration
├── PROGRAM.md                  # Compilation instructions (generated from template)
└── MOC - Knowledge Wiki.md     # Master index. Updated after every compilation.
```

## wiki.config.json Schema

```json
{
  "name": "string - project name",
  "language": "en|es",
  "defaultEngine": "codex|claude|gemini",
  "sources": [
    {
      "name": "string - human-readable group name",
      "path": "/absolute/path/to/source/group",
      "type": "kindle-highlights|markdown|pdf|mixed"
    }
  ],
  "lastCompiled": "ISO8601 timestamp or null",
  "compilationCount": "number"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Human-readable project name (e.g., "Stoic Philosophy") |
| `language` | `en` or `es` | Output language for all wiki articles |
| `defaultEngine` | `codex`, `claude`, or `gemini` | LLM engine used for compilation |
| `sources` | array | List of source groups to compile from |
| `sources[].name` | string | Display name for this source group |
| `sources[].path` | string | Absolute path to source group directory |
| `sources[].type` | enum | File format type hint for the compiler |
| `lastCompiled` | ISO8601 or null | Timestamp of last successful compilation |
| `compilationCount` | number | Total number of compilations run on this project |

## Slug Naming Convention

- Lowercase only
- Words separated by hyphens
- No special characters, accents, or punctuation
- No spaces
- Descriptive and concise

Examples:
- `stoic-discipline.md`
- `memento-mori.md`
- `negative-visualization.md`
- `marcus-aurelius.md`
- `fear-as-motivation.md`

## Frontmatter Schema per Article Type

### Concept

```yaml
---
title: "Concept Name"
aliases: ["alternative name", "another alias"]
tags: [concept, topic1, topic2]
sources:
  - "[[raw/source-group/Source File]]"
related:
  - "[[wiki/concepts/related-concept]]"
compiled_date: YYYY-MM-DD
---
```

### Author

```yaml
---
title: "Author Name"
aliases: ["Last Name"]
tags: [author, genre1, genre2]
books:
  - "[[raw/source-group/Book Title]]"
compiled_date: YYYY-MM-DD
---
```

### Theme

```yaml
---
title: "Theme Name"
aliases: ["alternative name"]
tags: [theme, topic1, topic2]
sources:
  - "[[raw/source-group/Source File]]"
concepts:
  - "[[wiki/concepts/related-concept]]"
compiled_date: YYYY-MM-DD
---
```

### Connection

```yaml
---
title: "Connection Name"
tags: [connection, cross-domain]
concepts:
  - "[[wiki/concepts/concept-a]]"
  - "[[wiki/concepts/concept-b]]"
compiled_date: YYYY-MM-DD
---
```

## Obsidian Property Type Mapping

| YAML Field | Obsidian Type | Notes |
|------------|---------------|-------|
| `tags` | tags | Renders as tag pills |
| `compiled_date` | date | Renders as date picker |
| `source_count` | number | Renders as number field |
| `status` | text | Renders as plain text |
| `aliases` | list | Used for Obsidian search aliases |
| `sources` | list | Wikilinks to raw source files |
| `related` | list | Wikilinks to other wiki articles |
| `books` | list | Wikilinks to raw book files |
| `concepts` | list | Wikilinks to concept articles |
