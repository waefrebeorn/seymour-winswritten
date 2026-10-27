# slermes (C11 Hermes Agent Fork)

**slermes** is a **pure C11 fork of Hermes Agent** — the AI agent framework that "grows with you" — rebuilt from the ground up in C11 with native JSON API, MCP (Model Context Protocol) integration, and s6-overlay supervision. Created by WaefreBeorn (2026-05-10 → 2026-07-03 active development).

---

## Overview

| Attribute | Detail |
|-----------|--------|
| **Language** | Pure C11 (GNU11, `-std=gnu11 -O3 -march=native`) |
| **Forked From** | Hermes Agent (Python/TypeScript/Electron) |
| **Repository** | `waefrebeorn/slermes` |
| **Created** | 2026-05-10 |
| **Last Push** | 2026-07-03 (v534) |
| **License** | MIT (inherited from Hermes) |
| **Architecture** | Zero Electron, zero Python runtime, native tool calling |

---

## Design Philosophy

> **"The agent that grows with you"** — but in C11, so it *actually* grows with you (no Electron bloat, no Python version hell, binary deployment).

### Core Principles
1. **No Electron** — Native UI via Ink (React for CLI) or pure TUI
2. **No Python Runtime** — All tools, skills, providers compiled in
3. **JSON API First** — `hermes_json_*` types for all IPC, tool results, LLM responses
4. **MCP Native** — Model Context Protocol client/server built into core
5. **s6 Supervision** — Process tree managed by s6-overlay (crash recovery, logs, readiness)
6. **Provider Rotation** — Free-tier gateway with automatic failover (NVIDIA, OpenRouter, local)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     slermes Core (C11)                       │
├─────────────────────────────────────────────────────────────┤
│  hermes_config.h    │  hermes_json.h      │  hermes_tool.h   │
│  hermes_provider.h  │  hermes_skill.h     │  hermes_agent.h  │
├─────────────────────────────────────────────────────────────┤
│  Providers: NVIDIA, OpenRouter, Ollama, llama.cpp, custom  │
│  Tools:     Native C (file, terminal, web, git, code_exec)  │
│  Skills:    Compiled .so plugins + JSON manifests           │
│  MCP:       stdio/HTTP client + server (JSON-RPC 2.0)       │
├─────────────────────────────────────────────────────────────┤
│  Supervision: s6-overlay (s6-svscan, s6-supervise, s6-log)  │
└─────────────────────────────────────────────────────────────┘
```

### Key Directories (from repo)
- `src/` — Core C11 sources
- `include/hermes/` — Public headers (`hermes_json.h`, `hermes_config.h`, etc.)
- `skills/` — Compiled skill plugins (`.so` + `skill.json`)
- `providers/` — Provider implementations
- `mcp/` — MCP client/server
- `tui/` — Ink-based TUI (optional)
- `ci-build.sh` — CI build script (explicit gcc targets, no Makefile dependency)

---

## JSON API Conventions (`slermes-c-json-api`)

All IPC, tool results, and LLM communication use **strict JSON conventions**:

```c
// Core types (hermes_json.h)
typedef enum { HERMES_JSON_NULL, HERMES_JSON_BOOL, HERMES_JSON_NUMBER,
               HERMES_JSON_STRING, HERMES_JSON_ARRAY, HERMES_JSON_OBJECT } hermes_json_type_e;

typedef struct hermes_json_s hermes_json_t;

// Construction
hermes_json_t *hermes_json_object(void);
hermes_json_t *hermes_json_array(void);
hermes_json_t *hermes_json_string(const char *s);
hermes_json_t *hermes_json_number(double n);
hermes_json_t *hermes_json_bool(bool b);
hermes_json_t *hermes_json_null(void);

// Access
hermes_json_t *hermes_json_get(hermes_json_t *obj, const char *key);
const char *hermes_json_get_string(hermes_json_t *obj, const char *key);
double hermes_json_get_number(hermes_json_t *obj, const char *key);
bool hermes_json_get_bool(hermes_json_t *obj, const char *key);
hermes_json_t *hermes_json_get_array(hermes_json_t *obj, const char *key);

// Serialization
char *hermes_json_dumps(hermes_json_t *j, bool pretty);
hermes_json_t *hermes_json_loads(const char *s, size_t len, char **err);
```

**Wire Protocol**: All tool calls, LLM requests, and MCP messages use this exact JSON structure — no ad-hoc formats.

---

## Include Patterns (`slermes-c-include-patterns`)

```c
// Public API — always include via hermes/ prefix
#include <hermes/hermes_json.h>
#include <hermes/hermes_config.h>
#include <hermes/hermes_tool.h>
#include <hermes/hermes_provider.h>
#include <hermes/hermes_agent.h>

// Internal — relative to src/
#include "internal/hermes_memory.h"
#include "internal/hermes_log.h"

// Skills — plugin interface
#include <hermes/hermes_skill.h>
```

**Build Rule**: `-Iinclude` for public, `-Isrc` for internal. No `../` traversals in public headers.

---

## Provider System

| Provider | Implementation | Status |
|----------|----------------|--------|
| **NVIDIA** | `provider_nvidia.c` | ✅ Primary (free tier) |
| **OpenRouter** | `provider_openrouter.c` | ✅ Fallback |
| **Ollama** | `provider_ollama.c` | ✅ Local |
| **llama.cpp** | `provider_llamacpp.c` | ✅ Local server |
| **Custom** | `provider_custom.c` | ✅ Extensible |

**Rotation Logic** (in `hermes_provider.c`):
1. Health check `/models` endpoint (HEAD request, 2s timeout)
2. Score by latency × error rate × quota remaining
3. Round-robin among healthy providers
4. Circuit breaker: 3 consecutive failures → 5 min cooldown

---

## MCP Integration

- **Client**: `mcp_client.c` — stdio + HTTP transports, JSON-RPC 2.0
- **Server**: `mcp_server.c` — exposes slermes tools as MCP resources
- **Tools exposed**: `file_read`, `file_write`, `terminal_exec`, `web_search`, `git`, `code_exec`
- **Skill discovery**: Auto-registers `.so` plugins as MCP tools

---

## s6 Supervision Tree (`hermes-s6-container-supervision`)

```
s6-svscan (PID 1 in container)
├── s6-supervise slermes-core      # Main agent process
├── s6-supervise slermes-mcp       # MCP server
├── s6-supervise slermes-gateway   # Provider rotation gateway
├── s6-supervise slermes-tui       # Optional TUI
└── s6-log (per service)           # Structured logging
```

**Readiness**: Each service writes `/run/slermes/<service>/ready` on startup; gateway waits for all before accepting requests.

---

## CI / Build (v534 — 2026-07-03 Fixes)

**Problem**: GitHub Actions builds kept failing (wayland detection, missing headers, pattern rules)
**Solution**: `ci-build.sh` — explicit compile + link, no Makefile default target

```bash
#!/bin/bash
# ci-build.sh (excerpt)
CC=gcc
CFLAGS="-std=gnu11 -O3 -march=native -ffast-math -funroll-loops -Iinclude"
LDFLAGS="-lm -ldl -lpthread -lssl -lcrypto -lcurl -lwebsockets"

# Compile all .c files explicitly
for f in src/*.c src/providers/*.c src/mcp/*.c src/tools/*.c; do
    $CC $CFLAGS -c "$f" -o "$f -o "build/$(basename $f .c).o"
done

# Link
$CC build/*.o $LDFLAGS -o build/slermes
```

**v534 Fixes** (2026-07-02 → 2026-07-03):
- Fix 5 port files with compile errors + wrong JSON API signatures
- Fix undefined `json_string_value` calls (3 files)
- Add missing generated Wayland header `xdg-shell-client-protocol.h`
- GHA: wayland detection, window stubs, cross-compile fallback
- CI build via explicit target list + manual link (no Makefile default target)
- `grep -oP` → `grep -ohP` (no filename prefixes in output)
- Apt packages: `libncurses-dev` not `libncursesw6-dev` (Ubuntu 24.04)

---

## Skills System

Skills are **compiled plugins** (`.so`) with JSON manifests:

```
skills/
├── waefrebeorn__bytropix/
│   ├── bytropix.so
│   └── skill.json        # { "name": "bytropix", "tools": ["bytropix_infer", "bytropix_quant"], ... }
├── waefrebeorn__seymour/
│   ├── seymour.so
│   └── skill.json
└── hermes-agent/          # Core meta-skills
    ├── hermes_agent.so
    └── skill.json
```

**Loading**: `dlopen()` at startup; symbols resolved via `hermes_skill_init()`, `hermes_skill_tools()`

---

## Relationship to Hermes Agent (Upstream)

| Aspect | Hermes Agent (Upstream) | slermes (Fork) |
|--------|-------------------------|----------------|
| **Language** | Python + TypeScript (Electron) | Pure C11 |
| **UI** | Electron + Ink | Ink TUI (optional) / headless |
| **Tools** | Python subprocesses | Native C functions |
| **Skills** | Python packages + JSON | Compiled `.so` + JSON |
| **MCP** | Python SDK | Native C client/server |
| **Supervision** | None / PM2 | s6-overlay |
| **Providers** | Python classes | C structs + function pointers |
| **Config** | YAML + Python | JSON + C structs |
| **Deployment** | pip + npm + Electron builder | Single static binary (mostly) |

---

## Development Timeline (GitHub Commits)

| Date | Commit | Milestone |
|------|--------|-----------|
| 2026-05-10 | Initial commit | Repo created, core structure |
| 2026-06-02 | v515–v520 | CI debug: apt packages, CC=gcc, fcntl.h, wayland-dev |
| 2026-06-02 | v521–v530 | Makefile pattern rules, single-target compile, explicit link |
| 2026-07-02 | v529–v533 | Wayland header gen, json_string_value fixes, grep -ohP |
| 2026-07-03 | v534 | **5 port files fixed + JSON API signatures corrected** |

**Total**: 534 commits in ~54 days (May 10 → July 3, 2026) — ~10 commits/day sustained

---

## Integration with WaefreBeorn Ecosystem

| Project | Uses slermes | slermes Uses |
|---------|--------------|--------------|
| **bytropix** | Skill for inference | — |
| **Seymour Project** | Topic tagger, wiki sync skills | — |
| **WuBuRouter** | Gateway pattern inspiration | Provider rotation logic |
| **money-room** | — | Cron-driven collector pattern |
| **WuBuOS** | — | s6-overlay supervision pattern |

---

## Current Status (2026-07-06)

| Component | Status |
|-----------|--------|
| Core JSON API | ✅ Complete, tested |
| Provider rotation | ✅ NVIDIA + OpenRouter + Ollama |
| MCP client/server | ✅ stdio + HTTP |
| s6 supervision | ✅ Tree defined, container-ready |
| CI build | ✅ v534 passing (explicit compile/link) |
| TUI (Ink) | 🟡 Optional, compiles |
| Skill plugin loader | ✅ dlopen + manifest |
| Native tools (file/term/web/git) | ✅ Implemented |
| Python skill compat layer | ❌ Not planned (C-only) |

---

## See Also
- [WaefreBeorn](01_WaefreBeorn.md) — Creator/organization
- [bytropix](04_bytropix.md) — Primary skill consumer
- [Seymour Project](02_Seymour_Project.md) — Absorption pipeline consumer
- [money-room](06_money_room.md) — Cron/collector pattern source
- [Cross-Referenced Timeline](07_Timeline_Crossref.md) — YouTube ↔ GitHub ↔ Research