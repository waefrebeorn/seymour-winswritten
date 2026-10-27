# WaefreBeorn

**WaefreBeorn** (also known as **WuBu**, **WaefreBeorn**, **WaefreBeorn** on YouTube) is an independent researcher, software engineer, and content creator focused on large language model (LLM) inference optimization, custom C/C++ inference engines, formal verification, and autonomous AI agent systems. Based in the United States, they operate a daily 3-hour commute (1.5 hours each way) in a 2019 Nissan Versa (~40 MPG) while running a multi-year self-directed research program spanning GPU kernel optimization, hyperbolic embedding spaces (WuBu Nesting), Lean 4 formal verification, and the **Seymour Ponderables** — a serialized book series of small-format clipart books documenting internet culture, memes, and technical research.

## Identity & Handles

| Platform | Handle | URL |
|----------|--------|-----|
| **GitHub** | `waefrebeorn` | https://github.com/waefrebeorn (66 public repos) |
| **YouTube (main)** | `@waefrebeorn` | https://www.youtube.com/@waefrebeorn |
| **YouTube (gaming/streaming)** | `@wubustreams` | https://www.youtube.com/@wubustreams |
| **Website** | `waefrebeorn.github.io` | https://waefrebeorn.github.io |
| **Telegram** | Direct DM | `@WaefreBeorn` |

## Biography

### Early Life & Education
- **Foster care childhood**: Devices confiscated by foster parent; read ~100 Gary Paulsen books (notably *Hatchet*) as primary entertainment
- **Mother**: Deceased (diabetes); known for running into streets to pick up pennies — origin of the **penny motif** that recurs across streams, transcripts, and the Seymour project
- **Wife**: Finds pennies; continues the penny motif as a shared callback
- **No formal CS degree**: Self-taught through deep-dive projects, reverse engineering, and open-source contribution

### Career Trajectory
- **2017–2020**: Early GitHub activity — Bitcoin casino/slot machine projects, vichan/lainchan imageboard forks, Kissu-Vi API server
- **2021–2023**: Deep learning experimentation — KAN (Kolmogorov-Arnold Networks), diffusion TTS, invisible watermarking, Godot engine work
- **2023–2024**: **bytropix** inference engine development — multi-model GPU kernels (Gemma 4, DiffusionGemma, Qwen 3.6), NSA-style sparse attention, chunked SSM (DeltaNet)
- **2024–2025**: **WuBu ecosystem** — P2P distributed inference network, WuBuMath (C11 math library), WuBuOS (TempleOS/ZealOS hybrid), WuBuRouter (AI coding agent gateway)
- **2025–2026**: **slermes** — Pure C11 fork of Hermes Agent with JSON API, MCP integration, and native tool calling
- **2026**: **Seymour Project** — Seymour Ponderables book series, absorption pipeline (C11 CDP + Whisper fallback), triple Devil's Advocate audit methodology

## Research Philosophy

> **"Free/now > optimize later"** — Prioritizes working implementations on free tiers over theoretical optimization. Avoids DeepSeek; uses free providers (NVIDIA, OpenRouter free tiers, local llama.cpp).

> **"Action over deliberation"** — Does not ask permission; executes and reports back. Hates "want me to...?" or "shall I...?" framing.

> **"Capture-first"** — Siri TTS → Telegram → Hermes Agent pipeline for idea capture during commute.

> **"Debug: compile→run→verify"** — Iterative verification loop; frustration = stop and fix, don't repeat.

## Key Technical Contributions

### bytropix (2024–2026)
- **Multi-model inference engine** supporting Gemma 4 12B, DiffusionGemma 26B, Qwen 3.6 35B simultaneously
- **GPU kernels**: IQ1_M, Q4_K, Q6_K quantized matmul; NSA-style sparse attention (DeepSeek-V3 DSA pattern)
- **Chunked SSM (DeltaNet)** recursive state with CUDA kernels
- **Tandem SSD→RAM→VRAM pipeline** with file-based staging buffers for WSL2
- **GQA heterogeneous head_dim** support (DiffusionGemma per-layer head_dim)

### WuBu Nesting (2024–present)
- **Hyperbolic embedding spaces**: $H^{n_i}_{c_i,s_i}$ with boundary $B_{i,j}$ and holographic decomposition (soul/echo)
- **Lean 4 formalization**: `bytropix/MATH/lean/wubu_proofs/` — power tower integer proof ($π^{π^{π^π}} ∉ ℤ$)
- **Hamilton encoder** + BSP (Binary Space Partitioning) tree for MLP V cache encoding

### slermes (2026–present)
- **Pure C11 fork of Hermes Agent** — no Electron, no Python runtime dependency
- **JSON API conventions**: `hermes_json_*` types, `slermes-c-include-patterns` for header organization
- **MCP (Model Context Protocol)** native integration
- **s6-overlay supervision tree** for container orchestration

### Seymour Project (2026–present)
- **Absorption pipeline**: Three parallel transcript extraction paths
  - **C11 CDP Engine** (`absorption_c11`): Chrome DevTools Protocol via raw sockets, 104+ transcripts
  - **Browser CDP** (Python asyncio): 262 transcripts from engagement panels
  - **Whisper fallback** (yt-dlp + faster-whisper tiny.en): 344+ transcripts for no-panel/age-gated videos
- **Triple Devil's Advocate audit methodology** — systematic adversarial review (Analytical Core → Structural Integrity → Adversarial Stress Test)
- **Seymour Ponderables**: 10 planned volumes of small-format clipart books (90s aesthetic, MGS2 Colonel spine)
- **Mind Palace + Wiki**: Structured knowledge base with eras, quotes, daily briefings, topic tags

### money-room (2026)
- **BTC market prediction engine**: 80-dim C11 engine, libcurl + jansson + SQLite
- **Cron-driven collectors**, JSON bridge surfaces, gap-grid tracking
- **Provider rotation gateway** for free-tier LLM APIs

## YouTube Content Timeline (408 videos, 3.89M words)

| Era | Years | Videos | Key Series / Themes |
|-----|-------|--------|---------------------|
| **Foundations** | 2009, 2012, 2017, 2020–2021 | 14 | Rickroll, Gangnam Style, early gaming, Steam Deck |
| **Deep Dives** | 2022–2023 | 121 | TF2 MvM, DNSL, Black Mesa, VRchat, #SaveTF2, Mind Scanning |
| **Hiatus Prep** | 2023–2024 | 91 | Death Stranding 1&2, Poppy Playtime Ch1-5, Marvel Rivals S1-4, Subnautica, RoboCop |
| **Absorption** | 2025–2026 | 203 | Marvel Rivals S5-S25, FNAF, Red Dead 2, Alan Wake 2, Lego, TABLE TIME, C11 pipeline build |

**Total**: 408 videos, ~3.89M transcript words, 4 eras

### Notable Series
- **Marvel Rivals** (~40+ videos, 2024–2026): Season 1 through Season 25 playthroughs
- **Death Stranding 1 & 2** (~20+ videos, 2024–2026): Full playthroughs with technical commentary
- **Poppy Playtime** (~15+ videos, 2024–2026): Chapters 1–5 with theory crafting
- **TABLE TIME** (~10+ videos, 2024–2025): Desk toy / mechanical keyboard / Oregon Trail streams
- **TF2 MvM** (~5+ videos, 2022/2025): Mann vs Machine longplays

## GitHub Repository Map (66 repos, key projects)

| Repository | Created | Last Push | Description | Stars |
|------------|---------|-----------|-------------|-------|
| **bytropix** | 2024-12-14 | 2026-06-22 | WuBu Nesting Playground, multi-model GPU inference engine | — |
| **seymour-winswritten** | 2026-06-22 | 2026-06-22 | Seymour Ponderables — clipart books about memes | — |
| **slermes** | 2026-05-10 | 2026-07-03 | Pure C11 fork of Hermes Agent | — |
| **money-room** | 2026-05-24 | 2026-06-22 | Open source BTC market prediction engine | — |
| **WuBu** | 2025-06-21 | 2026-05-25 | P2P Distributed Inference Network (Qwen 3.6-35B on Steam) | — |
| **WuBuMath** | 2026-06-26 | 2026-06-28 | Pure C11 mathematical & media encoding library | — |
| **WuBuOS** | 2026-06-07 | 2026-07-01 | Hybrid TempleOS/ZealOS C-Port with Win98/XP Classic | — |
| **WuBuRouter** | 2026-06-21 | 2026-06-21 | Unlimited FREE AI coding gateway (Claude Code, Codex, Cursor) | — |
| **WuBuSkills** | 2026-06-22 | 2026-06-22 | AI agent skills published by NVIDIA | — |
| **Godot-MCP** | 2025-03-24 | 2026-02-19 | MCP for Godot game engine | — |
| **gradretentionnet** | 2024-10-06 | 2024-11-09 | Persistent gradient retention research | — |
| **KAN-WuBu-Memory** | 2024-09-14 | 2025-10-27 | KAN stem training with emotional modeling | — |

## Hardware & Infrastructure

| Component | Spec |
|-----------|------|
| **GPU** | RTX 4050 Laptop (6140 MiB VRAM, 5073 MiB free) |
| **CPU** | Intel/AMD laptop (WSL2 Ubuntu) |
| **Commute Vehicle** | 2019 Nissan Versa, ~40 MPG, gas ~$3.90/gal = ~10 mi/$ |
| **Daily Commute** | 1.5 hours each way (3 hours total) — primary research/capture time |
| **LLM Inference** | llama-server port 18802 (Gemma-4-12B qat-UD-Q4_K_XL, 6.3GB) |
| **Vision** | llama-mtmd-cli + mmproj (Gemma-4 mmproj, 168MB) |
| **Storage** | SSD + NVMe for model weights, transcripts, clipart |

## Personal Motifs (Recurring in Transcripts)

| Motif | Origin | Appearances |
|-------|--------|-------------|
| **Penny** | Mother ran into streets for pennies (deceased, diabetes); wife finds pennies | 200+ quote bank entries, daily briefings, stream callbacks |
| **Gary Paulsen / Hatchet** | Foster childhood, devices confiscated, read ~100 books | Transcript references, personal lore |
| **40 MPG Versa** | Daily commute economics vs Uber/DoorDash/Gopuff | EV hybrid ideas, cost calculations |
| **Supercapacitor + Generator Hybrid** | EV hesitation (battery cost); architectural idea | Technical discussions, bytropix analogies |
| **MGS2 Colonel Spine** | Metal Gear Solid 2 reference | Seymour Ponderables book design |
| **90s Clipart Aesthetic** | Uncle John's Ponderables, childhood | Seymour book visual style, 490 clipart assets cataloged |

## Publications & Outputs

### Seymour Ponderables (In Progress)
- **Volume 1**: Foundations (2023 era) — Strongbad, Trogdor, DNSL, early streams
- **Volume 2**: Deep Dives (2024 era) — Death Stranding, Poppy Playtime, Marvel Rivals S1-4
- **Volume 3**: Hiatus Prep (2025 era) — Marvel Rivals S5-S25, FNAF, Red Dead 2, Alan Wake 2
- **Volume 4**: Absorption (2026 era) — C11 pipeline, Whisper, Seymour build
- **Ponderable #001**: "The Tower That Would Not Integer" — $π^{π^{π^π}} ∉ ℤ$ proof

### Technical Reports
- **Triple Devil's Advocate Audit** (2026-07-06) — Pipeline validation methodology
- **Power Tower Integer Proof** — Analytical result: fractional part of $\log\log\log\log N = 0.31766... ≠ 0$
- **bytropix Phase 28–29 Documentation** — IQ1_M, Q4_K, NSA attention, chunked SSM

### Open Source Tools
- **absorption_c11** — C11 YouTube CDP transcript extractor (raw sockets, no libcurl)
- **seymour_unified.py** — 9-command CLI for entire Seymour pipeline
- **topic_tagger.py** — Local LLM topic classification (Gemma-4-12B)
- **generate_infographics.py** — Automated visual summaries (matplotlib + wordcloud)

## Community & Collaboration

- **Penpal relationship model**: Shares life details gradually for worldview context; prefers direct communication over permission-asking
- **Hermes Agent integration**: Uses Hermes as primary agent interface; contributes skills, fixes, documentation
- **GPU MODE community**: Participates in competitive GPU kernel optimization challenges (QR decomposition, etc.)
- **Lean 4 / mathlib**: Formal verification contributions (power tower, WuBu Nesting proofs)

## See Also
- [Seymour Project / Seymour Ponderables](02_Seymour_Project.md)
- [WuBu Ecosystem](03_WuBu_Ecosystem.md)
- [bytropix Inference Engine](04_bytropix.md)
- [slermes (C11 Hermes Fork)](05_slermes.md)
- [money-room](06_money_room.md)
- [Cross-Referenced Timeline](07_Timeline_Crossref.md)