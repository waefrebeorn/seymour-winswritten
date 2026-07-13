---
title: "quantum-rng-audit"
created: "2026-07-12"
updated: "2026-07-12"
tags: [entity, project, audit, prng, entropy, devils-advocate]
sources: 1
status: active
---

# quantum-rng-audit

## Overview

`waefrebeorn/quantum_rng_audit` is a devil's-advocate audit fork of
`tsotchke/quantum_rng` — a C11 random-number generator marketed with
"quantum"/"63.999872 bits/sample"/"verified non-deterministic" claims. The fork
independently checks those claims against the actual code, build-and-run, using
the [[../concepts/devils-advocate-audit.md]] method.

## What the audit proved

| Claim | Reality |
|-------|---------|
| Quantum / superposition | **Classical** bit-mixing. "Qubits" = array indices; "Hadamard/Pauli gates" = splitmix64/xorshift mixes |
| 63.999872 bits/sample | Hardcoded marketing text — no code computed it, no NIST/Dieharder suite exists |
| Seeded mode | **Pure function of the seed** — byte-identical stream across PID/time (proven by `audit/determinism_test.c`) |
| Unseeded mode | Non-deterministic, drawn from `gettimeofday`/`getpid` (predictable, not a CSPRNG) |
| Entropy estimator | Now returns real Shannon entropy of output (~7.95 bits/byte) via `audit/qrng_measure.c` |
| `secure_rng` layer | Real hardware entropy (RDSEED/RDRAND/`/dev/random) added upstream — classical, not quantum; health tests **not yet run by this audit** |

## Verdict

A competent classical dual-mode PRNG with quantum-themed naming. Suitable as a
fast non-cryptographic RNG (seeded mode = reproducible). **Not** quantum, **not**
63.999872 bits/sample, **not** fit for cryptography. The code is honest after the
fix; the *rhetoric* still lags (see [[../concepts/devils-advocate-audit.md]]).

## Structure

- `audit/determinism_test.c` — proof the seed governs the stream.
- `audit/qrng_measure.c` — real entropy + chi-square measurement.
- `slerm/` (`qrng_demo`) — clean-room reimplementation backing the entropy audit.
- `proposed-upstream/` — `build-fix.patch` (missing `<sys/types.h>`) + `readme-honesty.patch`.
- `AUDIT.md` (§7 amends the verdict after upstream added `secure_rng`), `INTEGRATION.md`.

## Cross-References

- → [[../entities/waefrebeorn.md]]
- → [[../concepts/devils-advocate-audit.md]]
- → [[../concepts/varentropy-diagnostics.md]]
- → [[../entities/slermes.md]]

## Source

tsotchke/quantum_rng audit fork (waefrebeorn/quantum_rng_audit); PR #6 to tsotchke/quantum_rng.
