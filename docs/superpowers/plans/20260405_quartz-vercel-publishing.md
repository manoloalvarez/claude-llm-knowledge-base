# Quartz + Vercel Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the 428-article knowledge wiki as a static site on Vercel using Quartz v4.

**Architecture:** Clone Quartz into a new repo (`llm-book-wiki`), sync wiki content via a shell script, configure theme/plugins/layout, deploy to Vercel. The wiki vault is never modified — all work happens in the Quartz repo.

**Tech Stack:** Quartz v4, Node.js 22, Vercel (Hobby tier), TypeScript config

**Spec:** `docs/superpowers/specs/20260405_quartz-vercel-publishing-design.md`

---

## File Structure

| File | Responsibility |
|------|---------------|
| `quartz.config.ts` | Modify: site title, theme colors, font, link resolution, analytics removal |
| `quartz.layout.ts` | Modify: footer links, component arrangement |
| `sync.sh` | Create: copies wiki vault content into `content/` |
| `vercel.json` | Create: clean URLs config |
| `.gitignore` | Modify: ensure `content/` is NOT ignored (Quartz default may ignore it) |
| `content/index.md` | Created by sync.sh from MOC |
| `content/wiki/**` | Created by sync.sh from vault |
| `content/raw/**` | Created by sync.sh from vault |

---

### Task 1: Clone Quartz and Create GitHub Repo

**Files:**
- Create: `/Users/manolo/dev/ai-tools/llm-book-wiki/` (entire Quartz scaffold)

- [ ] **Step 1: Clone Quartz v4**

```bash
cd /Users/manolo/dev/ai-tools
git clone https://github.com/jackyzha0/quartz.git llm-book-wiki
cd llm-book-wiki
```

- [ ] **Step 2: Install dependencies**

```bash
npm i
```

Expected: successful install, `node_modules/` created.

- [ ] **Step 3: Remove Quartz's default content and upstream remote**

```bash
rm -rf content/*
git remote remove origin
```

Quartz ships with sample content in `content/`. We replace it with our wiki content.

- [ ] **Step 4: Create GitHub repo and set as origin**

```bash
gh repo create manoloalvarez/llm-book-wiki --public --source=. --remote=origin
```

Expected: repo created at `github.com/manoloalvarez/llm-book-wiki`.

- [ ] **Step 5: Verify project structure**

```bash
ls quartz.config.ts quartz.layout.ts package.json
ls -d content/
```

Expected: all files exist, `content/` is empty.

- [ ] **Step 6: Commit clean slate**

```bash
git add -A
git commit -m "chore: initialize Quartz with empty content"
```

---

### Task 2: Create sync.sh and Run Initial Content Sync

**Files:**
- Create: `sync.sh`

- [ ] **Step 1: Create sync.sh**

Write this file to `/Users/manolo/dev/ai-tools/llm-book-wiki/sync.sh`:

```bash
#!/bin/bash
set -euo pipefail

VAULT="/Users/manolo/Documents/Documents - Manolos MacBook Pro/llm-knowledge/books"
CONTENT="./content"

echo "Syncing wiki vault → Quartz content..."

# Clean previous content
rm -rf "$CONTENT/wiki" "$CONTENT/raw"

# Copy wiki articles
cp -r "$VAULT/wiki" "$CONTENT/wiki"

# Copy raw sources (resolve symlink, copy actual files)
mkdir -p "$CONTENT/raw"
cp -rL "$VAULT/raw/notas-libros" "$CONTENT/raw/notas-libros"

# MOC → index.md (homepage)
cp "$VAULT/MOC - Knowledge Wiki.md" "$CONTENT/index.md"

# Count
WIKI_COUNT=$(find "$CONTENT/wiki" -name "*.md" | wc -l | tr -d ' ')
RAW_COUNT=$(find "$CONTENT/raw" -name "*.md" | wc -l | tr -d ' ')
echo "Synced: $WIKI_COUNT wiki articles + $RAW_COUNT raw sources"
```

- [ ] **Step 2: Make sync.sh executable**

```bash
chmod +x sync.sh
```

- [ ] **Step 3: Run the initial sync**

```bash
./sync.sh
```

Expected output:
```
Syncing wiki vault → Quartz content...
Synced: 428 wiki articles + 235 raw sources
```

- [ ] **Step 4: Verify content structure**

```bash
ls content/index.md
ls content/wiki/concepts/ | head -5
ls content/wiki/authors/ | head -5
ls content/wiki/themes/ | head -5
ls content/wiki/connections/ | head -5
ls content/raw/notas-libros/ | head -5
```

Expected: `index.md` exists, all five directories have `.md` files.

- [ ] **Step 5: Check .gitignore does not exclude content/**

```bash
grep -n "content" .gitignore
```

If `content/` or `content` is listed in `.gitignore`, remove that line. The content must be committed for Vercel to build it.

- [ ] **Step 6: Commit**

```bash
git add sync.sh content/
git commit -m "feat: add sync script and initial wiki content (663 articles)"
```

---

### Task 3: Configure quartz.config.ts

**Files:**
- Modify: `quartz.config.ts`

- [ ] **Step 1: Read the current default config**

Read `quartz.config.ts` to understand the exact current structure before making changes.

- [ ] **Step 2: Update site identity and configuration**

In the `configuration` block, make these changes:

```typescript
configuration: {
  pageTitle: "Manolo's LLM Generated Book Wiki",
  pageTitleSuffix: "",
  enableSPA: true,
  enablePopovers: true,
  // Remove analytics block entirely (no analytics for now)
  locale: "en-US",
  baseUrl: "llm-book-wiki.vercel.app",
  ignorePatterns: ["private", "templates", ".obsidian"],
  defaultDateType: "modified",
```

Changes from default:
- `pageTitle`: "Quartz 4" → "Manolo's LLM Generated Book Wiki"
- `analytics`: remove the entire `analytics: { provider: "plausible" }` block
- `baseUrl`: "quartz.jzhao.xyz" → "llm-book-wiki.vercel.app"

- [ ] **Step 3: Update theme colors and typography**

Replace the entire `theme` block:

```typescript
  theme: {
    fontOrigin: "googleFonts",
    cdnCaching: true,
    typography: {
      header: "Schibsted Grotesk",
      body: "Source Sans Pro",
      code: "IBM Plex Mono",
    },
    colors: {
      lightMode: {
        light: "#faf8f8",
        lightgray: "#e5e5e5",
        gray: "#b8b8b8",
        darkgray: "#4e4e4e",
        dark: "#1a1a2e",
        secondary: "#e94560",
        tertiary: "#0f3460",
        highlight: "rgba(233, 69, 96, 0.15)",
        textHighlight: "#e9456033",
      },
      darkMode: {
        light: "#1a1a2e",
        lightgray: "#2a2a4a",
        gray: "#646480",
        darkgray: "#b0b0c0",
        dark: "#e0e0e0",
        secondary: "#e94560",
        tertiary: "#5a8fd8",
        highlight: "rgba(233, 69, 96, 0.15)",
        textHighlight: "#e9456033",
      },
    },
  },
```

Note: keep `fontOrigin: "googleFonts"` and the default fonts (Schibsted Grotesk / Source Sans Pro / IBM Plex Mono) — they're well-tested with Quartz's layout. Helvetica Neue is a system font that may not render consistently across platforms. Only the colors change.

- [ ] **Step 4: Update CrawlLinks plugin to absolute resolution**

In the `plugins.transformers` array, change the CrawlLinks plugin:

```typescript
Plugin.CrawlLinks({
  markdownLinkResolution: "absolute",
  prettyLinks: true,
  openLinksInNewTab: false,
  lazyLoad: true,
}),
```

Change from default: `markdownLinkResolution`: "shortest" → "absolute". Add `prettyLinks: true`, `openLinksInNewTab: false`, `lazyLoad: true`.

- [ ] **Step 5: Verify no other plugin changes needed**

Leave all other plugins at their defaults. Specifically keep:
- `Plugin.Favicon()` and `Plugin.CustomOgImages()` in emitters (good for public showcase)
- `Plugin.RemoveDrafts()` in filters
- All default transformers

- [ ] **Step 6: Test build**

```bash
npx quartz build
```

Expected: build completes successfully, `public/` directory created with HTML files. Check for errors in output — especially link resolution warnings.

- [ ] **Step 7: Commit**

```bash
git add quartz.config.ts
git commit -m "feat: configure site title, dark theme, absolute link resolution"
```

---

### Task 4: Configure quartz.layout.ts

**Files:**
- Modify: `quartz.layout.ts`

- [ ] **Step 1: Read the current default layout**

Read `quartz.layout.ts` to understand the exact current structure.

- [ ] **Step 2: Update footer links**

Find the `Component.Footer` block and replace the links:

```typescript
Component.Footer({
  links: {
    Blog: "https://manoloalvarez.blog",
    Podcast: "https://conceptos.blog",
    GitHub: "https://github.com/manoloalvarez",
  },
}),
```

Change from default: replaces Quartz GitHub/Discord links with Manolo's blog, podcast, and GitHub.

- [ ] **Step 3: Verify layout components**

The default Quartz layout already includes the components we need:
- Left sidebar: PageTitle, Search, Darkmode, Explorer
- Right sidebar: Graph, TableOfContents, Backlinks
- Before body: Breadcrumbs, ArticleTitle, ContentMeta, TagList

No other layout changes needed — the defaults match the spec.

- [ ] **Step 4: Test build and preview**

```bash
npx quartz build --serve
```

Open `http://localhost:8080/` in a browser. Verify:
- Homepage shows the MOC content (Authors, Concepts, Themes, etc.)
- Dark theme colors are applied (#1a1a2e background, #e94560 accents)
- Left sidebar has Explorer, Search, Dark mode toggle
- Click a concept link (e.g., "First-Principles Thinking") — should navigate to the article
- Right sidebar shows Graph, Table of Contents, Backlinks
- Click a raw source link in an article — should navigate to the Kindle highlight
- Graph view shows interconnected nodes
- Search works (try "stoicism")
- Footer shows Blog, Podcast, GitHub links

Press Ctrl+C to stop the server.

- [ ] **Step 5: Commit**

```bash
git add quartz.layout.ts
git commit -m "feat: update footer with blog, podcast, and GitHub links"
```

---

### Task 5: Create vercel.json and Deploy

**Files:**
- Create: `vercel.json`

- [ ] **Step 1: Create vercel.json**

Write to `/Users/manolo/dev/ai-tools/llm-book-wiki/vercel.json`:

```json
{
  "cleanUrls": true
}
```

- [ ] **Step 2: Commit vercel.json**

```bash
git add vercel.json
git commit -m "feat: add Vercel config for clean URLs"
```

- [ ] **Step 3: Push to GitHub**

```bash
git push -u origin main
```

If Quartz's default branch is `v4` instead of `main`:

```bash
git branch -M main
git push -u origin main
```

- [ ] **Step 4: Import project on Vercel**

```bash
vercel link
```

Or via Vercel dashboard:
1. Go to vercel.com/new
2. Import `manoloalvarez/llm-book-wiki`
3. Framework Preset: **Other**
4. Build Command: `npx quartz build`
5. Output Directory: `public`
6. Deploy

- [ ] **Step 5: Verify deployment**

```bash
vercel ls
```

Open the assigned `.vercel.app` URL. Verify the same checks from Task 4 Step 4 work on the live site:
- Homepage renders with MOC content
- Wiki links resolve correctly
- Raw source links work
- Graph view loads
- Search works
- Dark theme applied

- [ ] **Step 6: Update baseUrl if needed**

If Vercel assigned a URL different from `llm-book-wiki.vercel.app`, update `quartz.config.ts`:

```typescript
baseUrl: "<actual-vercel-url>",
```

Then:

```bash
git add quartz.config.ts
git commit -m "fix: update baseUrl to match Vercel deployment URL"
git push
```

---

### Task 6: Verify End-to-End Update Workflow

This task validates that the sync → push → deploy cycle works.

- [ ] **Step 1: Make a trivial change in the vault**

Open any wiki article in Obsidian and add a comment or minor edit. (Or just verify current state is recent.)

- [ ] **Step 2: Re-run sync**

```bash
cd /Users/manolo/dev/ai-tools/llm-book-wiki
./sync.sh
```

Expected: sync completes, reports article counts.

- [ ] **Step 3: Commit and push**

```bash
git add -A
git commit -m "sync: update wiki content"
git push
```

- [ ] **Step 4: Verify Vercel auto-deploys**

```bash
vercel ls
```

Or check the Vercel dashboard — a new deployment should appear within 1-2 minutes. Verify the change is reflected on the live site.

- [ ] **Step 5: Final commit in skill repo**

Back in the skill repo, commit the spec and plan:

```bash
cd /Users/manolo/dev/ai-tools/knowledge-wikis
git add docs/superpowers/specs/20260405_quartz-vercel-publishing-design.md docs/superpowers/plans/20260405_quartz-vercel-publishing.md
git commit -m "docs: add Quartz + Vercel publishing spec and plan"
git push
```
