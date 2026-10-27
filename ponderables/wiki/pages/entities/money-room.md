---
title: "money-room"
created: "2026-07-06"
updated: "2026-07-06"
tags: [entity, project, c11, trading-engine, inference, evolutionary-ai, production]
sources: 1
status: active
---

# money-room

## Overview

money-room (evolution/expansion of mega-era-network lineage) is an 80-dimensional C11 trading and inference engine running 10,000 agents with evolutionary learning, live market data bridging, and paper trading at 5ms/cycle on 722K BTC candles.

## Key Specifications

- **Language**: C11 (production-only, zero Python in production)
- **Files**: 210 C files
- **Agents**: 10,000 per room
- **Dimensions**: 80-dimensional genome/feature space
- **Evolution**: SGD + Darwin evolution, Kelly sizing
- **Markets**: 17 multi-market genomes
- **Live Feed**: 191-field bridging
- **Performance**: 5ms/cycle on 722K BTC candles
- **Tag**: Explicitly documented as "C11 (production-only)"

## Architecture

- **Inference Engine**: 80-dim forward pass in pure C11
- **Evolution Loop**: SGD optimization + Darwinian selection
- **Risk Management**: Kelly criterion position sizing
- **Data Pipeline**: Live feed bridging (191 fields) → feature extraction → inference
- **Backtesting**: 722K BTC candles processed at 5ms/cycle
- **Paper Trading**: Real-time simulation with production engine

## Significance

Proves C11 scales to high-performance AI/ML inference and evolutionary systems:
- Zero hidden costs (no GC, no exceptions, no RAII surprises)
- Predictable latency for trading-critical paths
- AI pair-programming effective due to unforgiving C semantics
- Clean deployment: single static binary, no runtime dependencies

## Cross-References

- → [[../sources/grok-essay-02-c11-front-superiority.md]]
- → [[../entities/slermes.md]]
- → [[../entities/plfm-radar.md]]
- → [[../concepts/c11-front-strategy.md]]
- → [[../concepts/unforgiving-c-ai-collaboration.md]]

## References

- Grok Essay: The C11 Front (source)
- GitHub: waefrebeorn/money-room (mega-era-network lineage)