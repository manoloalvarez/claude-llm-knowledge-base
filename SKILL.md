---
name: knowledge-wiki
description: >
  Build and maintain LLM-compiled knowledge wikis from raw sources.
  Point at any directory (Kindle highlights, articles, papers, notes)
  and compile a structured Obsidian wiki with concepts, cross-references,
  backlinks, and MOCs. Auto-selects the optimal Claude model per task.
  Uses Obsidian CLI for vault management, tagging, and health analysis.
  Triggers: 'knowledge wiki', 'knowledge base', 'compile wiki',
  'wiki from sources', 'build knowledge base', 'karpathy wiki'.
---

# Knowledge Wiki Skill

Build LLM-compiled knowledge wikis from raw source directories. Ingest raw sources, compile a structured Obsidian wiki with concepts/themes/connections, query against it, health-check for gaps, and enrich with web research. All output lives in an Obsidian vault with wikilinks, tags, properties, and Maps of Content.

**Commands:** `init`, `ingest`, `compile`, `query`, `health`, `enrich`, `translate`, `status`, `publish`

---

## 1. Prerequisites

- **Obsidian CLI v1.12+** — verify: `obsidian --version`
- **Python 3** — for scripts
- **Marp CLI** — for slide generation: `npm i -g @marp-team/marp-cli` — verify: `marp --version`

---

## 2. Project Detection

To find the current wiki project, walk up from cwd looking for `wiki.config.json`. If not found and no `--into` flag provided, ask the user which project to use.

```
--into <project-path>    Override project detection with explicit path
```

Read `wiki.config.json` for project config: name, language, sources, lastCompiled, compilationCount.

---

## 3. Model Selection

The skill auto-selects the optimal Claude model for each task. The orchestrating session (your current model) handles lightweight coordination — scanning, prompting, post-processing. Heavy work is dispatched to subagents via the Agent tool with the appropriate `model` parameter.

| Command | Phase | Model | Why |
|---------|-------|-------|-----|
| compile | Read sources + write articles | **sonnet** | Mechanical extraction, structured output |
| compile | Connection articles | **opus** | Cross-domain insight needs deeper reasoning |
| compile --scope library | Classify sources into topics | **haiku** | Simple categorization from titles |
| compile --scope library | Batch-compile each cluster | **sonnet** | Same as standard compile |
| compile --scope library | Cross-topic synthesis | **opus** | Deep reasoning across full wiki |
| query | Factual lookup | **sonnet** | Pattern matching against wiki |
| query | Deep synthesis | **opus** | Argument construction, nuanced answers |
| health | Semantic analysis | **opus** | Judgment across articles, gap detection |
| enrich | Gap analysis | **opus** | Strategic thinking about what's missing |
| enrich | Web research gathering | **haiku** | Simple fetch + format |
| translate | Translate wiki articles | **haiku** | Mechanical translation, preserves structure |
| init/ingest/status | — | **none** | Scripts + CLI only, no model needed |

### Dispatch Pattern

All compilation/query/analysis work is dispatched via the Agent tool:

```
Agent(
  model: "sonnet",  // or "opus" or "haiku" per table above
  prompt: "<rendered prompt from references/compilation-prompts.md>"
)
```

The prompt always includes "Read PROGRAM.md at `<project_root>`" so the subagent gets full compilation context.

**Key principle:** The orchestrator never reads raw source files itself. It scans the manifest, builds the prompt, dispatches to the right model, then runs post-processing. This keeps the orchestrating session's context lean.

---

## 4. Command: init

```
/knowledge-wiki init <path> --source <dir> [--source <dir2>] [--lang en|es]
```

**Pipeline:**

1. **Create project structure:**
   ```bash
   mkdir -p <path>/{.obsidian,raw,wiki/concepts,wiki/authors,wiki/themes,wiki/connections,outputs/slides,outputs/reports,outputs/charts}
   ```

2. **Register as Obsidian vault:**
   ```bash
   obsidian create vault="<project-name>" path="<path>"
   ```
   If vault already exists, skip.

3. **For each `--source` directory:**
   - Validate it exists
   - Auto-detect source type:
     - Has `### Highlights & Notes` + `>` blockquotes → `kindle-highlights`
     - `.pdf` files → `pdf`
     - `.md` files → `markdown`
     - Mixed → `mixed`
   - Create symlink: `ln -s <source-path> <path>/raw/<source-name>`

4. **Generate wiki.config.json:**
   ```json
   {
     "name": "<project-name>",
     "language": "<lang>",
     "sources": [{"name": "<dir-name>", "path": "<abs-path>", "type": "<detected>"}],
     "lastCompiled": null,
     "compilationCount": 0
   }
   ```

5. **Generate PROGRAM.md** from `references/program-template.md`:
   - Read the template
   - Replace `{{name}}`, `{{language}}`, `{{source_count}}`, `{{source_groups}}`
   - Build `{{source_types_section}}` by including only the relevant source type hint blocks
   - Write to `<path>/PROGRAM.md`

6. **Run scan_raw.py** to count sources:
   ```bash
   python3 ~/.claude/skills/knowledge-wiki/scripts/scan_raw.py <path>
   ```
   Parse JSON output for stats.

7. **Create MOC:**
   ```bash
   obsidian create title="MOC - Knowledge Wiki" vault="<project-name>"
   ```
   Write initial content: `# Knowledge Wiki\n\nVault: <name>\nSources: <count> files\nStatus: Awaiting first compilation.`

8. **Set MOC properties:**
   ```bash
   obsidian property:set file="MOC - Knowledge Wiki" name=tags value=moc type=tags vault="<project-name>"
   ```

9. **Report** summary: project created, source count, detected types, next step ("run `/knowledge-wiki compile`").

---

## 5. Command: ingest

```
/knowledge-wiki ingest <url|file|dir> [--group <name>] [--into <project-path>]
```

| Input | Method | Destination |
|-------|--------|-------------|
| URL (starts with `http`) | WebFetch → save as markdown | `raw/articles/YYYYMMDD_<slug>.md` |
| Local file | Copy with metadata | `raw/<group>/` |
| Local directory | Symlink | `raw/<group>/` |

**For URLs:**
1. Use WebFetch to download content
2. Convert to markdown
3. Save to `raw/articles/YYYYMMDD_<slug>.md`
4. Add source_url to frontmatter

**After saving, run obsidian_ingest.py:**
```bash
echo '{"vault": "<vault>", "files": [{"path": "<rel-path>", "source_type": "<type>", "title": "<title>", "author": "<author>", "source_url": "<url>"}]}' | python3 ~/.claude/skills/knowledge-wiki/scripts/obsidian_ingest.py
```

Update `wiki.config.json` sources array if a new source group was added.

---

## 6. Command: compile

```
/knowledge-wiki compile [--scope full|incremental|topic|library] [--topic <name>]
```

Default scope: `incremental`.

### Scopes: full, incremental, topic

**Pipeline — follow exactly, do NOT skip any step:**

1. **Scan manifest:**
   ```bash
   python3 ~/.claude/skills/knowledge-wiki/scripts/scan_raw.py <project-root>
   ```
   Parse JSON output. Check delta for files to process. If incremental and no new files, report "nothing to compile" and stop.

2. **Read compilation context:**
   - Read `references/compilation-prompts.md` for the compile prompt template
   - Read `wiki.config.json` for language
   - Read `PROGRAM.md` at project root (the subagent will also read this)

3. **Build the prompt** from the compile template:
   - Set `{{project_root}}` to absolute path
   - Set `{{scope}}` to FULL, INCREMENTAL, or TOPIC
   - Set `{{language}}` from config
   - For incremental: include `{{manifest_json}}` with delta files
   - For topic: include `{{topic}}` filter

4. **Dispatch to subagent** (see Section 3 for model selection):
   - Dispatch main compilation via `Agent(model: "sonnet", prompt: <rendered prompt>)`
   - If scope includes connection articles, dispatch those separately via `Agent(model: "opus", prompt: <connections prompt>)`
   - The subagent reads raw files, creates wiki articles using Write tool

5. **Post-compile processing** (NEVER skip this step):
   ```bash
   echo '{"project_root": "<root>", "vault": "<vault>", "files": ["wiki/concepts/file1.md", ...]}' | python3 ~/.claude/skills/knowledge-wiki/scripts/obsidian_post_compile.py
   ```
   - Collect the list of new/modified wiki files from the engine's output
   - Feed them to obsidian_post_compile.py
   - This sets properties, checks links, rebuilds MOC, reports tag distribution

6. **Update wiki.config.json:**
   - Set `lastCompiled` to current ISO timestamp
   - Increment `compilationCount`

7. **Report** summary: articles created/updated, unresolved links, tag distribution, coverage ratio.

### Scope: library

Compiles the entire source library in three phases: classify, batch-compile, synthesize. Supports pause/resume — safe to stop mid-process and continue later.

#### State file: `.compile-state.json`

The library scope tracks progress in `<project_root>/.compile-state.json`. This file is created at the start and updated after each cluster. It enables pause/resume and progress reporting.

```json
{
  "started": "2026-04-03T20:00:00Z",
  "phase": "compile",
  "clusters": [
    {"topic": "stoicism", "files": ["file1.md", ...], "status": "done", "articles_created": 8},
    {"topic": "leadership", "files": [...], "status": "done", "articles_created": 12},
    {"topic": "psychology", "files": [...], "status": "pending", "articles_created": 0}
  ],
  "completed_clusters": 2,
  "total_articles": 20
}
```

**Resume behavior:** When `--scope library` is invoked and `.compile-state.json` exists:
- Show progress bar and report what was completed:
  ```
  Resuming library compilation...
  ████████████████░░░░░░░░░░░░░░ 9/17 clusters
  ✓ Stoicism, Leadership, Psychology, Business, ... (9 done)
  ▸ Resuming from: Creativity (cluster 10/17)
  ```
- Resume from the next pending cluster (skip all "done" clusters)
- If `phase` is `"synthesis"`, skip directly to Phase 3
- If `phase` is `"done"`, report "Library compilation already complete" and stop

**To force a fresh start:** delete `.compile-state.json` or use `--scope library --fresh`.

#### Phase 1 — Classify sources into topic clusters

1. **Scan manifest** (same as above — run `scan_raw.py`)

2. **Dispatch classification agent:**
   ```
   Agent(
     model: "haiku",
     prompt: "Here are {{total_raw}} source file titles from a knowledge library:
       {{list of raw_files with title and author}}
       Group these into 12-20 topic clusters. Each cluster should have 8-15 files.
       A file can appear in multiple clusters if strongly relevant.
       Output ONLY valid JSON: {\"clusters\": [{\"topic\": \"...\", \"files\": [\"filename1.md\", ...]}]}"
   )
   ```

3. **Parse the JSON response** into a list of clusters. Validate every source file appears in at least one cluster. If any are missing, add them to the most relevant cluster.

4. **Write `.compile-state.json`** with all clusters set to `"pending"`, phase `"compile"`.

5. **Report classification to user:**
   ```
   Library compilation — 245 sources → 17 clusters
   
   | #  | Cluster              | Files | Status  |
   |----|----------------------|-------|---------|
   | 1  | Stoicism             | 13    | pending |
   | 2  | Leadership           | 15    | pending |
   | 3  | Psychology           | 11    | pending |
   | ...| ...                  | ...   | ...     |
   | 17 | Creativity           | 8     | pending |
   
   Starting compilation...
   ```

#### Phase 2 — Batch-compile each cluster (sequential)

For each cluster with status `"pending"`:

1. Build the compile prompt with `{{scope}}` = TOPIC and `{{topic}}` = cluster topic name
2. List the specific files belonging to this cluster in the prompt
3. Tell the subagent: "Check wiki/ for existing articles before creating new ones. If an article exists, read it and add new content from these sources."
4. Dispatch via `Agent(model: "sonnet", prompt: <rendered prompt>)`
5. Run `obsidian_post_compile.py` after EACH cluster
6. **Update `.compile-state.json`:** set this cluster to `"done"`, record `articles_created`, increment `completed_clusters`, update `total_articles`
7. **Report progress to user:**
   ```
   ████████████░░░░░░░░░░░░░░░░░░ 3/17 clusters
   ✓ Psychology — 9 new, 3 extended | 41 articles total
   ```
   Progress bar formula: fill `█` for `(completed / total) × 30` chars, `░` for the rest.

**Important rules for Phase 2:**
- Process clusters **sequentially**, not in parallel (avoids wiki file conflicts)
- If a concept/author article already exists from a previous cluster, the subagent should **extend it** (add new citations, quotes, related concepts) rather than overwrite
- After each cluster completes, the state file is updated — if the session is interrupted, the next invocation resumes from here

#### Phase 3 — Cross-topic synthesis

After all clusters are compiled (or when resuming with `phase: "synthesis"`):

1. **Update `.compile-state.json`:** set `phase` to `"synthesis"`.

2. **Collect all wiki articles** created across all clusters:
   ```bash
   find <project_root>/wiki -name "*.md" -type f
   ```

3. **Dispatch synthesis agent:**
   ```
   Agent(
     model: "opus",
     prompt: "Read PROGRAM.md at <project_root>.
       You are running the synthesis phase of a library-wide compilation.
       Read ALL articles in wiki/concepts/, wiki/authors/, wiki/themes/, wiki/connections/.
       Your job:
       1. Create NEW cross-topic connection articles in wiki/connections/ for ideas that
          bridge different topic clusters (e.g., stoicism ↔ psychology, leadership ↔ spirituality).
          Only create connections that are genuinely insightful — not obvious groupings.
       2. Create or extend wiki/themes/ articles that synthesize across 5+ sources from
          different clusters.
       3. Review existing articles for consistency: flag duplicate concepts that should be
          merged, fix broken wikilinks, ensure display alias syntax [[path|Name]] everywhere.
       4. Do NOT rewrite existing articles — only extend, connect, and create new synthesis.
       Language: {{language}}
       List every file you created or modified."
   )
   ```

4. **Run post-compile** on all new/modified files from the synthesis pass.

#### Phase 4 — Final update

1. Update `wiki.config.json`: set `lastCompiled`, increment `compilationCount`
2. **Update `.compile-state.json`:** set `phase` to `"done"`.
3. **Report full summary:**
   ```
   Library compilation complete!
   
   | Metric                | Value |
   |-----------------------|-------|
   | Clusters processed    | 17/17 |
   | Concepts              | 85    |
   | Authors               | 23    |
   | Themes                | 12    |
   | Connections           | 8     |
   | Total articles        | 128   |
   | Coverage              | 52.0% |
   | Unresolved links      | 4     |
   | Time elapsed          | 45m   |
   
   Next steps:
   - /knowledge-wiki health — check for gaps
   - /knowledge-wiki translate --lang es — translate to Spanish
   ```

---

## 7. Command: query

```
/knowledge-wiki query <question> [--format md|slides|terminal]
```

Default format: `terminal`.

**Pipeline:**

1. **Search wiki** via Obsidian CLI:
   ```bash
   obsidian search query="<keywords>" vault="<vault>" path="wiki/" limit=15
   ```
   Extract keywords from the question. Use multiple searches if needed (individual keywords + combined phrases) to cast a wider net. Deduplicate results.

2. **Read relevant articles** — the subagent reads matched articles directly (paths provided in the prompt).

3. **Build query prompt** from `references/compilation-prompts.md` query template:
   - Set `{{question}}`, `{{search_results}}`, format flags, `{{date}}`, `{{slug}}`
   - For slides format: include the Marp slide template from `references/compilation-prompts.md`

4. **Dispatch to subagent** (see Section 3 for model selection):
   - Factual lookups: `Agent(model: "sonnet", prompt: <query prompt>)`
   - Deep synthesis questions: `Agent(model: "opus", prompt: <query prompt>)`
   - Heuristic: if the question contains "why", "compare", "argue", or "synthesize" → opus; otherwise → sonnet

5. **Handle output by format:**
   - `terminal`: display answer directly
   - `md`: save to `outputs/reports/YYYYMMDD_<slug>.md`
   - `slides`: subagent saves Marp markdown to `outputs/slides/YYYYMMDD_<slug>.md`, then orchestrator runs:
     ```bash
     marp outputs/slides/YYYYMMDD_<slug>.md -o outputs/slides/YYYYMMDD_<slug>.html
     marp outputs/slides/YYYYMMDD_<slug>.md -o outputs/slides/YYYYMMDD_<slug>.pdf --allow-local-files
     ```
     Open the HTML file in the browser: `open outputs/slides/YYYYMMDD_<slug>.html`
     Report: "Slides saved to outputs/slides/ (markdown, HTML, PDF)"

---

## 8. Command: health

```
/knowledge-wiki health [--into <project-path>]
```

**Phase 1 — Obsidian CLI structural analysis:**
```bash
obsidian orphans format=json vault="<vault>"
obsidian deadends format=json vault="<vault>"
obsidian unresolved --verbose format=json vault="<vault>"
obsidian tags sort=count counts format=json vault="<vault>"
obsidian files folder=wiki/ ext=md --total vault="<vault>"
obsidian files folder=raw/ ext=md --total vault="<vault>"
```

Collect all output into `{{structural_results}}`.

**Phase 2 — Semantic analysis:**
Build health prompt from `references/compilation-prompts.md` health template. Dispatch via `Agent(model: "opus", prompt: <health prompt>)` with structural results. The subagent will:
1. Find inconsistencies across articles
2. Suggest new connections
3. Identify coverage gaps
4. Flag enrichment candidates
5. Rate coherence 1-10

**Phase 3 — Save report:**
Save combined structural + semantic analysis to `outputs/reports/YYYYMMDD_health.md`.

---

## 9. Command: enrich

```
/knowledge-wiki enrich [--topic <name>] [--into <project-path>]
```

**Pipeline:**

1. Read the latest health report from `outputs/reports/`. If no health report exists, instruct the user to run `/knowledge-wiki health` first and stop.
2. Extract gaps and suggestions
3. For each gap, dispatch to `/web-researcher` skill:
   - Depth: Deep
   - Build enrich prompt from `references/compilation-prompts.md`
4. Save research results as new raw sources in `raw/articles/YYYYMMDD_<slug>.md`
5. Run `obsidian_ingest.py` on each new file
6. Report: "Added N new sources. Run `/knowledge-wiki compile` to integrate them."

---

## 10. Command: translate

```
/knowledge-wiki translate --lang <code> [--scope full|changed] [--into <project-path>]
```

Default scope: `changed` (only articles modified since last translation).

Translates the English wiki into a parallel directory tree. The English wiki (`wiki/`) is always the source of truth — translations mirror it.

**Directory structure:**
```
wiki/              ← English (source)
  concepts/
  authors/
  themes/
  connections/
wiki-es/           ← Spanish (translated)
  concepts/
  authors/
  themes/
  connections/
wiki-fr/           ← French, etc.
  ...
```

**Pipeline:**

1. **Create target directories** if they don't exist:
   ```bash
   mkdir -p <project_root>/wiki-<lang>/{concepts,authors,themes,connections}
   ```

2. **Collect files to translate:**
   - `--scope full`: all `.md` files in `wiki/`
   - `--scope changed`: compare mtime of each `wiki/<path>` vs `wiki-<lang>/<path>`. Translate only where the English file is newer or the translation doesn't exist.

3. **Batch files into groups of 5-8** (to keep each Haiku dispatch small and fast).

4. **For each batch, dispatch translation agent:**
   ```
   Agent(
     model: "haiku",
     prompt: "You are a professional translator. Translate these Obsidian wiki articles
       from English to <language_name>.

       Rules:
       - Translate ALL prose content including headings, paragraphs, and list items
       - Keep YAML frontmatter keys in English (title, tags, sources, concepts, compiled_date)
       - Translate YAML frontmatter VALUES: title, aliases, tag values that are descriptive words
       - Preserve [[wikilinks]] paths exactly but translate the display alias:
         [[wiki/concepts/amor-fati|Amor Fati]] → [[wiki-<lang>/concepts/amor-fati|Amor Fati]]
       - Update all wikilink paths from wiki/ to wiki-<lang>/
       - Preserve all markdown formatting, code blocks, and blockquotes
       - For blockquotes from sources: keep the original English quote, add translation below:
         > 'Original English quote' — *Source*
         > *'Translated quote'*
       - Use 'tú' form for Spanish, never 'vos'
       - Include 100% correct accents and special characters (á, é, í, ó, ú, ñ, ü, ¿, ¡)
       - Add a cross-language link at the bottom: [[wiki/concepts/<slug>|English Version]]

       Files to translate:
       {{file_contents}}

       Write each translated file to wiki-<lang>/<same-path>."
   )
   ```

5. **Run post-compile** on translated files:
   ```bash
   echo '{"project_root": "<root>", "vault": "<vault>", "files": ["wiki-<lang>/concepts/file1.md", ...]}' | python3 ~/.claude/skills/knowledge-wiki/scripts/obsidian_post_compile.py
   ```

6. **Add cross-language links to English articles** (only on first translation):
   - For each translated file, check if the English source already has a link to the translation
   - If not, append to the English article's "See Also" section:
     `- [[wiki-<lang>/concepts/<slug>|Versión en Español]]` (or appropriate language label)

7. **Report** summary: files translated, files skipped (unchanged), language, target directory.

---

## 11. Command: status

```
/knowledge-wiki status [--into <project-path>]
```

Pure Obsidian CLI calls — no engine dispatch needed:

```bash
obsidian vault verbose vault="<vault>"
obsidian files folder=raw/ ext=md --total vault="<vault>"
obsidian files folder=wiki/ ext=md --total vault="<vault>"
obsidian orphans --total vault="<vault>"
obsidian unresolved --total vault="<vault>"
obsidian tags sort=count counts vault="<vault>"
```

Display as compact table:

```
| Metric          | Value |
|-----------------|-------|
| Raw sources     | 246   |
| Wiki articles   | 42    |
| Coverage        | 17.1% |
| Translations    | es (42), fr (0) |
| Orphan articles | 3     |
| Unresolved links| 7     |
| Top tags        | stoicism (15), leadership (12), ... |
| Last compiled   | 2026-04-03T15:30:00Z |
| Compilations    | 3     |
```

For translations, count `.md` files in each `wiki-<lang>/` directory. Show `—` if no translations exist.

---

## 12. Command: publish

```
/knowledge-wiki publish [--into <project-path>]
```

Syncs the wiki vault to a Quartz site repo, commits, and pushes — triggering a Vercel (or similar) deploy. Requires `publishRepo` in `wiki.config.json`.

**Config requirement:**

`wiki.config.json` must include a `publishRepo` field pointing to the absolute path of the Quartz site repo:

```json
{
  "name": "books",
  "language": "en",
  "publishRepo": "/Users/manolo/dev/ai-tools/llm-book-wiki",
  "sources": [...]
}
```

If `publishRepo` is missing, report: "No `publishRepo` configured in wiki.config.json. Add the absolute path to your Quartz site repo." and stop.

**Pipeline:**

1. **Read config:**
   - Load `wiki.config.json` from the project root
   - Validate `publishRepo` exists and the directory is a git repo

2. **Run sync script:**
   ```bash
   cd <publishRepo> && bash sync.sh
   ```
   The sync script handles all content transformations (path rewriting, wikilink rewriting, affiliate tags, etc.). Parse its output for the article counts.

3. **Check for changes:**
   ```bash
   cd <publishRepo> && git status --porcelain
   ```
   If no changes, report "Nothing to publish — site is up to date." and stop.

4. **Commit and push:**
   ```bash
   cd <publishRepo> && git add -A && git commit -m "sync: update wiki content ($(date +%Y-%m-%d))" && git push
   ```

5. **Report** summary:
   ```
   Published!
   ✓ Synced: 428 kb articles + 235 book sources
   ✓ Committed and pushed to origin
   ✓ Deploy triggered at <baseUrl from quartz.config.ts>
   ```

**Notes:**
- The sync script (`sync.sh`) lives in the Quartz repo, not the skill. Each project's sync script handles its own transformations.
- This command never modifies the vault — all changes happen in the Quartz repo's `content/` directory.
- If `git push` fails (e.g., auth issues), report the error and suggest the user run `! cd <publishRepo> && git push` manually.

---

## 13. Script Invocation Patterns

All scripts use the same pattern: JSON input, JSON output, Python 3.

### scan_raw.py

```bash
python3 ~/.claude/skills/knowledge-wiki/scripts/scan_raw.py <project-root>
```

- **Input:** `sys.argv[1]` = absolute path to project root
- **Output:** JSON to stdout
- **Schema:**
  ```json
  {
    "project_root": "/path",
    "raw_files": [{"path": "...", "title": "...", "author": "...", "words": 0, "mtime": "..."}],
    "wiki_articles": [{"path": "...", "title": "...", "sources": [], "tags": [], "words": 0, "compiled_date": "...", "mtime": "..."}],
    "delta": {"new": [], "modified": [], "unchanged": []},
    "stats": {"total_raw": 0, "total_wiki": 0, "total_raw_words": 0, "total_wiki_words": 0, "coverage": 0.0}
  }
  ```

### obsidian_ingest.py

```bash
echo '<json>' | python3 ~/.claude/skills/knowledge-wiki/scripts/obsidian_ingest.py
```

- **Input:** JSON on stdin: `{"vault": "...", "files": [{"path": "...", "source_type": "...", "title": "...", "author": "...", "source_url": "..."}]}`
- **Output:** JSON to stdout: `{"files_processed": N, "results": [...]}`

### obsidian_post_compile.py

```bash
echo '<json>' | python3 ~/.claude/skills/knowledge-wiki/scripts/obsidian_post_compile.py
```

- **Input:** JSON on stdin: `{"project_root": "...", "vault": "...", "files": ["wiki/concepts/file.md", ...]}`
- **Output:** JSON to stdout: `{"files_processed": N, "file_results": [...], "unresolved_links": [...], "tag_distribution": [...], "moc_rebuilt": true}`

---

## 14. Critical Instructions

**When the user invokes any compile, query, health, or enrich command, follow the pipeline exactly. Do NOT skip steps. Do NOT reorder steps.**

- **NEVER skip post-compile:** After any subagent writes wiki files, ALWAYS run `obsidian_post_compile.py`. This is what sets Obsidian properties and rebuilds the MOC.
- **NEVER skip the manifest scan:** Before compile, ALWAYS run `scan_raw.py` to get the delta. Don't guess which files need processing.
- **NEVER modify raw/ files.** They are read-only source material.
- **Load references when needed:**
  - `references/compilation-prompts.md` — when building prompts for subagent dispatch
  - `references/wiki-structure.md` — when creating new projects or checking article format
  - `references/program-template.md` — during init to generate PROGRAM.md
  - Obsidian skill's `references/commands.md` — for Obsidian CLI syntax details
- **Subagent prompt always starts with:** "Read PROGRAM.md at `<project_root>`" so the subagent has full compilation context.
- **All wiki output in the project's configured language** (from `wiki.config.json` field `language`).
- **Model selection is automatic.** Never ask the user which model to use — follow the table in Section 3.
