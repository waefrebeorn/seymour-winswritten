---
title: "Vintage Fork Strategy"
created: "2026-07-06"
updated: "2026-07-06"
tags: [concept, vintage-hardware, c89, c11, dual-track, portability, rustchain]
sources: 1
status: active
---

# Vintage Fork Strategy

## Overview

A dual-track development strategy where the main branch uses modern C11/C17/C23 while a `vintage-oldmachine` fork targets strict C89/C90 for antique hardware (Win98, XP, DOS, retro iron) — enabling single-binary deployment from modern servers to 1990s machines.

## Architecture

### Main Branch (Modern)
- **Standard**: C11 (or C17/C23 selectively)
- **Features**: _Generic, stdatomic.h, _Static_assert, _Alignas, threads.h
- **Targets**: Linux, macOS, Windows (modern), servers
- **Binary**: Single ~47MB static (slermes) or optimized inference engine (money-room)

### Vintage Fork (Antique)
- **Standard**: C89/C90 strict (`-std=c89 -pedantic-errors` or `/Za`)
- **Compat Layer**: `vintage/compat.h` with:
  - Fixed-width typedefs (`int32_t` etc. via manual definitions)
  - Conservative Win32 includes (`_WIN32_WINNT=0x0400`)
  - No C99+ keywords (`restrict`, `inline`, `bool`, etc.)
- **Downgrades**:
  - Atomics → `volatile` + critical sections or single-threaded fallbacks
  - `_Generic` → function pointer tables or macros
  - VLAs → static buffers
  - `stdatomic.h` → custom lightweight sync primitives
- **Targets**: Win98, WinXP, DOS, early Linux, Rustchain vintage nodes
- **Binary**: Tiny static .exe drops

## Implementation Process (Repeatable)

1. **Create compat.h** — All vintage-specific typedefs, macros, fallbacks
2. **Annotate mainline** — Mark C11-only sections with `#ifndef VINTAGE` guards
3. **Build script** — Separate Makefile target: `make vintage` uses `compat.h` + C89 flags
4. **Test matrix** — CI on modern + VM testing on 98/XP/DOSBox
5. **Sync strategy** — Core logic stays identical; only compat layer diverges

## Why It Works

- **Clean C11 code = Easy C89 port**: Explicit memory, no hidden runtime, clear ownership
- **Architecture preserved**: Tool registry, inference loops, gateway patterns translate directly
- **AI assistance maintained**: Prompt with "strict C89 subset, use compat.h" for vintage work
- **Single source of truth**: Core algorithms don't fork, only platform adaptation layer

## Evidence

- slermes: 352 .c files already explicit and clean — vintage port is mechanical
- money-room: 80-dim inference loop is pure math — no C11 deps in hot path
- plfm_radar: Already embedded C — proves bare-metal viability

## Cross-References

- → [[../sources/grok-essay-02-c11-front-superiority.md]]
- → [[../entities/slermes.md]]
- → [[../entities/money-room.md
- → [[../entities/plfm-radar.md]]
- → [[../concepts/c11-front-strategy.md]]

## References

- Grok Essay: The C11 Front (source)