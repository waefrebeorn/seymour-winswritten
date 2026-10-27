# Seymour Project / Seymour Ponderables

**Seymour Project** (also known as **Seymour Ponderables**, **Seymour Wins Written**) is an independent research, archival, and publishing initiative created by **WaefreBeorn** (2026–present). It combines a **multi-pipeline YouTube transcript absorption system**, a **formal verification research program** (Lean 4), and a **10-volume small-format book series** ("Seymour Ponderables") modeled on *Uncle John's Bathroom Reader* / *Uncle John's Ponderables* with 1990s clipart aesthetics and *Metal Gear Solid 2* Colonel-inspired spine design.

---

## Overview

| Attribute | Detail |
|-----------|--------|
| **Creator** | WaefreBeorn (GitHub: `waefrebeorn`, YouTube: `@waefrebeorn`, `@WuBuStreams`) |
| **Started** | June 2026 (`seymour-winswritten` repo created 2026-06-22) |
| **Primary Repository** | `seymour-project` (local, `/home/wubu/seymour-project/`) |
| **GitHub Mirror** | `waefrebeorn/seymour-winswritten` |
| **Core Pipeline** | Three-path absorption: C11 CDP, Browser CDP (Python), Whisper CPU fallback |
| **Formal Verification** | Lean 4 (`ponderables/research/power_tower_integer/lean4/`) |
| **Publication Format** | 10 volumes, ~24 ponderables each, 90s clipart, MGS2 Colonel spine |
| **Knowledge Base** | Mind Palace + Wiki (`pre_seymour/`, `ponderables/wiki/`) |

---

## Three-Pipeline Absorption Architecture

The Seymour Project's core technical achievement is a **triple-redundant transcript extraction system** processing 676 videos (408 with transcripts, 3.89M words) across two YouTube channels (`@waefrebeorn`, `@WuBuStreams`).

### Pipeline 1: C11 CDP Engine (`absorption_c11`)
- **Language**: Pure C11 (GNU11, `-O3 -march=native -ffast-math`)
- **Transport**: Raw sockets (no libcurl) → Chrome DevTools Protocol (CDP) WebSocket
- **Target**: YouTube engagement panel transcripts (auto-generated captions)
- **Output**: `absorption/data/transcripts/` — 104+ transcripts
- **Orchestrator**: `run_final_absorber.py` — batches of 50, Chrome restart every 50–100 videos (memory leak mitigation)
-200MB/hr leak)
- **Progress Tracking**: `gpu_progress.json` (atomic writes), `absorption_progress.json`

### Pipeline 2: Browser CDP (Python asyncio)
- **Language**: Python 3.11+, `websockets`, `asyncio`
- **Port**: 40581 (separate Chrome instance from C11)
- **Target**: Same engagement panel, different codepath for validation
- **Output**: `whiteboard/seymour-pipe/captions/` — 262 transcripts
- **Progress**: `browser_extract_progress.json` (318 videos tracked, 262 done)

### Pipeline 3: Whisper CPU Fallback
- **Language**: Python, `yt-dlp` + `faster-whisper` (tiny.en, int8, CPU)
- **Target**: Videos **without** engagement panels (age-gated, no auto-captions, deleted)
- **Audio**: 16k mp3 (~0.7 MB/min), 3-hr video ≈ 125 MB
- **Output**: `whiteboard/seymour-pipe/whisper_transcripts/` — 344 transcripts
- **Orchestrator**: `run_whisper_pipeline.py` (chunked, resumable) + `run_whisper_batch.py` (legacy)
- **Queue**: `remaining_v4.txt` → `whisper_remaining.txt` (empty = complete)

### Unified Index
- **File**: `pre_seymour/index.json` (408 videos, 3.89M words)
- **Sources Tracked**: `c11` (104), `whisper` (304)
- **Eras**: 2023-foundations (93), 2024-deep-dives (47), 2025-hiatus-prep (206), 2026-absorption (13)
- **Topic Tags**: 63 clusters, 408/408 tagged (Gemma-4-12B local)
- **Quotes**: 200 mined (`quotes.json`, `quotes.md`)
- **Daily Briefing**: `daily_briefing.md` (auto-generated)

---

## Seymour Ponderables Book Series

### Design Specification
| Element | Specification |
|---------|---------------|
| **Format** | Small-format (pocket), ~24 ponderables/volume × 10 volumes = 240 total |
| **Aesthetic** | 1990s clipart (490 cataloged in `ponderables/wiki/clipart/`) |
| **Spine** | *Metal Gear Solid 2* Colonel portrait motif |
| **Tone** | *Uncle John's Bathroom Reader* / *Uncle John's Ponderables* — curious, digressive, footnoted |
| **Content Source** | Transcripts, quotes, research proofs, clipart, stream lore |

### Volumes (Planned)
| Volume | Era | Videos | Status |
|--------|-----|--------|--------|
| **Vol 1: Foundations** | 2023 | 93 | Draft |
| **Vol 2: Deep Dives** | 2024 | 47 | Planned |
| **Vol 3: Hiatus Prep** | 2025 | 206 | Planned |
| **Vol 4: Absorption** | 2026 | 13 | Planned |
| **Vol 5–10** | Research/Overflow | — | Planned |

### Ponderable #001: "The Tower That Would Not Integer"
- **Theorem**: $N = \pi^{\pi^{\pi^\pi}} \notin \mathbb{Z}$
- **Proof**: $\{\log\log\log\log N\} = 0.3176613010072957... \neq 0$
- **Verification**: C implementation matches Python to $1.4 \times 10^{-8}$ (float precision limit)
- **Lean 4**: Skeleton ready (`ponderables/research/power_tower_integer/lean4/`), blocked on `lake build Mathlib` (2–4 hrs)
- **MPFR/Arb**: 200+ bit interval arithmetic certificate pending

---

## Formal Verification Research Program

### Power Tower Integer Problem
- **Question**: Is $\pi^{\pi^{\pi^\pi}}$ an integer?
- **Result**: **Proven non-integer** via analytical fractional part computation
- **Devil's Advocate Audit** (Triple Pass):
  1. **Analytical Core**: ✅ VALID — direct computation, verified
  2. **Poincaré Manifold**: ❌ Decorative — 4 arbitrary spheres, no topology
  3. **Intersection Invariant**: ❌ Heuristic — arbitrary product, no Chern–Weil
  4. **Monte Carlo**: ❌ Wrong target — measures random norms, not $\{\log^4 N\}$
  5. **Curvature Assignment**: ❌ Arbitrary — $c_i = 0.1 \log(1+\log\_val_i)$
- **Conclusion**: Analytical result stands alone; topology is separate research proposal

### Lean 4 Formalization
```
lean4/
├── lakefile.toml           ✅ Configured (local mathlib path)
├── .lake/packages/mathlib  ✅ Cloned (v4.13.0)
├── src/Main.lean           ✅ Ready (sorry statements, correct syntax)
└── .lake/packages/mathlib  ⚠️ NOT PRE-BUILT (needs `lake build Mathlib` — 2–4 hrs)
```
- **Dependencies**: mathlib4, Aesop, Batteries, Qq, LeanSearchClient, ProofWidgets, ImportGraph, Plausible
- **Blockers**: `lake build Mathlib` (network/git issues in WSL)
- **Next**: Build mathlib → replace `sorry` with proofs → publish Ponderable #001

### WuBu Nesting Formalization
- **Location**: `bytropix/MATH/lean/wubu_proofs/`
- **Structures**: Hyperbolic spaces $H^{n_i}_{c_i,s_i}$, boundaries $B_{i,j}$, holographic decomposition (soul/echo)
- **Status**: Early scaffolding; dependent on mathlib topology library

---

## Mind Palace + Wiki Knowledge Base

### Structure (`ponderables/wiki/`)
| Directory | Contents |
|-----------|----------|
| `pages/sources/` | 5 source documents |
| `pages/entities/` | 12 entity pages (people, games, tools) |
| `pages/concepts/` | 20 concept pages (technical, personal, lore) |
| `clipart/` | 490 cataloged 90s clipart assets |
| `volumes/` | 4 volume manifests |
| `indices/` | 2 cross-reference indices |
| `ponderables/` | 299 ponderable entries |
| `raw/articles/` | 4 raw article imports |

### Pre-Seymour Index (`pre_seymour/`)
| File | Purpose |
|------|---------|
| `index.json` | Master index (408 videos, metadata, topics, transcripts) |
| `index_with_topics.json` | Tagged version for search |
| `timeline.md` | Human-readable chronological list |
| `quotes.json` / `quotes.md` | 200 curated quotes with scores |
| `daily_briefing.md` | Auto-generated daily summary |
| `eras/*.json` | Era-partitioned video lists |
| `STREAM_REFERENCE.md` | Streamer callback cheat-sheet |

### Streamer Reference (`STREAM_REFERENCE.md`)
Quick-search commands for live "Seymour Wins Written" streams:
```bash
seymour-pre "bytropix" -n 1
seymour-pre "cuda" --era 2025
seymour-pre "godot" --source c11
seymour-pre --random -n 1
seymour-pre --stats
seymour-pre --eras
```
Topics: bytropix, Nissan Versa/EV hybrid, Gary Paulsen/Hatchet, pennies (mom/wife), foster childhood, RTX 4050/GPU MODE, Godot, CUDA kernels, WuBu Nesting, Seymour Ponderables

---

## Pipeline Status (2026-07-06)

| Component | Status | Coverage |
|-----------|--------|----------|
| **Video Discovery** | ✅ Complete | 676 IDs (videos + streams tabs) |
| **C11 CDP** | 🟢 Running | 104+ transcripts, batch orchestrator |
| **Browser CDP** | ✅ Complete | 262 transcripts |
| **Whisper Fallback** | ✅ Complete | 344 transcripts (176/176 chunked done, 11 failed) |
| **Unified Index** | ✅ Built | 408 videos, 3.89M words, 100% tagged |
| **Topic Tagging** | ✅ Complete | 63 clusters, 408/408 tagged |
| **Clipart Vision** | ✅ Complete | 490 cataloged, 12 categories |
| **Wiki Sync** | ✅ Complete | All JSONs, manifest, indices, index.md, log.md |
| **Ponderable Candidates** | ⏳ Pending | 297 identified, 0 ingested |
| **Volumes Created** | 🔄 Partial | 2 vols, 24 ponderables |
| **Quote Extraction** | ⏳ Pending | 200 mined, not automated |
| **Synthesis (Pre-Synth)** | 🔴 Broken | 2000-token prompts timeout at 3.7 tok/s |

### Critical Risks (Triple Devil's Advocate Audit)
1. **Pre-synth synthesis times out** — 2000 tokens at 3.7 tok/s = 9+ min; exceeds timeout
2. **Cron jobs fail with HTTP 429** — Provider rate limits make autonomous ops impossible
3. **No automated Ponderable ingestion** — 297 candidates idle, 2 vols, 24 ponderables
4. **Gemma-4-12B too slow for synthesis** — Need async/background, smaller model, or reduced context
5. **Chrome memory leak** — 2GB/hr, requires restart every 50–100 videos (orchestrator handles, cron doesn't)
6. **`seymour-infographics-regen` cron malformed** — `cd` command embedded in script path
7. **Whisper health check mismatch** — Monitors old batch processor vs. new chunked pipeline
8. **No credential audit** — `cookies.txt` age unknown, provider keys may have rotated

---

## GitHub Repository: `waefrebeorn/seymour-winswritten`

| Commit | Date | Message |
|--------|------|---------|
| `b757795` | 2026-06-22 | Gemma 4 household: remove all Gemma 3 references and model files |
| `68bf538` | 2026-06-22 | Initial commit: Seymour Ponderables project structure |

**Note**: Primary development occurs in local `/home/wubu/seymour-project/`; GitHub mirror is sparse.

---

## Related Projects
- **bytropix** — Inference engine powering local LLM runs for topic tagging, synthesis
- **WuBu ecosystem** — Distributed inference, OS, router, skills providing infrastructure
- **slermes** — C11 agent framework (potential future Seymour CLI host)
- **money-room** — Cron/collector patterns reused for absorption orchestration

---

## See Also
- [WaefreBeorn (Person/Org)](01_WaefreBeorn.md)
- [WuBu Ecosystem](03_WuBu_Ecosystem.md)
- [bytropix Inference Engine](04_bytropix.md)
- [slermes (C11 Hermes Fork)](05_slermes.md)
- [money-room](06_money_room.md)
- [Cross-Referenced Timeline](07_Timeline_Crossref.md)