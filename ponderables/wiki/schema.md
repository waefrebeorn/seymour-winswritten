# SEYMOUR WIKI — Schema

This document tells Hermes how the Seymour wiki is structured, what conventions to follow, and what workflows to use when ingesting sources, answering questions, or maintaining the wiki. This is the key configuration file that makes the LLM a disciplined wiki maintainer.

---

## Wiki Root

```
/home/wubu/seymour-project/ponderables/wiki/
```

## Directory Structure

```
wiki/
├── index.md              # Content catalog — all pages listed with summaries
├── log.md                # Append-only chronological log
├── schema.md             # This file — conventions and workflow
├── raw/                  # Raw sources (immutable, read-only)
│   ├── youtube/          # Transcript files from YouTube extraction
│   ├── articles/         # Web articles, blog posts
│   └── books/            # Book excerpts, research papers
├── pages/                # Wiki pages (LLM-maintained)
│   ├── entities/         # People, characters, creators
│   ├── concepts/         # Meme types, ideas, frameworks
│   ├── sources/          # Summaries of raw sources
│   ├── entries/          # Ponderable-style entries written as standalone pages
│   └── topics/           # Cross-cutting topic overviews
└── assets/               # Downloaded images, clipart references
```

## Conventions

### Page Format

- Plain markdown files, `.md` extension
- YAML frontmatter at top: `---`, tags, date, source count, status
- First heading is the page title
- Cross-links use relative paths: `[The Colonel](../entities/colonel.md)`
- Every entity/concept page ends with a "References" section linking to source pages

### Frontmatter Template

```yaml
---
title: "Page Title"
created: "2026-06-25"
updated: "2026-06-25"
tags: [entity, meme, clipart]
sources: 3
status: draft | active | stale
---
```

### Index Format (index.md)

Each entry:
```
- [Page Title](relative/path) — one-liner summary | date | tags
```

### Log Format (log.md)

Each entry:
```
## [2026-06-25] ingest | Source Title
Keypoints: key1, key2, key3
Pages touched: concepets/foo.md, entities/bar.md
---
```

---

## Operations

### Ingest

When a new raw source is added to `raw/`:
1. Read the source, extract key takeaways
2. Write a summary page in `pages/sources/`
3. Create/update relevant entity pages in `pages/entities/`
4. Create/update relevant concept pages in `pages/concepts/`
5. If the source inspires a Ponderable-style entry, write to `pages/entries/`
6. Update `index.md` — add new pages, update modified pages
7. Append entry to `log.md`
8. Cross-link all touched pages

### Query

When answering a wiki question:
1. Read `index.md` to find relevant pages
2. Read relevant pages
3. Synthesize answer with citations `[→ pagename](relative/link)`
4. If the answer is substantial (table, comparison, deep analysis), file it back as a new page in `pages/topics/` and update `index.md`

### Lint (run periodically)

Health-check:
- Pages with no inbound links (orphans)
- `stale` pages vs current sources
- Concepts/entities mentioned but missing pages
- Cross-reference consistency
- Index — all present pages listed
- Contradictions between pages

---

## Domain-Specific Rules

### Ponderables

- When a book concept maps naturally to a wiki page, create it
- Maintain cross-volume cross-references as the wiki grows
- Each book can be represented as a topic page linking to its entries

### Meme Knowledge Base

- Entities = memes, platforms, creators, companies
- Concepts = virality, meme types, cultural phenomena
- Sources = YouTube transcripts, articles, books
- Entries = Seymour-style mini-essays that synthesize multiple sources

### Clipart Archive

- Store metadata in `pages/entities/clipart-archive.md`
- Link specific images to entries they appear in

---

## Human's Job

- Curate sources (drop videos, articles into `raw/`)
- Ask questions, probe deeper
- Review important entries
- Direct emphasis and tone

## LLM's Job

- All wiki maintenance grunt work
- Cross-referencing, consistency, index updates
- Summaries and synthesis
- Catching gaps and suggesting new sources
