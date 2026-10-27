# money-room

**money-room** is an open-source **Bitcoin market prediction engine** built by WaefreBeorn (2026-05-24 → 2026-06-22). It serves as the **architectural pattern source** for the Seymour Project's absorption pipeline — providing the cron-driven collector framework, JSON bridge surfaces, gap-grid tracking, and provider rotation gateway that were adapted for YouTube transcript absorption.

---

## Overview

| Attribute | Detail |
|-----------|--------|
| **Repository** | `waefrebeorn/money-room` |
| **Created** | 2026-05-24 |
| **Last Push** | 2026-06-22 |
| **Language** | C11 (collectors), Python (bridge/orchestration) |
| **Core Engine** | 80-dimensional C11 predictor |
| **Data Layer** | libcurl + jansson + SQLite |
| **Scheduling** | Cron-driven collector binaries |
| **Output** | JSON bridge files + static dashboards |

---

## Architecture (The "Engine Room" Pattern)

money-room implements the **Absorber Monkey Engine Room** skill — a reusable framework for recurring data absorption tasks:

```
┌─────────────────────────────────────────────────────────────────┐
│                      money-room Architecture                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  Cron Jobs   │───►│  Collector   │───►│   SQLite     │      │
│  │  (systemd/   │    │  Binaries    │    │   (prices,   │      │
│  │   cron.d)    │    │  (C11,       │    │   agents,    │      │
│  └──────────────┘    │   libcurl)   │    │   signals)   │      │
│                      └──────┬───────┘    └──────┬───────┘      │
│                             │                   │              │
│                             ▼                   ▼              │
│                      ┌──────────────┐    ┌──────────────┐      │
│                      │  JSON Bridge │    │  Gap Grid    │      │
│                      │  (snapshot   │    │  (PORTED /   │      │
│                      │   files)     │    │   PARTIAL /  │      │
│                      └──────┬───────┘    │   REAL GAP)  │      │
│                             │            └──────────────┘      │
│                             ▼                                 │
│                      ┌──────────────┐                          │
│                      │  Lightweight │                          │
│                      │  C Data      │                          │
│                      │  Server      │                          │
│                      │  (API/JSON)  │                          │
│                      └──────────────┘                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Reusable Components (Adopted by Seymour)

| Component | money-room | Seymour Adaptation |
|-----------|------------|-------------------|
| **Cron Collectors** | BTC price/agent collectors every 5 min | `seymour-pipeline-cycle` (whisper + clipart + wiki) |
| **JSON Bridge** | `data/snapshots/*.json` | `pre_seymour/index.json`, `gpu_progress.json` |
| **Gap Grid** | PORTED/PARTIAL/REAL GAP cells | `whisper_remaining.txt`, `retry_cdp_videos.txt` |
| **Provider Rotation** | Free LLM API gateway | `no_agent=true` cron jobs (zero external LLM calls) |
| **C Data Server** | HTTP JSON API | `seymour_unified.py` CLI (local only) |
| **Benchmark/Probe** | `benchmark_providers.c` → `scorecard.json` | `verify_absorber_cdp.py` pre-flight checks |

---

## Collector Binaries (C11)

| Binary | Purpose | Schedule |
|--------|---------|----------|
| `collect_prices` | Fetch BTC/USDT from exchanges | Every 5 min |
| `collect_agents` | Fetch agent signals from APIs | Every 5 min |
| `collect_stats` | Compute rolling statistics | Every 15 min |
| `benchmark_providers` | Probe free LLM endpoints | Hourly |
| `rotation_cli` | Provider health/rotate CLI | On-demand |

**Build**: `engine/Makefile` — explicit targets, C11 features (`_Static_assert`, `_Alignas`, `atomic_bool`, `_Thread_local`)

---

## Data Flow

### 1. Collection (Cron → C Binary → SQLite)
```bash
# crontab entry
*/5 * * * * /home/wubu/money-room/engine/collect_prices >> /var/log/money-room/prices.log 2>&1
*/5 * * * * /home/wubu/money-room/engine/collect_agents >> /var/log/money-room/agents.log 2>&1
```

### 2. Bridge Generation (Python → JSON)
```python
# scripts/generate_bridge.py (runs after collectors)
import sqlite3, json
conn = sqlite3.connect('data/money_room.db')
# Query latest prices, agents, signals
# Write to data/bridge/latest.json
# Write to data/bridge/history/YYYY-MM-DD.json
```

### 3. Gap Grid Tracking
```json
// data/gaps/grid.json
{
  "BTC_USDT_BINANCE": { "status": "PORTED", "last_update": "2026-06-22T14:30:00Z", "owner": "collect_prices" },
  "AGENT_SIGNAL_GPT4": { "status": "PARTIAL", "last_update": "2026-06-22T10:15:00Z", "owner": "collect_agents", "notes": "Rate limited" },
  "PREDICTION_80DIM": { "status": "REAL GAP", "last_update": null, "owner": "engine/predictor.c", "clough_bill": "PRED-001" }
}
```

### 4. Provider Rotation Gateway
- **Registry**: `data/registry/free_provider_registry.json`
- **Endpoints**: NVIDIA, OpenRouter, Together AI, Google AI Studio, local llama.cpp
- **Rotation**: Distributed low-volume usage; HEAD probe health checks
- **Benchmark**: `benchmark_providers.c` → `data/tests/scorecard.json`

---

## GitHub Commit History (2026-05-24 → 2026-06-22)

| Date | Commits | Pattern |
|------|---------|---------|
| 2026-06-22 | 20+ | `data: update live stats/prices/agents` (automated) |
| 2026-06-22 | 1 | `auth: key updates` |

**Note**: All 21 commits on 2026-06-22 are automated data updates — the engine runs autonomously via cron.

---

## Integration with Seymour Project

The Seymour Project **directly adopted** money-room patterns:

| Seymour Component | money-room Source | Adaptation |
|-------------------|-------------------|------------|
| **C11 Absorber** (`absorption_c11`) | `engine/collector.c` pattern | Raw sockets + CDP WebSocket instead of libcurl + REST |
| **Cron Pipeline** (`seymour-pipeline-cycle`) | `crontab` + collector binaries | `no_agent=true` + `seymour_unified.py` subcommands |
| **Progress Tracking** (`gpu_progress.json`) | `data/bridge/latest.json` | Atomic write + video ID dedup |
| **Gap Tracking** (`whisper_remaining.txt`) | `data/gaps/grid.json` | Flat file queue for Whisper fallback |
| **Pre-flight Checks** (`verify_absorber_cdp.py`) | `benchmark_providers.c` | Chrome CDP + absorber binary health |
| **Provider Rotation** | `rotation_cli.c` + registry | **Eliminated** — all cron jobs now `no_agent=true` (zero external LLM calls) |

---

## Key Technical Decisions

### 1. C11 for Collectors (Not Python)
- **Why**: Sub-millisecond latency, no GIL, static binary deployment, WSL2 friendly
- **Features Used**: `_Static_assert` (struct sizes), `_Alignas(64)` (cache line), `atomic_bool` (stop flags), `_Thread_local` (error buffers)

### 2. Raw Sockets over libcurl (Adopted by Seymour)
- **Why**: libcurl unavailable in some WSL2 envs; `engine/probe_http.c` provides HTTP/1.1 client
- **Seymour**: `absorption/engine/http_raw.c` + `cdp_client.c` — full CDP over raw sockets

### 3. JSON Bridge over Direct DB Access
- **Why**: Decouples collectors from consumers; enables static hosting
- **Seymour**: `pre_seymour/index.json` served directly; no DB needed

### 4. Gap Grid with "Clough Bills"
- **Why**: Task naming + ownership + cadence for recurring gaps
- **Seymour**: `retry_cdp_videos.txt`, `whisper_remaining.txt` — flat but effective

### 5. `no_agent=true` Cron Jobs (Critical Fix)
- **money-room**: Used external LLM calls in cron → **rate limited**
- **Seymour**: **All cron jobs `no_agent=true`** — zero external LLM calls, script-only execution
- **Result**: Seymour cron jobs run reliably; money-room cron jobs failed 100% with HTTP 429

---

## Current Status

| Component | Status |
|-----------|--------|
| Collector binaries | ✅ Running (cron) |
| SQLite data layer | ✅ Live (prices, agents, signals) |
| JSON bridge | ✅ Auto-generated every 5 min |
| Gap grid | ✅ Tracked (PORTED/PARTIAL/REAL GAP) |
| Provider rotation | ⚠️ **Rate limited** (external LLM calls in cron) |
| Benchmark/probe | ✅ `scorecard.json` updated hourly |
| C data server | ❌ Not deployed (planned) |

---

## Lessons Learned (Applied to Seymour)

1. **Never put external LLM APIs in cron jobs** — Use `no_agent=true` + local models only
2. **Raw sockets > libcurl** for WSL2 reliability — Seymour C11 absorber uses this
3. **Atomic JSON writes** — `.tmp` + rename pattern prevents corrupted progress files
4. **Gap tracking as flat files** — Simpler than DB, survives SIGKILL mid-batch
5. **Chrome memory leak requires restart** — money-room collectors don't have this; Seymour orchestrator restarts Chrome every 50–100 videos
6. **Benchmark before trust** — `benchmark_providers.c` → `scorecard.json`; Seymour has `verify_absorber_cdp.py`

---

## See Also
- [WaefreBeorn](01_WaefreBeorn.md) — Creator/organization
- [Seymour Project](02_Seymour_Project.md) — Primary pattern consumer
- [absorb-monkey-engine-room skill](https://github.com/waefrebeorn/WuBuSkills) — Formalized pattern
- [bytropix](04_bytropix.md) — Shares C11 engine patterns
- [slermes](05_slermes.md) — Shares JSON API + supervision patterns
- [Cross-Referenced Timeline](07_Timeline_Crossref.md) — YouTube ↔ GitHub ↔ Research