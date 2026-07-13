# The Ledger of Curiosity

### An editorial on a GitHub history that became a public record of verifiable effort

*WaefreBeorn — 2026-07-12*

---

There is a story people tell about genius: the lone flash, the sudden insight, the one commit that changes everything. It is almost always false, and it is almost always the least interesting part.

The truth is quieter and far more durable. It is in the *shape* of the work — not the single spark, but the curve of a person refusing to stop.

Pull the full public history of `waefrebeorn` from GitHub and you get 72 repositories and roughly twenty thousand commits. On their own, those numbers are noise. What matters is the slope.

For a decade the output held a steady, workmanlike rhythm — a few hundred commits a month, sometimes less, sometimes more, spread across systems experiments, tooling, and the long apprenticeship of learning to think in C. Then, in the back half of 2025, the line bends. By mid-2026 it is not a line anymore. It is a wall: 2,219 commits in May 2026 alone, 2,134 in June, and July already on pace to surpass them both.

That is a 4.6× surge in average monthly output against the 2024 baseline. Not a trick of a busy week. A sustained, compounding acceleration.

But volume is the least interesting thing about it.

What changed in the vertical part of the curve was not *how much* got built — it was *what kind of thing* got built. The work stopped being merely output and became **verifiable output**.

Consider the projects that landed in that surge:

- **`slermes`** — a complete reimplementation of an AI agent in pure C11. No Python, no C++, no interpreter. Three hundred and fifty-two source files, a single forty-seven-megabyte static binary. Built the unforgiving way, where the compiler is the hallucination filter and there is nowhere to hide.
- **`WuBuMath`** — a pure C11 mathematics and media library that became the independent reference point for an entirely separate body of work.
- **Two devil's-advocate audit forks** — `eshkol_audit` and `quantum_rng_audit` — where the brief was not to praise someone's code but to *break it honestly*. To take another person's claims and reproduce them, line by line, build by build, until the claim and the code either agreed or the gap was measured and named.

That last part is the actual win, and it is easy to miss.

In the eshkol audit, the exact automatic differentiation turned out to be real — including nested derivatives, which most systems quietly get wrong. One genuine geometry bug was found: the exponential map drifted off the origin, breaking a geodesic invariant that should hold everywhere. The fix was a single, clean formula change. It shipped upstream as a polite pull request with the evidence attached, not as a takedown.

In the quantum_rng audit, the marketing said "quantum" and "63.999872 bits per sample." The code said classical PRNG. The audit sided with the code, measured the real entropy at roughly 7.95 bits per byte, proved the seeded mode was reproducible across processes, and offered the honest wording back to the author. No drama. Just the gap, closed with math.

This is the throughline: **effort converted into evidence.** Every claim in those audits is something a third party can compile and run. Every pull request references only files inside the repository, so the person on the other end can actually open them. The work is built to be *checked*, not believed.

That is what the acceleration curve is really showing. It is not "a person got faster at typing." It is "a person built a system — agent, language, math library, audit method — where each unit of effort compounds into something the world can verify." The slope is the compound interest of verifiable curiosity.

There is a Colonel in the Seymour story who insists the truth is being revealed, piece by piece, and you are free to distrust the reveal. Fair. So here is a reveal you can check yourself: the repositories are public, the commits are dated, the audits build from a single `gcc` command. The ledger is open.

The nice part — the part worth showing — is not that one person wrote a lot of code. Plenty of people write a lot of code. The nice part is that the code *argues for itself*. It does not ask you to take its word. It hands you the command to run.

That is the win. Not louder. Verifiable.

And the curve says it is still accelerating.

---

*Raw data: 72 repositories, 20,176 commits sampled (GitHub API, 2026-07-12). Acceleration: 229 → 1,046 avg commits/month (2024 H2 → 2026 H1); peak May 2026 = 2,219. Method: [[devils-advocate-audit]]. Evidence: [[eshkol-audit]], [[quantum-rng-audit]], [[slermes]], [[wubu-manifolds]].*
