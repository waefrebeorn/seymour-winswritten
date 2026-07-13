---
title: "Devil's-Advocate Audit"
created: "2026-07-12"
updated: "2026-07-12"
tags: [concept, method, verification, devils-advocate, proof]
sources: 2
status: active
---

# Devil's-Advocate Audit

## Overview

A verification discipline used across the [[../entities/waefrebeorn.md]] code
audits: **every claim is build-and-run verified against current source — never
trusted from prose.** The "devil's advocate" framing means you actively try to
refute each claim (including your own prior conclusions), then re-verify against
the live code. Applied as a **triple** pass (3xDA) for high-stakes findings.

## Core rules

1. **No theorem without a check.** A math/claim needs a compile + run + numeric
   result, not an assertion. Symbolic OR numeric (Lean proof OR measured gap).
2. **Re-verify every claim against CURRENT source.** Docs drift; code is ground
   truth. A claim that was true last week (e.g. "upstream build is broken") may
   be false after an upstream push — amend, don't over-claim.
3. **Reproduce, don't refute by assertion.** When you find a defect, keep the
   buggy code verbatim as evidence and add a test that demonstrates it; offer
   the fix as a separate, clearly-scoped change. Don't silently "fix" upstream.
4. **No local-file references in delivered artifacts.** A PR body or audit doc
   must cite only paths inside the repo — a `/tmp/...` reference is a "crater"
   the reader cannot open (see [[../entities/eshkol-audit.md]] and
   [[../entities/quantum-rng-audit.md]]).

## Pattern

- **Dual-track**: (a) a standalone C port to test *math* without the upstream
  toolchain (no LLVM needed), and (b) a clean-room interpreter to test the
  *contract* (e.g. AD parity). Both run with one `gcc` command.
- **Angel coder**: when the task is "fix broken code," find the red and make it
  green — correct stale docs, wire up missing includes, close "open" items with
  real measurements.

## Why it fits Seymour

The method is itself a [[../concepts/varentropy-diagnostics.md]]-style
contradiction detector: it surfaces the gap between claimed and actual behavior.
And it parallels the Colonel's [[../concepts/curation-s3.md]] — selection for
societal (or in this case, mathematical) sanity.

## Cross-References

- → [[../entities/eshkol-audit.md]]
- → [[../entities/quantum-rng-audit.md]]
- → [[../entities/wubu-manifolds.md]]
- → [[../entities/slermes.md]]
- → [[../concepts/varentropy-diagnostics.md]]
- → [[../concepts/curation-s3.md]]
- → [[../concepts/c11-front-strategy.md]]

## Source

WaefreBeorn audit practice (eshkol_audit, quantum_rng_audit forks); Hermes
github-open-pr-no-gh skill (PR delivery without gh).
