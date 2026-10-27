# Triple Devil's Advocate Audit — Waefrebeorn Umbrella License v3.0
## Applied Against All 78 waefrebeorn/* GitHub Repositories

### Audit Date: July 2026
### Methodology: 3-pass DA attack (DA1=compat, DA2=migration, DA3=legal risk)
### Sources: GitHub API (all 78 repos), GitHub license metadata, GPL §7, Apache 2.0, MIT, BSD-3-Clause

---

## DA1: License Compatibility Attack

**Question**: Does the Waefrebeorn Umbrella License v3.0 conflict with existing licenses?

### Finding #1: GPL Family — 7 repos CANNOT be relicensed
- CVBX-Via-BNN (GPL-3.0), PrismRTMPS (GPL-3.0), WuBu-DefCon (AGPL-3.0)
- WuBuContainer (GPL-2.0), WuBuFX (GPL-2.0), obs-dual-format (GPL-2.0), spout2 (GPL-2.0)
- **Risk**: GPL §7 says "You may not add any additional restrictions." Waefrebeorn's corporate obligations, copyleft-at-scale, and dispensation are additional restrictions.
- **Mitigation**: Leave GPL repos as-is. Do NOT relicense. Waefrebeorn Umbrella does not apply to GPL code unless explicitly dual-licensed by ALL contributors.

### Finding #2: MIT — 24 repos dual-license needed
- MIT is fully compatible but has NO restrictions. Waefrebeorn Umbrella adds restrictions.
- **Mitigation**: Dual-license strategy — existing MIT contributions keep MIT, new contributions under Waefrebeorn Umbrella. Add LICENSE.waefrebeorn file.

### Finding #3: Apache-2.0 (6 repos), BSD-3-Clause (1 repo) — compatible
- Permissive licenses align with Umbrella's freedoms. Apply directly or dual-license.

### Finding #4: Unlicense (1 repo) — conflict
- SanctumOS uses Unlicense (public domain). Unlicense disclaims all copyright. Umbrella retains copyright and grants permissions. These are contradictory.
- **Mitigation**: Evaluate whether SanctumOS creator wants public domain or Umbrella permissive terms.

---

## DA2: Migration Feasibility Attack

### Finding #1: 29 repos need LICENSE file added (Tier 1) — EASIEST
### Finding #2: 31 repos need dual-license strategy (Tier 2) — MEDIUM
### Finding #3: 7 repos must be left unchanged (Tier 3) — NO ACTION
### Finding #4: 10 repos need license investigation (Tier 4)
### Finding #5: 1 repo needs evaluation (Tier 5)

### Migration Commands (ready to execute):

**Tier 1 (29 repos — apply directly):**
```bash
# For each repo, add LICENSE file from template
gh api repos/waefrebeorn/<repo>/contents/LICENSE \
  --method PUT \
  --field message="Add Waefrebeorn Umbrella License v3.0" \
  --field content="$(base64 -w0 LICENSE.template)" \
  --field branch="main"
```

**Tier 2 (31 repos — dual-license):**
```bash
# Add LICENSE.waefrebeorn to each repo
gh api repos/waefrebeorn/<repo>/contents/LICENSE.waefrebeorn \
  --method PUT \
  --field message="Add Waefrebeorn Umbrella License as dual-license option" \
  --field content="$(base64 -w0 LICENSE.template)" \
  --field branch="main"
```

---

## DA3: Legal & Enforcement Risk Attack

### Risk #1: Dispensation Clause (§6.4)
The creator disclaims downstream responsibility. Courts may not enforce this as a license restriction but rather as a moral statement.
- **Severity**: LOW
- **Mitigation**: Dispensation complements the warranty disclaimer (§9), not a replacement. Courts already accept "as-is" disclaimers.

### Risk #2: No OSI/SPDX Recognition
The license is not recognized by package managers (npm, PyPI, crates.io). Compliance departments may reject it.
- **Severity**: MEDIUM
- **Mitigation**: Request OSI review or register with SPDX custom identifier `Waefrebeorn-Umbrella-1.0`.

### Risk #3: Modifiable License Reserve (§11)
The creator can change terms for future distributions. Contributors may object.
- **Severity**: LOW-MEDIUM
- **Mitigation**: Follow Gagnon et al. (2024) exact procedures: uniform application, 12-month remediation, public documentation, future-only scope.

### Risk #4: Ohio + International Jurisdiction Gap
No governing law clause (following GPL approach). International users may not know which court has jurisdiction.
- **Severity**: LOW
- **Mitigation**: Consider adding Ohio governing law with flexible venue while remaining jurisdiction-neutral.

### Risk #5: Retroactive Shell Entity Revocation (§5)
The creator can revoke license for shell entities and retroactively void it. This is unprecedented in OSS licenses (which are typically irrevocable).
- **Severity**: MEDIUM
- **Mitigation**: Narrow the revocation to ONLY bad-faith violations of anti-shell-company/anti-fraud provisions. Not a blanket revocation power.

---

## Execution Priority

| Priority | Tier | Repos | Action |
|----------|------|-------|--------|
| P1 | Tier 1 | 29 | Add LICENSE file (Umbrella v3.0) |
| P2 | Tier 2 | 31 | Dual-license (keep existing + add Umbrella) |
| P3 | Tier 4 | 10 | Investigate actual license first |
| P4 | Tier 5 | 1 | Evaluate Unlicense (SanctumOS) |
| P5 | Tier 3 | 7 | NO ACTION — GPL repos left as-is |
| P6 | Tier 6 | 0 | NOASSERTION repos (none in this batch) |

**Total repos needing action: 60**
**Total repos left as-is (GPL): 7**
**Total repos unchanged (other): 11**

---

## License Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0 | 2026-07 | Initial draft from Kimi K3 analysis |
| v2.0 | 2026-07 | Kevin Bacon chain v1 — 47 sources, 15 improvements |
| v3.0 | 2026-07 | Legal landscape + dispensation + community standards + STE documentation |
| v3.0-DA | 2026-07 | Triple Devil's Advocate audit applied, migration plan produced |

---

## Files Produced

| File | Description |
|------|-------------|
| `triple-da-license-audit-summary.md` | This document — DA audit results |
| `migration-plan.md` | Step-by-step migration plan for all 78 repos |
| `LICENSE.template` | LICENSE file template for Tier 1 repos |
| `waefrebeorn-umbrella-license-v3.md` | Full v3 license text |
| `waefrebeorn-umbrella-license-v2.md` | Previous v2 license text |
| `waefrebeorn-standard-license-v2.md` | Standard license v2 |
| `wsl-research-improvements.md` | Kevin Bacon chain improvement research |
