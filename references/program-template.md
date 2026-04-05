# Knowledge Wiki — Compilation Program

## Project: {{name}}
Language: {{language}}
Sources: {{source_count}} files across {{source_groups}} groups

## Directory Layout
- raw/ — Source materials. READ ONLY. Never modify.
- wiki/concepts/ — One article per key idea
- wiki/authors/ — Author profiles for every source author
- wiki/themes/ — Cross-source theme synthesis
- wiki/connections/ — Surprising cross-domain links
- MOC - Knowledge Wiki.md — Master index. Update after every compilation. Must include "Source Library by Cluster" section (see below).

## Source Types
{{source_types_section}}

## Compilation Rules
1. Read ALL files in the specified scope
2. Identify key concepts that appear across multiple sources
3. Create wiki/concepts/<slug>.md for each concept
4. Use Obsidian [[wikilinks]] for ALL cross-references
5. Use #tags for categorization
6. Include YAML frontmatter on every article (see Frontmatter Schema below)
7. Quote directly from sources with attribution
8. Flag conflicting information with >[!warning] callouts
9. Prefer depth over breadth — rich articles > stubs

## Frontmatter Schema

### Concept
```yaml
---
title: "Concept Name"
aliases: ["alternative name"]
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
tags: [author, genre1]
books:
  - "[[raw/source-group/Book Title]]"
compiled_date: YYYY-MM-DD
---
```

### Theme
```yaml
---
title: "Theme Name"
aliases: ["alternative"]
tags: [theme, topic1]
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

## Quality Standards
- Concept articles: 500+ words, 3+ source citations, 2+ related concepts
- Author articles: biographical context, key ideas, book-by-book summaries
- Theme articles: synthesis across 5+ sources, practical applications
- Connection articles: explain WHY ideas connect, not just THAT they do

## MOC Structure

The MOC (Map of Content) must always contain these sections in order:
1. **Authors** — alphabetical list of `[[wiki/authors/<slug>|Name]]`
2. **Concepts** — alphabetical list of `[[wiki/concepts/<slug>|Name]]`
3. **Connections** — alphabetical list of `[[wiki/connections/<slug>|Name]]`
4. **Themes** — alphabetical list of `[[wiki/themes/<slug>|Name]]`
5. **Source Library by Cluster** — all raw source books grouped by topic cluster with wikilinks to raw files

The "Source Library by Cluster" section is generated from `.compile-state.json`. Each cluster is an H3 heading with its books listed as `[[raw/notas-libros/<filename>|<filename>]]`. This section MUST be preserved or regenerated whenever the MOC is rebuilt.

## Compilation Modes
- **FULL**: Rebuild all wiki articles from scratch
- **INCREMENTAL**: Only process delta files from manifest
- **TOPIC**: Focus on files matching a keyword/tag cluster

---

## Standard Source Type Hints

The following blocks are included conditionally based on source types present in the project.

### kindle-highlights
```
Files follow Glasp Kindle export format:
- H1 = book title
- ### Metadata section: Title, Author, Book URL, Kindle link, Last Updated
- ### Highlights & Notes section: blockquoted passages (> ...)
Extract: book title, author name, all highlighted passages with context.
```

### markdown
```
Generic markdown files. Extract title from H1 or filename.
Parse any YAML frontmatter for metadata. Content is the full file body.
```

### pdf
```
PDF files. Extract text content. Title from first heading or filename.
```

### mixed
```
Mixed file types. Detect format per-file and extract accordingly.
```
