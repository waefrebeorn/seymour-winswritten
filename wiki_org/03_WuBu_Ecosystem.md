# WuBu Ecosystem

**WuBu** is a interconnected suite of open-source projects spanning distributed LLM inference, operating system development, AI agent routing, mathematical libraries, and creative tools — all developed by **WaefreBeorn** as a unified research and infrastructure platform. The name "WuBu" (五步, "five steps") reflects the project's iterative, layered architecture philosophy.

## Repository Map (GitHub: `waefrebeorn`)

| Repository | Created | Updated | Description | Language |
|------------|---------|---------|-------------|----------|
| **WuBu** | 2025-06-21 | 2026-05-25 | P2P Distributed Inference Network — Qwen 3.6-35B A3B on Steam Deck, Zonos TTS, DAC audio | Python |
| **WuBuMath** | 2026-06-26 | 2026-06-28 | Pure C11 mathematical & media encoding library, "slermed" from bytropix | C11 |
| **WuBuOS** | 2026-06-07 | 2026-07-01 | Hybrid TempleOS/ZealOS C-port with Win98/XP classic shell | C |
| **WuBuRouter** | 2026-06-21 | 2026-06-21 | Unlimited FREE AI coding — connects Claude Code, Codex, Cursor, OpenCode, Goose | Go/TypeScript |
| **WuBuSkills** | 2026-06-22 | 2026-06-22 | AI agent skills published by NVIDIA (metadata sync) | Python |
| **WuBuCut** | 2026-06-18 | 2026-06-18 | Open-source CapCut alternative | TypeScript |
| **WuBuVideo** | 2026-06-18 | 2026-06-18 | Original OpenCut codebase | TypeScript |
| **WuBuFX** | 2025-02-28 | 2025-03-02 | Windows compile of "StreamFX" for OBS 31.0.1 | C++ |
| **WuBuWallPaper** | 2024-10-26 | 2025-05-27 | MP4/GIF wallpaper tool using classic Win32 APIs | C++ |
| **WuBuContainer** | 2026-06-07 | 2026-06-07 | Universal WuBu file format | — |
| **WuBu-DLP** | 2025-08-12 | 2025-08-12 | Python GUI wrapper for yt-dlp | Python |
| **WuBu-DefCon** | 2026-07-05 | 2026-07-05 | Autonomous red teaming platform; multi-agent offensive security | Python |
| **WuBu-known-examples-in-c** | 2026-06-22 | 2026-06-22 | Copy of abandoned repo: https://github.com/rby90/p... | C |

---

## Core Pillars

### 1. WuBu (P2P Distributed Inference) — *Flagship*
**Repo**: `waefrebeorn/WuBu` | **Commits**: 70+ | **Active**: 2025-06 → 2026-05

- **Goal**: Run Qwen 3.6-35B A3B (and similar) on consumer hardware via P2P weight sharding
- **Key Components**:
  - **Zonos TTS** integration (Descript Audio Codec, Gradio UI)
  - **DAC Autoencoder** — fully vendored, chunked decoding for dtype stability
  - **Steam Deck target** — 6140 MiB VRAM (RTX 4050 Laptop), optimization for 8GB VRAM
  - **Repetition penalty / CFG scale** tuning for TTS quality
- **Milestones**:
  - 2025-06-26: Zonos GUI controls + max_new_tokens fix
  - 2025-06-26: DAC vendoring + chunked decoding
  - 2025-06-25: Repetition penalty + Gradio CFG scale fixes
  - 2025-05-25: "Overtake: WuBu → P2P Distributed Inference Network" — pivot from prior direction

### 2. WuBuMath — *Mathematical Foundation*
**Repo**: `waefrebeorn/WuBuMath` | **Created**: 2026-06-26 | **Language**: C11

- **Origin**: "Slermed from bytropix" — extracted, cleaned math/media kernels from bytropix inference engine
- **Commit**: `v1: clean repo — faithful VHF engine + training (no mp4 history)`
- **Purpose**: Standalone C11 library for:
  - Hyperbolic operations (log map, exp map, Möbius addition)
  - Quantization kernels (Q4_K, IQ1_M, Q6_K)
  - Media encoding (VP9, AV1 helpers)
  - SIMD-optimized linear algebra (AVX2/NEON)
- **Relationship**: Feeds `bytropix` and `slermes`; consumed by `WuBuOS` VSL layer

### 3. WuBuOS — *Operating System*
**Repo**: `waefrebeorn/WuBuOS` | **Active**: 2026-06 → 2026-07 | **Language**: C

- **Vision**: Hybrid TempleOS/ZealOS C-port with Windows 98/XP classic shell aesthetic
- **Architecture**: Phase-based development (4 phases, 20+ items)
- **Key Phases** (from commit log):
  - **Phase 1**: Multi-target deployment (bare metal initramfs, WSL2, OCI, macOS)
  - **Phase 2**: Settings daemon, notifications, session manager, clipboard, MIME, trash, screenshots
  - **Phase 3**: Proton/Wine integration, Steam game library UI (Start menu + Proton)
  - **Phase 4**: Package manager + .wubu App Store, OS Design Bible (OS_BIBLE.md)
- **Recent** (2026-07-01): VSL Vulkan/GPU layer integration, test structure fixes, screenshot capture
- **Test Status**: 747+ tests passing (2026-06-22), 412 gaps tracked

### 4. WuBuRouter — *Agent Gateway*
**Repo**: `waefrebeorn/WuBuRouter` | **Created**: 2026-06-18 | **Updated**: 2026-06-20

- **Tagline**: "Unlimited FREE AI coding"
- **Integrations**: Claude Code, Codex, Cursor, OpenCode, Goose, Ponytail (minimal code gen)
- **Features**:
  - Provider management (Anthropic, Gemini, Perplexity, Kiro, CodeBuddy CN, Xiaomi)
  - SSRF guards, proxy lifecycle, headroom dashboard
  - API key management UI, watcher configuration
  - Anthropic-compatible `/v1/messages` validation
- **Commits**: 20+ in 3 days (intense sprint)

### 5. WuBu-DefCon — *Offensive Security*
**Repo**: `waefrebeorn/WuBu-DefCon` | **Created**: 2026-07-05

- **Goal**: Autonomous red teaming platform; multi-agent offensive security
- **Status**: Initial commit only (very new)

### 6. Creative Tools (Video/Wallpaper)
| Repo | Purpose | Status |
|------|---------|--------|
| **WuBuCut** | CapCut alternative | Initial commit |
| **WuBuVideo** | OpenCut codebase | Initial commit |
| **WuBuFX** | StreamFX for OBS 31.0.1 (Windows compile) | 2025-02 → 2025-03 |
| **WuBuWallPaper** | MP4/GIF live wallpaper (Win32) | 2024-10 → 2025-05 |
| **WuBu-DLP** | yt-dlp GUI wrapper | 2025-08 |

---

## Cross-Project Dependency Graph

```
WuBuMath (C11 math/media kernels)
    ├───► bytropix (inference engine)
    ├───► slermes (C11 agent framework)
    └───► WuBuOS (VSL Vulkan layer)
    
WuBu (P2P inference)
    ├───► uses bytropix kernels
    ├───► uses WuBuMath quantization
    └───► targets WuBuOS deployment

WuBuRouter (agent gateway)
    ├───► routes to local bytropix/llama-server
    └───► exposes WuBuSkills (NVIDIA skills)

WuBu-DefCon (red teaming)
    ├───► uses WuBuRouter for agent orchestration
    └───► targets WuBuOS/WuBuRouter for testing
```

---

## Timeline of Major Events

| Date | Event | Repo |
|------|-------|------|
| 2024-10-26 | WuBuWallPaper created | WuBuWallPaper |
| 2025-02-28 | WuBuFX (StreamFX compile) | WuBuFX |
| 2025-06-21 | WuBu created (P2P inference) | WuBu |
| 2025-06-26 | Zonos GUI + DAC fixes sprint | WuBu |
| 2025-07-18 | SanctumOS fork (ZealOS) created | SanctumOS → WuBuOS |
| 2025-08-12 | WuBu-DLP (yt-dlp GUI) | WuBu-DLP |
| 2026-06-07 | WuBuOS + WuBuContainer created | WuBuOS |
| 2026-06-18 | WuBuCut + WuBuVideo + WuBuRouter created | 3 repos same day |
| 2026-06-21 | WuBuRouter feature sprint (20 commits) | WuBuRouter |
| 2026-06-22 | WuBuSkills + seymour-winswritten created | WuBuSkills, Seymour |
| 2026-06-26 | WuBuMath created (extracted from bytropix) | WuBuMath |
| 2026-07-01 | WuBuOS VSL Vulkan integration | WuBuOS |
| 2026-07-05 | WuBu-DefCon created | WuBu-DefCon |

---

## WuBu in YouTube Transcripts (Seymour Corpus)

The Seymour pre-seymour index (408 videos) contains **181 WuBu-tagged videos** across eras:

| Era | WuBu Videos | Key Series |
|-----|-------------|------------|
| 2023-foundations | ~15 | Early architecture discussions |
| 2024-deep-dives | ~25 | Death Stranding, Poppy Playtime, Subnautica streams |
| 2025-hiatus-prep | ~120 | Marvel Rivals S5–S25, Death Stranding 2, Poppy Ch3–5, FNAF, RDR2 |
| 2026-absorption | ~8 | C11 pipeline, whisper absorption, Seymour build |

**Notable transcript claims** (from quotes.md + timeline):
- "P2P Distributed Inference Network — Qwen 3.6-35B A3B on Steam Deck" (2025-05-25 pivot)
- "Specialized CUDA Triton kernels for common hyperbolic operation → single fused kernel for log map" (2025-08-14, `lrnK5Nm-YIk`)
- "WuBu Nesting / hyperbolic spaces" — recurring research theme
- "bytropix inference engine — Gemma 4 12B dual-head-dim ISW" (2026-06)

---

## Relationship to Seymour Project

| Seymour Component | WuBu Dependency |
|-------------------|-----------------|
| **Topic tagging (Gemma-4-12B)** | Runs on `bytropix` inference engine (WuBuMath kernels) |
| **Whisper fallback** | `WuBu-DLP` → yt-dlp wrapper pattern |
| **Clipart vision (llama-mtmd-cli)** | `WuBuMath` media encoding helpers |
| **Lean 4 formalization** | `WuBuMath` → `bytropix/MATH/lean/wubu_proofs/` |
| **C11 absorber (`absorption_c11`)** | Shares `http_raw.c`, `cdp_client.c` patterns with `slermes` |

---

## Technical Stack Summary

| Layer | Technologies |
|-------|--------------|
| **Core Language** | C11 (WuBuMath, slermes, bytropix, WuBuOS), Python (WuBu, WuBuRouter, tools) |
| **GPU** | CUDA (Triton kernels), Vulkan (VSL), OpenCL fallback |
| **Inference** | llama.cpp/llama-server, bytropix custom kernels, faster-whisper |
| **Audio** | Zonos TTS, Descript Audio Codec (DAC), 16k mp3 for Whisper |
| **Video** | FFmpeg, VP9/AV1, MP4/GIF wallpaper (Win32/GDI) |
| **OS** | Linux (WSL2 primary), bare metal, OCI, macOS targets |
| **Networking** | P2P (libp2p consideration), raw sockets (C11 absorber), WebSocket (CDP) |
| **Formal Verification** | Lean 4, mathlib4, Aesop, Batteries |

---

## See Also
- [WaefreBeorn (Person/Org)](01_WaefreBeorn.md)
- [Seymour Project / Seymour Ponderables](02_Seymour_Project.md)
- [bytropix Inference Engine](04_bytropix.md)
- [slermes (C11 Hermes Fork)](05_slermes.md)
- [money-room](06_money_room.md)
- [Cross-Referenced Timeline](07_Timeline_Crossref.md)