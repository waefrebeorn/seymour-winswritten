# Seymour Wins — Patreon Distribution (ToS-Compliant)

## What this does
Turns the daily chronicle into Patreon-ready posts:
- **Individual searchable posts** — one post per daily issue, tagged by
  `seymour-wins`, theme, year, date → fully searchable on Patreon.
- **Yearly COLLECTION posts** — one index post per year linking all individual
  posts, so the catalog is easily accessible in one place.

## Pricing ladder (derived from base doc)
Source of truth: `SERIES-BIBLE-v1.md` (base project pricing **$7.99–$12.99/volume**).
Mapped to a Patreon subscription ladder in `patreon_tiers.json`:

| Tier | Price | Unlocks | Gating |
|------|-------|---------|--------|
| The Feed | Free | Daily issue (1 page), individual + collection posts | public |
| Ponderable | $5/mo | + weekly chronicle volume PDFs | tier-gated |
| Archivist | $12/mo | + 30-pages/day MULTIVERSE AU spins | tier-gated |
| First Principles | $13/mo | + full annual multiverse PDFs | tier-gated |

The ladder is anchored to the base doc's price range: $5 sits below the
$7.99 floor (a monthly slice), $12/$13 bracket the $12.99 top.

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
