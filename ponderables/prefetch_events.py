#!/usr/bin/env python3
"""
Seymour Wins — EVENT POOL PREFETCH (offline 6-year fill enabler)
================================================================
Calls the Wikimedia onthisday events API ONCE per calendar date (366 calls)
and caches the FULL event list (year, text) for each date to
event_pool.json. Then fill_all_ngplus.py builds 2021-2026 entirely offline,
picking a different event per year so the years don't duplicate.

All facts stay REAL + verified (same Wikimedia source fill_year uses).
"""
import os, sys, json, time, urllib.request, urllib.error, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
POND = os.path.dirname(os.path.abspath(__file__))
WM = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{mm:02d}/{dd:02d}"
UA = "SeymourAbsorber/1.0 (toilet-book daily timeline; contact wubu)"
POOL = os.path.join(POND, "event_pool.json")

def _get(url, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except Exception:
            if attempt == 1:
                return None
            time.sleep(0.5)

def prefetch():
    pool = {}
    for mm in range(1, 13):
        dim = [0,31,28,31,30,31,30,31,31,30,31,30,31][mm]
        for dd in range(1, dim + 1):
            key = f"{mm:02d}-{dd:02d}"
            data = _get(WM.format(mm=mm, dd=dd))
            evs = []
            if data:
                for e in data.get("events", []):
                    try:
                        yr = int(e.get("year", 0))
                    except Exception:
                        yr = 0
                    txt = (e.get("text") or "").strip()
                    if txt:
                        evs.append([str(yr), txt])
            pool[key] = evs
            if (mm*31 + dd) % 20 == 0:
                print(f"  prefetched {key} ({len(evs)} events)", flush=True)
    json.dump(pool, open(POOL, "w"), indent=1)
    total = sum(len(v) for v in pool.values())
    print(f"POOL BUILT: {len(pool)} dates, {total} total events -> {POOL}")

if __name__ == "__main__":
    prefetch()
