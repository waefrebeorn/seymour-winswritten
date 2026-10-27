---
title: "plfm_radar"
created: "2026-07-06"
updated: "2026-07-06"
tags: [entity, project, c, embedded, radar, firmware, vintage-hardware]
sources: 1
status: active
---

# plfm_radar

## Overview

plfm_radar is an embedded radar firmware project in C, demonstrating C's suitability for vintage/old-machine hardware work and real-time embedded systems.

## Key Specifications

- **Language**: C (embedded, real-time constraints)
- **Domain**: Radar signal processing firmware
- **Hardware**: Embedded/microcontroller targets
- **Relevance**: Proves C scales down to bare-metal vintage hardware

## Significance

Part of the evidence base for the C11 front strategy:
- Embedded work requires explicit memory/layout control
- No runtime overhead acceptable
- Direct register manipulation, interrupt handling
- Clean portability to C89 subset for vintage fork

## Cross-References

- → [[../sources/grok-essay-02-c11-front-superiority.md]]
- → [[../entities/slermes.md]]
- → [[../entities/money-room.md]]
- → [[../concepts/vintage-fork-strategy.md]]

## References

- Grok Essay: The C11 Front (source)
- GitHub: waefrebeorn/plfm_radar