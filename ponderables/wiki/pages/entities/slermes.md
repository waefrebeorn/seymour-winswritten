---
title: "slermes"
created: "2026-07-06"
updated: "2026-07-06"
tags: [entity, project, c11, hermes, agent, systems-programming]
sources: 1
status: active
---

# slermes

## Overview

slermes is a pure C11 reimplementation of the Hermes agent — a full-featured AI coding assistant with CLI, TUI, GUI, plugin system, MCP support, cron scheduler, and gateways to 14+ messaging platforms. 352 .c files + 127 headers, single ~47 MB static binary, near-complete parity (89.4%+ modules ported).

## Key Specifications

| Attribute | Value |
|-----------|-------|
| Language | Pure C11 (explicitly labeled) |
| Files | 352 .c + 127 .h |
| Binary | Single ~47 MB static binary |
| Build | Makefile-driven, multi-platform (Linux/macOS/Windows cross-compile) |
| Parity | 89.4%+ modules ported, zero real gaps |
| Features | CLI (95+ commands), TUI (92 RPCs), GUI (Wayland/EGL), plugins, MCP, cron, skills, 14+ platform gateways |

## Architecture Highlights

- **Tool Registry**: _Generic-based type-safe dispatch for 95+ CLI commands
- **Plugin System**: Clean FFI via C ABI (no name mangling) — C++ would break this
- **Concurrency**: stdatomic.h for gateway polling, cron scheduler, multi-platform message loops
- **GUI**: Wayland/EGL via pure C — no C++ framework dependencies
- **Cross-compile**: Windows targets from Linux via MinGW

## Why C11 Works Here

1. **Single binary deployment** — No runtime dependencies, no C++ stdlib version hell
2. **Plugin ABI stability** — C linkage = universal plugin interface
3. **AI pair-programming** — Unforgiving compiler catches hallucinations instantly
4. **Performance** — Predictable memory layout, no hidden overhead
5. **Vintage path** — Clean C89 subset extraction for Win98/XP targets

## Cross-References

- → [[../sources/grok-essay-02-c11-front-superiority.md]]
- → [[../concepts/c11-front-strategy.md]]
- → [[../concepts/unforgiving-c-ai-collaboration.md]]
- → [[../concepts/vintage-fork-strategy.md]]
- → [[../entities/money-room.md]]
- → [[../entities/plfm-radar.md]]

## Source

Grok Essay: The C11 Front — Superiority Over C++ (direct repository inspection)