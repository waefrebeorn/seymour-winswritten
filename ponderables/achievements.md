# Seymour Wins — Achievements Vault (New Game Plus)

Resolved gaps and shipped milestones. File:line references point at the
artifacts that prove each item is done (not just planned).

## New Game Plus / Mathematic Sprawl (2026-07-07)
- **Stream mining**: TF-IDF over 697 real @wubustreams transcripts (local, no scrape) → `ponderables/mine_themes.py` → `ponderables/topics.json`.
- **Theme sprawl**: 1087 themes generated across 9 axes (base / cross_event / colonel_truth / meme / overlap / decade / meme_fmt / news / format) → `ponderables/sprawl_themes.py` → `ponderables/themes.json` (1087 entries, meta.total_themes=1087).
- **Overlap graph**: 366 distinct dates, 239,083 keyword co-occurrence edges, top-500 serialized → `ponderables/overlap_graph.py` → `ponderables/overlap_index.json`.
- **Colonel-of-truth codec layer**: every one of 366 daily issues carries a `> COLONEL (codec transmission):` line woven from the sprawl theme's `colonel_frame` → `ponderables/theme_router.py` + `fill_year.write_issue` / `remix.write_issue`.
- **Remix / prestige rebuild**: all 366 issues re-themed offline (facts preserved, no re-fetch) through the 1087-theme router → `ponderables/remix.py`. Verified: 366/366 Colonel blocks, 55 distinct sprawl themes actually used, base spread varied (llm 64, penny 56, gun 39, ev 37, versa 19, ...).
- **Annual PDF rebuilt**: `pdf/seymour_wins_2020_annual.pdf` (367 pp incl. cover, ~33 MB) via `build_calendar.py 2020`; vision-verified clean layout, themed clipart, Colonel block present, no overflow.
- **Interesting-facts enrichment**: 46 real public-domain facts as a "TRIPLE-CHECKED" sidebar routed by base theme → `ponderables/interesting_facts.json` + `ponderables/enrich.py`. 366/366 issues enriched.
- **Artwork expanded**: clipart keyword map extended with 8 new NG+ categories (metalgear/gun/colonel/brain/flag/sky/book/key); acquisition re-run via `acquire_clipart.py` (OGA CC0, provenance-tracked).

- **Fill all years 2021-2026**: prefetched 366 dates' full event lists once (6,832 real verified events -> `event_pool.json`), then generated 2,191 issues offline across 6 years with distinct event-per-year assignment. All years 100% Colonel-coded + enriched, 44-48 distinct sprawl themes each. Total project: **2,557 issues (2020-2026), 0 gaps**.
- **Event pool prefetch**: `prefetch_events.py` (366 Wikimedia calls) -> `event_pool.json` (1MB, 6832 events). Enables offline multi-year fill avoiding per-year network throttling.
- **Year fill generator**: `fill_all_ngplus.py` (uses event's REAL year in FACT, not timeline slot; fixed year-mismatch bug found in vision QA).
- **7 annual PDFs rebuilt**: seymour_wins_2020..2026_annual.pdf (each 28-34 MB, vision-verified clean + themed clipart + Colonel + TRIPLE-CHECKED sidebar).

## Resilient Daily System (prior NG+ foundation)
- 5-path fill (Wikimedia / muffinlabs / Wikipedia REST / CC0 bundle / browser-capture daemon) → `ponderables/fill_year.py`, `ponderables/history_fallback.json`.
- Browser capture extension + local daemon → `ponderables/browser_plugin/*`, `ponderables/daily_daemon.py`.
- Coverage: 366/366 for 2020, 0 gaps, even theme spread.

## Clipart provenance
- 758 CC0 SVGs acquired; provenance in `assets/clipart/PROVENANCE.json` (726 entries); MIT-licensed sets quarantined in `assets/clipart/_quarantine/` (609).
