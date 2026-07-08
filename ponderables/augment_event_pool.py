#!/usr/bin/env python3
"""
Augment event_pool.json: fill only the EMPTY dates from the Wikimedia
onthisday API (same PD source prefetch_events.py uses). Idempotent:
re-running skips already-populated dates and writes the pool file
incrementally so a crash loses no work. Polite rate (>=1.2s gap) + retry.
"""
import os, json, time, urllib.request, urllib.error

POND = os.path.dirname(os.path.abspath(__file__))
WM = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{mm:02d}/{dd:02d}"
UA = {"User-Agent": "SeymourAbsorber/1.0 (toilet-book daily timeline; contact wubu)"}
POOL = os.path.join(POND, "event_pool.json")

_TS = [0.0]
def _get(url, timeout=10):
    while time.time() - _TS[0] < 1.2:
        time.sleep(0.1)
    _TS[0] = time.time()
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(min(2 ** (attempt + 1), 20)); continue
            return None
        except Exception:
            time.sleep(1)
    return None

def main():
    pool = json.load(open(POOL))
    # ensure all 366 calendar dates exist
    for mm in range(1, 13):
        dim = [0,31,28,31,30,31,30,31,31,30,31,30,31][mm]
        for dd in range(1, dim + 1):
            pool.setdefault(f"{mm:02d}-{dd:02d}", [])
    empty = [k for k, v in pool.items() if not v]
    print(f"POOL: {sum(1 for v in pool.values() if v)}/{len(pool)} populated; "
          f"{len(empty)} empty; filling...", flush=True)
    # sort so progress is deterministic
    filled = 0
    for key in sorted(empty):
        if pool.get(key):   # re-check (resume safety)
            continue
        mm, dd = map(int, key.split("-"))
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
        if evs:
            pool[key] = evs
            filled += 1
        # incremental save every 10 fills (lossless on crash)
        if filled and filled % 10 == 0:
            json.dump(pool, open(POOL, "w"), indent=1)
            print(f"  filled {filled} (total populated {sum(1 for v in pool.values() if v)})", flush=True)
    json.dump(pool, open(POOL, "w"), indent=1)
    nonempty = sum(1 for v in pool.values() if v)
    print(f"DONE: {nonempty}/{len(pool)} dates populated "
          f"({filled} newly filled this run), "
          f"{sum(len(v) for v in pool.values())} total events -> {POOL}", flush=True)

if __name__ == "__main__":
    main()
