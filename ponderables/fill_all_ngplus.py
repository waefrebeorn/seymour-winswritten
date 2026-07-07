#!/usr/bin/env python3
"""
Seymour Wins — FILL ALL YEARS (New Game Plus, offline after prefetch)
=====================================================================
Generates 2021-2026 daily issues from the cached event_pool.json (no network).
For each calendar date, assigns a DIFFERENT real event to each year so the
six timelines don't repeat. Then applies the sprawl router + Colonel codec +
enrichment, exactly like remix.py.

Prereq: python3 prefetch_events.py  (builds event_pool.json)

Run: python3 fill_all_ngplus.py
     python3 fill_all_ngplus.py 2021 2022   (specific years)
"""
import os, sys, glob, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme_map
from theme_router import route_theme, theme_label, colonel_frame, base_of
from enrich import pick as pick_fact  # reuse interesting-fact router

POND = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.join(POND, "calendar")
POOL = os.path.join(POND, "event_pool.json")

DIM = [0,31,28,31,30,31,30,31,31,30,31,30,31]

def write_issue(path, year, fact, src, yrtxt_override=None):
    mm = os.path.basename(os.path.dirname(path))
    dd = os.path.basename(path).replace(".md", "")
    theme = route_theme(fact)
    label = theme_label(theme)
    colonel = colonel_frame(theme)
    yrtxt = yrtxt_override if yrtxt_override else str(year)
    angle = theme_map.angle(base_of(theme), fact, year)
    sidebar = ""
    fobj = pick_fact(theme)
    if fobj:
        sidebar = f"\n\n> **TRIPLE-CHECKED:** {fobj['text']}\n> _(verified public-domain fact — {fobj['id']})_\n"
    body = f"""**TITLE:** {label} — {yrtxt}
**THEME:** {theme}
**THEME_LABEL:** {label}
**FACT:** {yrtxt}: {fact}¹
{angle}

> **COLONEL (codec transmission):** {colonel}

The fossil record states it plainly above. The folklore record — what people *felt* about it — is a different document, written six weeks later in group chat, mutated by the feed.
{sidebar}
---
¹ Wikipedia, On This Day ({mm}-{dd}). Source: {src}.
"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(body)

def main():
    pool = json.load(open(POOL))
    years = [int(a) for a in sys.argv[1:]] if len(sys.argv) > 1 else list(range(2021, 2027))
    total = 0
    for y in years:
        print(f"=== {y} ===", flush=True)
        # rotate the starting event index per year so columns differ
        rot = (y - 2021)
        for mm in range(1, 13):
            dim = DIM[mm] + (1 if (mm == 2 and y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 0)
            for dd in range(1, dim + 1):
                key = f"{mm:02d}-{dd:02d}"
                evs = pool.get(key) or []
                if not evs:
                    # fall back to any date-key with events (shouldn't happen)
                    evs = next(iter(pool.values()), [])
                if not evs:
                    continue
                idx = (rot + mm + dd) % len(evs)
                yrtxt, fact = evs[idx]
                path = f"{CAL}/{y:04d}/{mm:02d}/{dd:02d}.md"
                # NOTE: yrtxt is the EVENT's real year from the pool (not the
                # timeline slot y). The folder y is just the volume's year.
                write_issue(path, y, fact, "wikimedia_pool", yrtxt_override=yrtxt)
                total += 1
        print(f"  {y}: {dim} days written", flush=True)
    print(f"FILL ALL COMPLETE: {total} issues across {len(years)} years")

if __name__ == "__main__":
    main()
