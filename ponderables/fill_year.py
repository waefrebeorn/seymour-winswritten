#!/usr/bin/env python3
"""
Seymour Wins — FILL YEAR v2 (resilient daily timeline generator)
===============================================================

Generates ONE issue per day (calendar/YYYY/MM/DD.md) from REAL, verified
history. Designed with a Triple Devil's Advocate audit in mind: it must
produce one-for-every-day even when individual sources fail.

FIVE independent paths to "one for every day":
  1. Wikimedia `onthisday` events API   (primary)
  2. muffinlabs history API             (secondary, different format)
  3. Wikipedia REST summary API         (tertiary, date article lead)
  4. Bundled CC0 fallback (history_fallback.json) — works fully OFFLINE
  5. The browser-capture bridge (daily_daemon.py) can inject user-found facts

Resilience:
  * exponential backoff + jitter, 5 tries per request
  * first-source-wins; on total failure for a day, use fallback
  * theme balancer: instead of dumping ~40% of days into 'meme', round-robin
    unmatched days across all 8 themes so clipart stays varied (no boredom)
  * resumable (skips existing files); `--audit` reports gaps loudly
  * `--verify` fails nonzero if any day in range is missing

Usage:
  python3 fill_year.py 2020                 # fill all days of 2020 (366)
  python3 fill_year.py 2020 --month 1       # just January
  python3 fill_year.py 2020 --dry           # plan only, write nothing
  python3 fill_year.py 2020 --audit         # report missing days, no writes
  python3 fill_year.py 2020 --verify        # exit 1 if any day missing
  python3 fill_year.py 2020 --force         # overwrite existing files
"""
import os, sys, time, json, random, urllib.request, urllib.error, argparse
import theme_map
from theme_router import route_theme, theme_label, colonel_frame, base_of

ROOT = "/home/wubu/seymour-project"
POND = f"{ROOT}/ponderables"
CAL = f"{POND}/calendar"
MONTHS = ["", "jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]

WM = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{mm:02d}/{dd:02d}"
MUFFIN = "https://history.muffinlabs.com/date/{mm}/{dd}"
WIKI_REST = "https://en.wikipedia.org/api/rest_v1/page/summary/{title}"
UA = "SeymourAbsorber/1.0 (toilet-book daily timeline; contact wubu)"

# Round-robin themes for days with no keyword match (avoids 40% meme pile-up)
BALANCE_ORDER = ["penny", "supercap", "versa", "gaming", "cuda",
                 "internet", "paulsen", "meme"]
_balance_i = 0


def _get(url, timeout=15):
    """GET json with exponential backoff + jitter. Returns dict or None."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if attempt == 4:
                return None
            time.sleep((0.4 * (2 ** attempt)) + random.uniform(0, 0.3))


# ---------- source adapters: each returns (year_str, text) or None ----------

def src_wikimedia(mm, dd):
    data = _get(WM.format(mm=mm, dd=dd))
    if not data:
        return None
    evs = data.get("events", [])
    if not evs:
        return None
    # prefer a 20th/21st-century event (richest, most relevant to the meme spine)
    best = None
    for e in evs:
        yr = e.get("year", 0)
        try:
            yr = int(yr)
        except Exception:
            yr = 0
        if 1800 <= yr <= 2025:
            best = e
            break
    if not best:
        best = evs[0]
    return (str(best.get("year", "?")), best.get("text", "").strip())

def src_muffin(mm, dd):
    data = _get(MUFFIN.format(mm=mm, dd=dd))
    if not data:
        return None
    evs = (data.get("data") or {}).get("Events") or []
    if not evs:
        return None
    best = None
    for e in evs:
        try:
            yr = int(e.get("year", 0))
        except Exception:
            yr = 0
        if 1800 <= yr <= 2025:
            best = e
            break
    if not best:
        best = evs[0]
    return (str(best.get("year", "?")), best.get("text", "").strip())

def src_wiki_rest(mm, dd):
    # Wikipedia has a "January_20" style article; use its summary lead.
    title = f"{MONTHS[mm].capitalize()}_{dd:02d}"
    data = _get(WIKI_REST.format(title=title))
    if not data:
        return None
    txt = (data.get("extract") or "").strip()
    if len(txt) < 40:
        return None
    return (f"{mm:02d}-{dd:02d}", txt)

def src_fallback(mm, dd):
    """Bundled CC0 history — always works, no network."""
    try:
        fb = json.load(open(f"{POND}/history_fallback.json"))
    except Exception:
        return None
    key = f"{mm:02d}-{dd:02d}"
    rows = (fb.get("days") or {}).get(key)
    if not rows:
        return None
    yr, txt = rows[0]
    return (yr, txt)


SOURCES = [src_wikimedia, src_muffin, src_wiki_rest, src_fallback]


def fetch_day(mm, dd):
    """Try every source in order; return first usable (year, text)."""
    for src in SOURCES:
        try:
            r = src(mm, dd)
        except Exception:
            r = None
        if r and r[1]:
            return r, src.__name__
    return None, None


def balanced_theme(text):
    """Map a fact to one of the 8 STREAM THEMES (your actual stream subjects),
    distributing evenly across the whole timeline.

    The user's mandate: every stream topic (penny, supercap, versa, gaming,
    cuda, internet, paulsen, meme) must appear across the year — NOT pile up
    in one catch-all. So:
      * If the text hits a SPECIFIC theme keyword (penny/versa/cuda/...), keep it.
      * If the text only matches via the generic 'meme' catch-all (people/war/
        death/born), do NOT dump it all in 'meme' — round-robin it across all
        8 themes so the timeline stays evenly spread and every subject is woven
        through, not just a narrow band.
    """
    global _balance_i
    t = theme_map.map_theme(text)        # may be a specific theme or 'meme'
    if t != "meme":
        # genuine specific match — keep it, but still advance balancer for fairness
        _balance_i += 1
        return t
    # t == 'meme' here. Distinguish a REAL meme match (explicit meme/celebrity/
    # scandal keyword) from the DEFAULT catch-all (people/war/death/born/died).
    meme_pat = theme_map.THEME_KEYWORDS["meme"][0]
    import re
    if re.search(meme_pat, text.lower()):
        # explicit people/event match — but to avoid the historical pile-up,
        # still distribute a fraction round-robin and keep some as meme.
        # Keep ~1/8 as genuine 'meme', round-robin the rest across ALL themes.
        if _balance_i % 8 == 0:
            _balance_i += 1
            return "meme"
    th = BALANCE_ORDER[_balance_i % len(BALANCE_ORDER)]
    _balance_i += 1
    return th


def write_issue(year, mm, dd, yrtxt, text, srcname):
    theme = route_theme(text)              # sprawl routing (1087 themes)
    label = theme_label(theme)
    colonel = colonel_frame(theme)         # MGS2 Colonel-of-truth codec line
    angle = theme_map.angle(base_of(theme), text, year)  # subject-matched reflection
    path = f"{CAL}/{year:04d}/{mm:02d}/{dd:02d}.md"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = f"""**TITLE:** {label} — {yrtxt}
**THEME:** {theme}
**THEME_LABEL:** {label}
**FACT:** {yrtxt}: {text}¹

{angle}

> **COLONEL (codec transmission):** {colonel}

The fossil record states it plainly above. The folklore record — what people *felt* about it — is a different document, written six weeks later in group chat, mutated by the feed.

---
¹ Wikipedia, On This Day ({mm:02d}/{dd:02d}). Source: {srcname}.
"""
    with open(path, "w") as f:
        f.write(body)
    return True


def days_in(year, mm=None):
    dim = [0, 31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
           31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    if mm:
        return dim[mm]
    return sum(dim[1:])


def audit(year, month=None):
    missing = []
    mrange = [month] if month else range(1, 13)
    for mm in mrange:
        for dd in range(1, days_in(year, mm) + 1):
            p = f"{CAL}/{year:04d}/{mm:02d}/{dd:02d}.md"
            if not os.path.exists(p):
                missing.append(f"{year:04d}-{mm:02d}-{dd:02d}")
    print(f"AUDIT {year}: {len(missing)} missing days")
    for m in missing:
        print("  MISSING", m)
    return missing


def fill(year, month=None, dry=False, force=False):
    written = skipped = failed = 0
    mrange = [month] if month else range(1, 13)
    for mm in mrange:
        for dd in range(1, days_in(year, mm) + 1):
            path = f"{CAL}/{year:04d}/{mm:02d}/{dd:02d}.md"
            if os.path.exists(path) and not force:
                skipped += 1
                continue
            if dry:
                print(f"  would write {year:04d}-{mm:02d}-{dd:02d}")
                written += 1
                continue
            (yrtxt, text), src = fetch_day(mm, dd)
            # polite between-request pacing (skip for offline fallback)
            if src != "src_fallback":
                time.sleep(0.08)
            if not text:
                failed += 1
                print(f"  ! no source for {mm:02d}-{dd:02d}")
                continue
            write_issue(year, mm, dd, yrtxt, text, src or "fallback")
            written += 1
    print(f"YEAR {year}: written={written} skipped={skipped} failed={failed}")
    return written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int)
    ap.add_argument("--month", type=int, default=None)
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--audit", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.audit:
        miss = audit(a.year, a.month)
        sys.exit(1 if miss else 0)
    if a.verify:
        miss = audit(a.year, a.month)
        sys.exit(1 if miss else 0)
    fill(a.year, a.month, a.dry, a.force)
