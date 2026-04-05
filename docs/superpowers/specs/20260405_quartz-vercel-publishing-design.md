# Quartz + Vercel Publishing — Design Spec

## Overview

Publish the 428-article knowledge wiki (compiled from 235 Kindle highlight exports) as a public, browsable static site using Quartz v4 on Vercel. The wiki vault stays untouched — a sync script copies content into a separate Quartz repo that Vercel auto-deploys on push.

## Goals

- **Public showcase** of the compiled wiki with interactive graph, backlinks, search, and tag navigation
- **Full traceability** — visitors can follow any citation back to the raw Kindle highlight
- **Zero cost** — Vercel Hobby tier, static output, no serverless functions
- **Vault integrity** — the Obsidian vault is never modified; all transformations happen in the Quartz repo copy

## Architecture

```
Wiki Vault (source of truth)                  Quartz Repo (published site)
─────────────────────────────                 ──────────────────────────────
books/                                        llm-book-wiki/
├── wiki/                    ──sync.sh──►     ├── content/
│   ├── concepts/ (205)                       │   ├── index.md (← MOC renamed)
│   ├── authors/ (175)                        │   ├── wiki/
│   ├── themes/ (37)                          │   │   ├── concepts/
│   └── connections/ (11)                     │   │   ├── authors/
├── raw/                                      │   │   ├── themes/
│   └── notas-libros/ (235)                   │   │   └── connections/
├── MOC - Knowledge Wiki.md                   │   └── raw/
├── PROGRAM.md (excluded)                     │       └── notas-libros/
├── wiki.config.json (excluded)               ├── quartz.config.ts
├── .compile-state.json (excluded)            ├── quartz.layout.ts
└── outputs/ (excluded)                       ├── sync.sh
                                              ├── vercel.json
                                              └── public/ (build output)
```

**Two separate repos:**

| Repo | Purpose | URL |
|------|---------|-----|
| `claude-knowledge-wikis` | Skill definition, scripts, references | `github.com/manoloalvarez/claude-knowledge-wikis` |
| `llm-book-wiki` | Quartz site with wiki content, deployed on Vercel | `github.com/manoloalvarez/llm-book-wiki` |

## Wikilink Resolution

The wiki uses full-path wikilinks: `[[wiki/concepts/first-principles-thinking|First-Principles Thinking]]`. Quartz's CrawlLinks plugin resolves these natively in `absolute` mode — paths are resolved relative to the content folder root.

**Resolution examples:**

| Wikilink in source | Resolves to |
|--------------------|-------------|
| `[[wiki/concepts/flow-state-and-peak-performance]]` | `content/wiki/concepts/flow-state-and-peak-performance.md` |
| `[[wiki/authors/andrew-grove\|Andrew S. Grove]]` | `content/wiki/authors/andrew-grove.md` (displays "Andrew S. Grove") |
| `[[raw/notas-libros/High Output Management]]` | `content/raw/notas-libros/High Output Management.md` |

**No path rewriting or content transformation required.** All links work as-is.

## Quartz Configuration

### quartz.config.ts

```typescript
const config: QuartzConfig = {
  configuration: {
    pageTitle: "Manolo's LLM Generated Book Wiki",
    pageTitleSuffix: "",
    enableSPA: true,
    enablePopovers: true,
    locale: "en-US",
    baseUrl: "llm-book-wiki.vercel.app", // Update after Vercel assigns actual URL
    ignorePatterns: [
      "private",
      "templates",
      ".obsidian",
    ],
    defaultDateType: "modified",
    theme: {
      // See Theme section below
    },
  },
  plugins: {
    transformers: [
      Plugin.FrontMatter(),
      Plugin.CreatedModifiedDate({ priority: ["frontmatter", "filesystem"] }),
      Plugin.SyntaxHighlighting(),
      Plugin.ObsidianFlavoredMarkdown({ enableInHtmlBlock: false }),
      Plugin.GitHubFlavoredMarkdown(),
      Plugin.TableOfContents(),
      Plugin.CrawlLinks({
        markdownLinkResolution: "absolute",
        prettyLinks: true,
        openLinksInNewTab: false,
        lazyLoad: true,
      }),
      Plugin.Description(),
      Plugin.Latex({ renderEngine: "katex" }),
    ],
    filters: [
      Plugin.RemoveDrafts(),
      // ExplicitPublish NOT used — all content is published
    ],
    emitters: [
      Plugin.AliasRedirects(),
      Plugin.ComponentResources(),
      Plugin.ContentPage(),
      Plugin.FolderPage(),
      Plugin.TagPage(),
      Plugin.ContentIndex({ enableSiteMap: true, enableRSS: true }),
      Plugin.Assets(),
      Plugin.Static(),
      Plugin.NotFoundPage(),
    ],
  },
}
```

### Theme

Dark theme matching the existing Marp slides aesthetic:

```typescript
theme: {
  cdnCaching: true,
  typography: {
    header: "Helvetica Neue",
    body: "Helvetica Neue",
    code: "JetBrains Mono",
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

### quartz.layout.ts

```typescript
// Left sidebar
sharedPageComponents: {
  head: Component.Head(),
  header: [],
  afterBody: [],
  footer: Component.Footer({
    links: {
      "Blog": "https://manoloalvarez.blog",
      "Podcast": "https://conceptos.blog",
      GitHub: "https://github.com/manoloalvarez",
    },
  }),
},

// Layout: left sidebar + content + right sidebar
beforeBody: [
  Component.Breadcrumbs(),
  Component.ArticleTitle(),
  Component.ContentMeta(),
  Component.TagList(),
],
left: [
  Component.PageTitle(),
  Component.MobileOnly(Component.Spacer()),
  Component.Search(),
  Component.Darkmode(),
  Component.Explorer(),
],
right: [
  Component.Graph(),
  Component.TableOfContents(),
  Component.Backlinks(),
],
```

## Features Enabled

| Feature | Quartz Component | Purpose |
|---------|-----------------|---------|
| Interactive graph | `Component.Graph()` | Visual exploration of concept connections |
| Backlinks | `Component.Backlinks()` | "What links here" on every article |
| Full-text search | `Component.Search()` | Client-side, instant, free |
| Tag index pages | `Plugin.TagPage()` | Auto-generated page per tag |
| Table of contents | `Component.TableOfContents()` | Right sidebar on longer articles |
| Explorer | `Component.Explorer()` | Left sidebar folder tree |
| Page preview popovers | `enablePopovers: true` | Hover wikilinks to preview |
| Dark/light toggle | `Component.Darkmode()` | User preference, dark default |
| Breadcrumbs | `Component.Breadcrumbs()` | Path navigation (wiki > concepts > article) |
| Alias redirects | `Plugin.AliasRedirects()` | Frontmatter `aliases` generate redirect pages |
| RSS feed | `Plugin.ContentIndex()` | Auto-generated feed |
| Sitemap | `Plugin.ContentIndex()` | For search engine indexing |

**Features NOT enabled:**
- `ExplicitPublish` — all content publishes (no opt-in flag needed)
- Reading time — not useful for a reference wiki

## Sync Script

`sync.sh` — copies content from the vault into the Quartz repo. Run after each `/knowledge-wiki compile`.

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

Key detail: `cp -rL` on the raw directory **resolves the symlink** and copies actual files (required because Vercel builds from git, not local filesystem).

## Content Transformations During Sync

All transformations happen on the Quartz repo copy, never on the vault:

1. **MOC rename**: `MOC - Knowledge Wiki.md` → `index.md` (becomes homepage)
2. No other transformations needed — wikilinks, frontmatter, tags all work natively

## Vercel Deployment

### Configuration

| Setting | Value |
|---------|-------|
| Framework preset | Other |
| Build command | `npx quartz build` |
| Output directory | `public` |
| Node version | 22 |
| Plan | Hobby ($0/month) |

### vercel.json

```json
{
  "cleanUrls": true
}
```

### Deployment Workflow

```
/knowledge-wiki compile  →  cd llm-book-wiki  →  ./sync.sh  →  git add + commit + push  →  Vercel auto-deploys
```

Vercel watches the `main` branch. Every push triggers a build. No CI/CD config needed beyond the defaults.

## URL Structure

Quartz generates clean URLs from the content directory structure:

| Content file | Published URL |
|-------------|---------------|
| `content/index.md` | `/` (homepage) |
| `content/wiki/concepts/first-principles-thinking.md` | `/wiki/concepts/first-principles-thinking` |
| `content/wiki/authors/andrew-grove.md` | `/wiki/authors/andrew-grove` |
| `content/wiki/themes/the-examined-self-...md` | `/wiki/themes/the-examined-self-...` |
| `content/raw/notas-libros/High Output Management.md` | `/raw/notas-libros/High-Output-Management` |

## Future Enhancements (Out of Scope)

- **`/knowledge-wiki publish` command**: Automate sync + commit + push from the skill
- **Custom domain**: `wiki.manoloalvarez.blog` or `books.manoloalvarez.blog`
- **Analytics**: Plausible or Umami via Quartz's analytics config
- **Custom CSS**: Article type styling (concepts vs authors vs themes)
- **Automatic deploy on compile**: Git hook or skill integration
