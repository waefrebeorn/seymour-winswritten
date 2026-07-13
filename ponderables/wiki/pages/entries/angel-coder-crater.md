---
title: "The Angel Coder and the Crater"
created: "2026-07-12"
updated: "2026-07-12"
tags: [entry, ponderable, audit, code, methodology]
sources: 2
status: active
---

# The Angel Coder and the Crater

When the boss says "fix the broken code, be the angel coder," the temptation is
to patch the red line and ship. But an audit is only as good as its craters.

A *crater* is a referenced thing that doesn't exist where you pointed — a
`/tmp/proof.c` cited in a PR body the maintainer can't open, a `det_crossproc.c`
mentioned but never committed, a build command that fails as written. The devil's
advocate doesn't just fix the bug; they hunt the craters in their *own* report,
because a claim you can't reproduce is a claim you don't have.

The angel coder's real job: make every assertion green and openable. Build the
adapter you documented. Port the `/tmp` cross-check into the repo as check #5.
Re-run the command in the doc and watch it fail — then fix the doc, not just the
code. Triple-pass it: can I reproduce the headline claim? Do the doc's commands
actually compile? Is the tree pushable without dragging in a dirty WIP file?

WuBu's two audit forks landed this way: eshkol's exact AD confirmed (nested
derivative = 160), one real exp-map bug closed with a measured 0.0166 gap;
quantum_rng debunked to a competent classical PRNG, seed-proven reproducible,
entropy honestly measured at ~7.95 bits/byte. Every number backed by a `gcc &&
./x` you can run. No craters. That's the win — not the fixes, the
*reproducibility*.

## Cross-References

- → [[../concepts/devils-advocate-audit.md]]
- → [[../entities/eshkol-audit.md]]
- → [[../entities/quantum-rng-audit.md]]
- → [[../entities/wubu-manifolds.md]]
- → [[../concepts/varentropy-diagnostics.md]]
