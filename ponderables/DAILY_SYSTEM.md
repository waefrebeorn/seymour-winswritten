# Seymour Wins — Daily System (TDA-hardened)

## The mandate
ONE issue per day. No gaps. Every `calendar/YYYY/MM/DD.md` is a real, verified
historical anchor — never fabricated. The "through the years" spine (same date,
every year, side by side) is the whole thesis, so coverage must be total.

## Triple Devil's Advocate — what was broken
1. **Coverage gap (PASS 1 — TRUE & severe):** 2020 needs 366 issues; only **4**
   existed (1.1%). `fill_year.py` v1 was authored but never run to completion.
2. **Single source (PASS 2):** v1 used Wikimedia only. One 500/rate-limit blocked
   the entire year. No fallback, no backoff-with-jitter.
3. **Theme pile-up (PASS 2):** `map_theme` defaulted ~40% of days to `meme`
   (history is mostly people), re-introducing the boredom we just fixed in the
   constants volume.
4. **No validator (PASS 2):** nothing failed loudly when a day was missing.
5. **No browser capture (PASS 3):** the user explicitly wanted a way to file
   facts found on the web. v1 had zero capture path.

## The fix — FIVE independent paths to "one for every day"
| # | Path | Failure mode covered |
|---|------|----------------------|
| 1 | Wikimedia `onthisday` API | primary, richest |
| 2 | muffinlabs history API | different format/source |
| 3 | Wikipedia REST summary | tertiary |
| 4 | Bundled `history_fallback.json` (CC0) | **fully offline** |
| 5 | Browser capture extension → `daily_daemon.py` | user-found facts |

Resilience: exponential backoff + jitter (5 tries), first-source-wins, polite
0.25s pacing (skipped for offline fallback), theme **round-robin balancer** so
unmatched days spread across all 8 themes (no meme pile-up), resumable, and a
loud `--audit` / `--verify`.

## Commands
```bash
# Fill a whole year (resumable; skips existing)
python3 fill_year.py 2020

# Just one month
python3 fill_year.py 2020 --month 1

# Report gaps WITHOUT writing
python3 fill_year.py 2020 --audit

# CI gate: exit 1 if any day missing
python3 fill_year.py 2020 --verify

# Overwrite everything
python3 fill_year.py 2020 --force
```

## Build the PDFs
```bash
python3 build_calendar.py 2020 01            # one month
python3 build_calendar.py 2020               # full annual (366 pp)
python3 build_calendar.py 2020 01 20 --through-years   # one date, all years
```

## Browser capture bridge
```bash
# 1. Start the local daemon
python3 daily_daemon.py --port 8770 &

# 2. Load the extension (Firefox/Chrome):
#    browser_plugin/  -> about:debugging -> Load Temporary Add-on (manifest.json)
#
# 3. On any page: select text -> right-click -> "Capture selection → Seymour Wins"
#    OR click the toolbar icon, set date/theme/fact, hit FILE IT.
#    It writes calendar/YYYY/MM/DD.md via the daemon.
```

## Post-fill: the overlap spine is still hand-seeded
`fill_year.py` writes the `FACT` + `THEME` + a generic reflection. The
cross-year `OVERLAP: [[YYYY-MM-DD]]` links (the actual "through the years"
thesis) are seeded on the 4 original hand-written COVID-spine days and should
be extended per-year as more years are filled. `build_through` renders them.
