# Seymour Wins — Patreon Distribution (ToS-Compliant)

## What this does
Turns the daily chronicle into Patreon-ready posts:
- **Individual searchable posts** — one post per daily issue, tagged by
  `seymour-wins`, theme, year, date → fully searchable on Patreon.
- **Yearly COLLECTION posts** — one index post per year linking all individual
  posts, so the catalog is easily accessible in one place.

## Pricing ladder (derived from base doc + user directive)
Spine (user directive 2026-07-08): **$1/week × 52 = $52/year**. Months = volume.
Years = competent archive. Base print doc `SERIES-BIBLE-v1.md` ($7.99–$12.99/vol)
is the *physical book* price, distinct from this subscription ladder. Full
authority in `PRICING.md`; machine-readable in `patreon_tiers.json`.

| Tier | Price | Unlocks | Gating |
|------|-------|---------|--------|
| The Feed | Free | Daily issue (1 page), individual + collection posts | public |
| Weekly Reader | $52/yr ($1/wk) | + weekly chronicle volume PDFs (52–53/yr) | tier-gated |
| Monthly Volume | $120/yr ($10/mo) | + month-as-volume bundle (12/yr) + 30-pg/day AU | tier-gated |
| Annual Archive | $156/yr | + full annual multiverse PDF (11k+ pp) + archive | tier-gated |

Post-product counts (dry-run, all 7 years): 2,557 daily + 7 collection + 367
weekly + 84 monthly = 3,015 payloads.

## ToS compliance (IMPORTANT)
- Uses the **official Patreon API v2** (OAuth2, `POST /api/oauth2/v2/posts`).
  Do NOT use browser-scraping/bot automation to post — that is the gray area
  Patreon's ToS discourages.
- **Paced sender**: min 2s between posts, exponential backoff on 429/5xx.
- **Edge rate limit** (2025-07-04): a burst of bad requests triggers a 30-min
  block. The sender posts ONE at a time and validates payloads first.
- **V1 clients are deprecated** (2026-03-25) — register a V2 client only.

## Usage
```bash
# 1) Build payloads (dry-run, writes to patreon_payloads/, pushes NOTHING)
python3 patreon_upload.py --dry-run
python3 patreon_upload.py --dry-run --year 2020

# 2) Add credentials to .env (gitignored) — from patreon.com/portal V2 client
#    PATREON_ACCESS_TOKEN=...
#    PATREON_CAMPAIGN_ID=...

# 3) Real push (requires token + campaign id)
python3 patreon_upload.py --live
```
The default mode is `--dry-run`. Live push aborts safely if `.env` is missing
or the token/campaign id are absent.

## Tier gating note
Patreon gates posts to tiers via **access rules / benefits** set on the
campaign. The uploader tags each payload's `tier` field from `patreon_tiers.json`;
wire the actual `tiers_details` access-rule IDs from your campaign when going live.
