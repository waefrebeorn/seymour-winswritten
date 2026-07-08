# SEYMOUR WINS — SALES MODEL (back catalog + future subscription, 2026-07-08)

## The split doctrine
- **PAST TIMELINE (2020–2025):** one-time VOLUME BUYS. Fixed product — the
  artwork + factoids already gathered. Buy the history once, own it.
- **FUTURE TIMELINE (2026+):** SUBSCRIPTION. Ongoing daily issues, volumes, AU
  spins, annual archive. Recurring value, per PRICING.md tiers.
- **Cross-promo:** back-catalog buyers get 20% off their first subscription month.

## Value principle: ONE PAGE = ONE PAGE
No Uncle John's-style fluff inflation. Every sold page carries a GENUINE
factoid (history event + stream lens + Colonel) or genuine clipart. We price
honestly per page: **$0.10/page** base, bundle-discounted.

## Back-catalog product ladder (one-time)
| Product | Pages | Price | Math |
|---------|-------|-------|------|
| Single weekly volume | ~217 | $21.70 | 217 × $0.10 |
| One year (52–53 vols, a la carte) | ~11,300 | $21.70/vol | or year-set $520 |
| **3-Year Bundle** (origin trilogy) | ~6,300 | **$315** | 6,300 × $0.05 |
| **Complete Back Catalog** (2020–2025) | ~12,600 | **$520** | 12,600 × $0.041 |

Most buyers only arrive in 2026, so the 3-year and complete bundles are the
front-door products: "the whole origin story, cheap, honest per-page."

## Factoid engine (the content that makes pages worth $0.10)
`factoid_engine.py` fuses THREE sources per day into one dense, genuine factoid:
1. **World history** — `event_pool.json` (365 dates × real, triple-checked events).
2. **Stream voice** — the 8 user themes (penny, supercap, versa, gaming, cuda,
   internet, paulsen, meme) + Colonel-of-truth lens.
3. **Self-reference ("pastors")** — `concept_tagger.py` scanned 1,228 real
   stream references; each factoid can cite a prior tagged moment so the system
   builds on itself.

Output: `factoids/<year>/<MMDD>.json` (2,557 factoids, 2020–2026). Local only.

## Self-referential transcript system (builds on itself)
From 2026, when you name a concept in-stream, `concept_tagger.py` tags it
(date + video + quote). Future factoids/subscription posts cite these as
"pastors" — the transcript pipeline refers back to its own prior work. The
past (your backlog) drives the future (the subscription). This is the loop:
**sell the past as volumes; feed the future as subscription; let each refer
to the other.**

## Files
- `back_catalog_model.json` — the sales ladder (machine-readable)
- `factoid_engine.py` — history+stream+Colonel factoid generator
- `concept_tagger.py` — scans transcripts → `concept_tags.json` (the "pastors")
- `factoids/` — generated (local, not committed)
- `PRICING.md` — the subscription ladder (future timeline)
