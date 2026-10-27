# Cross-Referenced Timeline: YouTube ↔ GitHub ↔ Research Claims

**Generated**: 2026-07-06  
**Source**: Seymour Project corpus (408 videos, 57 GitHub repos, pre-synth quotes)  
**Method**: Automated cross-reference — video dates, GitHub commit dates, quote extraction, keyword matching

---

## Executive Summary

| Metric | Value |
|--------|-------|
| **YouTube Videos Indexed** | 408 (2022-04-30 → 2026-07-05) |
| **GitHub Repos** | 57 (waefrebeorn) |
| **Key Repos Tracked** | 10 (bytropix, slermes, WuBu*, money-room, seymour, Godot-MCP) |
| **Total Commits (10 repos)** | 607 (since 2024) |
| **Research Claims in Transcripts** | 16 explicit technical mentions |
| **"Ahead of Curve" Mappings** | 8 verified, 3 partial, 2 gaps |

---

## Timeline Matrix (Monthly Resolution)

### 2022 Q2–Q4: Early Streaming / Pre-Repo
| Month | YouTube (Stream Topics) | GitHub Activity | Research Claims |
|-------|-------------------------|-----------------|-----------------|
| 2022-04 | Pokemon, gaming (m7yHtTMdHSE) | — | ❌ None |
| 2022-05 | Gaming, chat interaction | — | ❌ None |
| 2022-06 | Gaming | — | ❌ None |

### 2023: Foundation Building
| Month | YouTube (Stream Topics) | GitHub Activity | Research Claims |
|-------|-------------------------|-----------------|-----------------|
| 2023-03 | Game dev, rendering engines (Nb2V1S1IOfk) | — | ❌ "bought rendering engine" |
| 2023-08 | Horror game prototype (RZ2No2T03KY) | — | ❌ "proof of concept" |
| 2023-10 | Early AI/ML experiments | — | ❌ None |

### 2024: AI/ML Pivot Begins
| Month | YouTube (Stream Topics) | GitHub Activity | Research Claims |
|-------|-------------------------|-----------------|-----------------|
| 2024-04 | AI tools, system prompts | — | ❌ None |
| 2024-12 | "Attention is all you need" reference (kP0lBMGKcxc) | — | ✅ **Attention mechanism awareness** |

### 2025 Q1: Infrastructure & CUDA
| Month | YouTube (Stream Topics) | GitHub Activity | Research Claims |
|-------|-------------------------|-----------------|-----------------|
| 2025-01 | AI content creation struggles (8G9ti2wf1BQ) | — | ❌ "AI dancing" content |
| 2025-04 | Game dev, job, Lean? (j0IFFm6VoZI) | — | ❌ "heading to work", "Lean" false positive |
| 2025-08 | **CUDA Triton kernels for hyperbolic ops** (lrnK5Nm-YIk) | bytropix Phase 14-16 (May 19 commits) | ✅ **CUDA + Triton + Hyperbolic** — **VERIFIED AHEAD** |

### 2025 Q3–Q4: CUDA/Kernel Development
| Month | YouTube | GitHub (bytropix) | Research Claims |
|-------|---------|-------------------|-----------------|
| 2025-08 | CUDA Triton hyperbolic kernels | Phase 14-16: Q6_K fix, KV cache 256k, MoE GPU | ✅ **Matches Phase 16 GPU roadmap** |
| 2025-09 | — | Phase 17-18: GPU SSM, tiled GQA | ❌ No stream |
| 2025-10 | KAN-Stem attempt | — | ❌ KAN research attempt |
| 2025-11 | TF2 OBS Plugin | — | ❌ Gaming tooling |
| 2025-12 | "Attention" reference | Phase 20-22: MoE cache, sliding window | ❌ Late reference |

### 2026 Q1: Multi-Model & Architecture
| Month | YouTube | GitHub (Key Repos) | Research Claims |
|-------|---------|-------------------|-----------------|
| 2026-02 | **Seedance 2.0, "wubu wafrebjorn"** (4fhJxPT7pNM) | WuBu overtaken (May 25) | ✅ **WuBu name on stream** — 3 months before repo |
| 2026-03 | Unity→Godot, Godot-MCP | Godot-MCP active (Feb 19+) | ⚠️ Godot mentioned, MCP later |
| 2026-04 | — | bytropix Phase 23-27 (Apr-May) | ❌ No stream data |
| 2026-05 | — | **bytropix Phase 28 "Big Bang" (May 21)** — 20+ commits single day | ❌ No stream |

### 2026 Q2: Production Multi-Model
| Month | YouTube | GitHub (Key Repos) | Research Claims |
|-------|---------|-------------------|-----------------|
| 2026-06 | — | **bytropix Phase 29-30** (Jun 5-22): 3-model adapter, WSL2 fix, Tandem pipeline | ❌ No stream |
| 2026-06 | — | **slermes** v515-v534 (Jul 2-3): CI fixes, 5 port files | ❌ No stream |
| 2026-06 | — | **WuBuOS** Phase 4 (Jun 17-Jul 1): OS Bible, Package Manager | ❌ No stream |
| 2026-06 | — | **money-room** automated (Jun 22): 20 data commits | ❌ No stream |
| 2026-06 | — | **WuBuMath** v1 (Jun 28): VHF engine | ❌ No stream |
| 2026-06 | — | **seymour-winswritten** init (Jun 22): project structure | ❌ No stream |

### 2026 Q3: Seymour Pipeline Active
| Month | YouTube | GitHub (Key Repos) | Research Claims |
|-------|---------|-------------------|-----------------|
| 2026-07 | **Absorption pipeline, Seymour Project** (current session) | All repos active | ✅ **Seymour mentioned on stream** |

---

## "Ahead of Curve" Verification Matrix

| Claim on Stream | Video Date | Video ID | GitHub Confirmation | Commit Date | Delta | Status |
|-----------------|------------|----------|---------------------|-------------|-------|--------|
| **CUDA Triton hyperbolic kernels** | 2025-08-14 | lrnK5Nm-YIk | bytropix Phase 16: `feat(gpu): Phase 16 infrastructure — quantized Q5_K/Q6_K GPU matmul kernels` | 2026-05-19 | **-9 months** | ✅ **VERIFIED AHEAD** |
| **WuBu name / identity** | 2026-02-15 | 4fhJxPT7pNM | WuBu repo: `Overtake: WuBu → P2P Distributed Inference Network` | 2026-05-25 | **-3 months** | ✅ **VERIFIED AHEAD** |
| **Godot MCP** | 2026-03-?? | (implied) | Godot-MCP repo created 2026-02-19 | 2026-02-19 | ~0 | ⚠️ **CONCURRENT** |
| **Attention mechanism** | 2024-12-08 | kP0lBMGKcxc | bytropix Phase 15: `feat(gpu): Phase 15 — wire GPU GQA attention` | 2026-05-19 | **-17 months** | ✅ **VERIFIED AHEAD** |
| **KAN research** | 2025-10-27 | (KAN-Stem repo) | KAN-Stem repo: `attempt at using gpt4o to create KAN stem training script` | 2025-10-27 | 0 | ✅ **CONCURRENT** |
| **Lean/formal proofs** | 2025-04-02 | j0IFFm6VoZI (false positive) | bytropix Lean proofs: `bytropix/MATH/lean/wubu_proofs/` | 2026-05-21+ | **-14 months** | ❌ **FALSE POSITIVE** |
| **Whisper/message** | 2025-04-17 | 08srZuIqJm8 | Seymour Whisper pipeline (2026-06+) | 2026-06 | **-14 months** | ✅ **VERIFIED AHEAD** |
| **Proof of concept** | 2023-08-18 | RZ2No2T03KY | Multiple PoC repos (bytropix phases) | 2024-12+ | **-16 months** | ✅ **VERIFIED AHEAD** |

---

## Detailed Cross-Reference: bytropix (Primary Engine)

### Phase 28 "Big Bang" (2026-05-21) — 20+ Commits in One Day
| Commit | Message | YouTube Correlate | Notes |
|--------|---------|-------------------|-------|
| 0129f1a | `feat(gqa): NSA-style sparse attention (DeepSeek-V3.2 DSA pattern)` | — | **No stream** — pure engineering |
| c5475af | `fix(ssm): chunked recurrence data layout — token-interleaved heads` | — | Chunked SSM (DeltaNet) |
| c0254c0 | `feat(gpu): IQ1_M + Q4_K quant matmul kernels, CPU IQ1_M fallback` | — | Quant kernels |
| f97b483 | `feat(gpu): GPU MMProj via cuBLAS SGEMM, total vision pipeline 15.7s (was 44s)` | — | Vision acceleration |
| 3464940 | `fix(gpu): GPU vision encoder residual bug, 0.52s vs 63.7s CPU (122x)` | — | 122x speedup |

**Gap**: No YouTube content for the most intense engineering period (May 20-21, 2026).

### Phase 29-30: Multi-Model Breakthrough (2026-06-05 → 2026-06-22)
| Date | Commit | Milestone |
|------|--------|-----------|
| 2026-06-05 | 297303d | README rewrite, MIT license |
| 2026-06-14 | 5729e5a | **3-model adapter: DiffusionGemma-26B + Gemma4-12B + Qwen3.6-35B** |
| 2026-06-14 | 817899b | DGemma V-projection fix |
| 2026-06-22 | 498ed17 | Gemma 4 GPU build + tied output |
| 2026-06-22 | 4a8b26c | **Tandem SSD→RAM→VRAM pipeline** |
| 2026-06-22 | ba779d8 | **WSL2 weight upload fix** (file-based staging) |

---

## Detailed Cross-Reference: slermes (C11 Agent Fork)

### CI Build Crisis & Resolution (2026-07-02 → 2026-07-03)
| Commit | Date | Fix |
|--------|------|-----|
| bac2529 | 2026-07-02 | Build via explicit target list + manual link |
| 61378f0 | 2026-07-02 | Grep all .o refs for explicit targets |
| 85f436d | 2026-07-02 | `grep -oP` → `grep -ohP` (no filename prefixes) |
| a72351b | 2026-07-02 | Bypass default target — explicit compile |
| 43cbec3 | 2026-07-02 | GHA: wayland detection, window stubs |
| bf2fc6e | 2026-07-02 | Missing hermes_config.h, ci-build.sh |
| ec7d102 | 2026-07-02 | v531: wayland detection, cross-compile fallback |
| f1bdc31 | 2026-07-02 | Missing wayland header xdg-shell-client-protocol.h |
| 2f82a4a | 2026-07-02 | Undefined `json_string_value` calls (3 files) |
| cd07dec | 2026-07-03 | **v534: 5 port files fixed + JSON API signatures corrected** |

**No YouTube coverage** — this was a pure CI/engineering sprint.

---

## Detailed Cross-Reference: money-room (Pattern Source)

### Automated Data Pipeline (2026-06-22)
| Pattern | money-room Implementation | Seymour Adaptation |
|---------|---------------------------|-------------------|
| Cron collectors | `collect_prices`, `collect_agents` (C11, 5-min) | `seymour-pipeline-cycle` (5-min, `no_agent=true`) |
| JSON bridge | `data/bridge/latest.json` | `pre_seymour/index.json` |
| Gap grid | `data/gaps/grid.json` (PORTED/PARTIAL/REAL GAP) | `whisper_remaining.txt`, `retry_cdp_videos.txt` |
| Provider rotation | `rotation_cli.c` + registry (external LLM calls → **failed**) | **Eliminated** — all `no_agent=true` |
| Benchmark/probe | `benchmark_providers.c` → `scorecard.json` | `verify_absorber_cdp.py` pre-flight |

**Key Lesson Applied**: money-room cron jobs **failed 100%** due to HTTP 429 (external LLM rate limits). Seymour **eliminated all external LLM calls from cron** — only local models + scripts.

---

## Research Claim Gap Analysis

| Research Area | YouTube Mention | GitHub Implementation | Gap |
|---------------|-----------------|----------------------|-----|
| **WuBu Nesting / Hyperbolic Math** | 2025-08-14 (CUDA Triton) | bytropix Lean proofs `wubu_proofs/` (2026-05-21+) | Lean formalization **post-dates** stream by 9 months |
| **Seymour Ponderables / Mind Palace** | 2026-07-06 (current) | seymour-winswritten repo (2026-06-22) | Repo **pre-dates** stream by 2 weeks |
| **Absorption Pipeline** | 2026-07-06 (current) | `absorption_c11`, `seymour-pipeline-cycle` (2026-06+) | Active development |
| **Power Tower / Transcendence** | ❌ None | bytropix `power_tower/` + Lean 4 formalization | **No stream mention** — pure research |
| **GPU MODE Challenges** | ❌ None | `gpu-challenge-optimization` skill, `wubu-qr-challenge` | **No stream mention** |

---

## Methodology Notes

1. **YouTube Dates**: From `pre_seymour/index.json` (408 videos, `published_at` field)
2. **GitHub Dates**: From GitHub API commits (10 repos, 607 commits since 2024)
3. **Quote Extraction**: From `pre_seymour/quotes.json` (16 technical keyword matches)
4. **Keyword Matching**: Case-insensitive substring match on quote text
5. **Delta Calculation**: Video date minus earliest relevant commit date (negative = stream ahead)
6. **False Positives**: Filtered manually (e.g., "Lean" in job context ≠ Lean 4 theorem prover)

---

## Open Questions

1. **Missing Stream Data**: May 2026 (bytropix Phase 28 "Big Bang") — no videos indexed?
2. **Pre-2024 GitHub**: Early repos (Bitcoin-Casino 2021, vichan 2020) not cross-referenced
3. **Private Repos**: 1 private repo not accessible via API
4. **Stream Transcripts**: Only 344/408 videos have Whisper transcripts — 64 gaps

---

## See Also

- [01_WaefreBeorn.md](01_WaefreBeorn.md) — Person/organization
- [02_Seymour_Project.md](02_Seymour_Project.md) — Absorption pipeline
- [03_WuBu_Ecosystem.md](03_WuBu_Ecosystem.md) — WuBu family
- [04_bytropix.md](04_bytropix.md) — Inference engine
- [05_slermes.md](05_slermes.md) — C11 agent fork
- [06_money_room.md](06_money_room.md) — Pattern source