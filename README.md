# Seymour Ponderables — Project Root

This is the root of the Seymour Ponderables knowledge project.

## Wiki

The wiki lives at `ponderables/wiki/` and follows the [LLM Wiki](LLM-WIKI.md) pattern by Karpathy.

- **Schema & conventions** → `wiki/schema.md`
- **Page index** → `wiki/index.md`
- **Change log** → `wiki/log.md`
- **Pages** → `wiki/pages/` (concepts, entities, sources, entries, topics)
- **Raw sources** → `wiki/raw/` (immutable inputs)

## Series Documents

- `SERIES-BIBLE.md` — overall series specification
- `vol1-architecture.md` — Volume 1 (10 books, 114 entries)
- `vol1-production.md` — production pipeline
- `PONDERABLE-001-outline.md` — first book outline

## Other Directories

- `clipart/` — 90s clipart archive
- `quotes/` — MGS2 Colonel quotes and others
- `research/` — research notes
- `whiteboard/` — active working notes
- `docs/` — miscellaneous documentation

## How to Use

Drop raw sources (YouTube transcripts, articles, book notes) into `wiki/raw/`. Hermes will ingest them — reading, extracting, and updating the wiki pages. Ask questions against the wiki at any time.
