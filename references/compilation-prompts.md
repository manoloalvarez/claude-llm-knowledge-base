# Compilation Prompt Templates

These templates are used when dispatching compilation and query tasks to LLM engines (Codex/Claude/Gemini).
Variables use `{{variable}}` syntax. Conditional blocks use `{{#if flag}}...{{/if}}`.

---

## Compile Prompt

Used for: FULL, INCREMENTAL, and TOPIC compilation modes.

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

### Variables

| Variable | Description |
|----------|-------------|
| `{{project_root}}` | Absolute path to the wiki project directory |
| `{{scope}}` | Compilation mode: `FULL`, `INCREMENTAL`, or `TOPIC` |
| `{{language}}` | Output language: `en` or `es` |
| `{{manifest}}` | Boolean — true when INCREMENTAL mode with delta files |
| `{{manifest_json}}` | JSON array of file paths to process (INCREMENTAL only) |
| `{{topic}}` | Topic filter string (TOPIC mode only) |

---

## Query Prompt

Used for: answering research questions against the compiled wiki.

```
You are a knowledge researcher. Your working directory is {{project_root}}.

Read PROGRAM.md for context about this knowledge wiki.

Question: {{question}}

Relevant articles found by search:
{{search_results}}

Research this question by reading the relevant wiki articles and raw sources.
Synthesize a comprehensive answer with citations using [[wikilinks]].

{{#if format_slides}}
Output as a Marp slide deck. Save to outputs/slides/{{date}}_{{slug}}.md

Marp slide rules:
- Start with this exact frontmatter:
  ---
  marp: true
  theme: default
  paginate: true
  backgroundColor: #1a1a2e
  color: #e0e0e0
  style: |
    section { font-family: 'Helvetica Neue', Arial, sans-serif; }
    h1 { color: #e94560; font-size: 2.2em; }
    h2 { color: #e94560; font-size: 1.6em; }
    blockquote { border-left: 4px solid #e94560; padding-left: 1em; color: #b0b0b0; font-style: italic; }
    strong { color: #e94560; }
  ---
- Separate slides with --- on its own line
- Title slide: H1 + subtitle + source attribution
- Content slides: H2 heading, 3-5 bullet points max, one blockquote per slide
- Keep text concise — slides are not reports
- Use tables for comparisons
- End with a synthesis/summary slide
- 8-12 slides total (not too many, not too few)
{{/if}}
{{#if format_md}}
Output as a markdown report.
Save to outputs/reports/{{date}}_{{slug}}.md
{{/if}}
{{#if format_terminal}}
Output your answer directly. Do not save to file.
{{/if}}
```

### Variables

| Variable | Description |
|----------|-------------|
| `{{project_root}}` | Absolute path to the wiki project directory |
| `{{question}}` | The user's research question |
| `{{search_results}}` | Pre-searched relevant article paths/snippets |
| `{{format_slides}}` | Boolean — output as Marp slide deck |
| `{{format_md}}` | Boolean — output as markdown report |
| `{{format_terminal}}` | Boolean — output directly to terminal |
| `{{date}}` | ISO date string (YYYYMMDD) for output filename |
| `{{slug}}` | Slugified version of the question for output filename |

---

## Health Prompt

Used for: wiki quality analysis and gap detection.

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

### Variables

| Variable | Description |
|----------|-------------|
| `{{project_root}}` | Absolute path to the wiki project directory |
| `{{structural_results}}` | Output from Obsidian CLI graph/link analysis |
| `{{date}}` | ISO date string (YYYYMMDD) for output filename |

---

## Enrich Prompt

Used for: delegating web research to fill gaps identified in health checks.
Engine: web-researcher skill.

```
Research the following knowledge gap identified in a wiki health check:

Gap: {{gap_description}}
Wiki context: {{wiki_context}}

Provide comprehensive information that could fill this gap.
Focus on factual, well-sourced content.
```

### Variables

| Variable | Description |
|----------|-------------|
| `{{gap_description}}` | Description of the knowledge gap from health report |
| `{{wiki_context}}` | Relevant existing wiki content for context |
