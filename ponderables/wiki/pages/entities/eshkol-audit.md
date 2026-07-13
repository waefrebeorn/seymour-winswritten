---
title: "eshkol-audit"
created: "2026-07-12"
updated: "2026-07-12"
tags: [entity, project, audit, geometry, ad, c11, devils-advocate]
sources: 1
status: active
---

# eshkol-audit

## Overview

`waefrebeorn/eshkol_audit` is a cross-validation audit fork of
`tsotchke/eshkol` — a Scheme-dialect language with native exact automatic
differentiation and Riemannian-geometry primitives (`lib/core/manifold.esk`).
The fork exists to independently verify eshkol's math claims against
[[../entities/wubu-manifolds.md]] (an independent C implementation of the same
constant-curvature geometry), using the [[../concepts/devils-advocate-audit.md]]
method: every claim is build-and-run verified, not asserted.

## What the audit proved

| Area | Result |
|------|--------|
| Exact AD | Real and correct, including **nested derivatives** (`(derivative (derivative f))` = 160 for x⁵@2) — proven by the clean-room [[../entities/slermes.md]] reimplementation `slermes-eshkol` |
| Exp map (F1) | **One real bug:** released `manifold-exp-map` violated the geodesic invariant `dist(p, exp_p(v)) = |v|` off the origin (drifted 2.83→4.96). Fix: drop the conformal-factor `lam` from the tanh argument. |
| Christoffel / curvature (F3) | Analytic Γ and K=−1/+1/0, scalar R=K·n(n−1) cross-validated vs WuBuMath to gap 0.0166 |
| Parallel transport | eshkol `lam_a/lam_b` rescale matches WuBuMath's reference to gap 0.00000 |

## Structure

- `cross-validation/` — standalone C port + `test_crossval.c` (6 checks, no LLVM needed). Build+run: `gcc -std=c11 -O3 -I. wubu_poincare_geom.c test_crossval.c -o crossval -lm && ./crossval` → 5/6 (F1 buggy form kept verbatim as evidence).
- `slerm/` — clean-room Scheme/AD interpreter (`slermes-eshkol`) proving the AD contract.
- `proposed-upstream/` — copy-pasteable `exp-map-fix.patch` + evidence map.
- `AUDIT.md`, `INTEGRATION.md` — index + WuBuMath integration notes.

## Why it matters

eshkol's AD is genuinely sound; the only real defect was a geometry norm-scaling
bug, now fixed in the fork and offered upstream as PR #275. The audit is the
bridge proving eshkol and WuBuManifolds agree to ~1e-2 — they are the two
halves of a verifiable Riemannian-ML stack (see
[[../concepts/devils-advocate-audit.md]]).

## Cross-References

- → [[../entities/wubu-manifolds.md]]
- → [[../entities/slermes.md]]
- → [[../entities/waefrebeorn.md]]
- → [[../concepts/devils-advocate-audit.md]]
- → [[../concepts/c11-front-strategy.md]]

## Source

tsotchke/eshkol audit fork (waefrebeorn/eshkol_audit); PR #275 to tsotchke/eshkol.
