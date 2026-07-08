#!/usr/bin/env python3
"""Retry-only backfill for event_pool dates that still have no events.
Slower throttle + more retries to distinguish rate-limited failures from
genuinely-empty API responses. Idempotent: skips populated dates, saves
incrementally."""
import os, json, time, urllib.request, urllib.error

POND = os.path.dirname(os.path.abspath(__file__))
WM = "https://api.wikimedia.org/feed/v1/wikipedia/en/onthisday/events/{mm:02d}/{dd:02d}"
UA = {"User-Agent": "SeymourAbsorber/1.0 (toilet-book daily timeline; contact wubu)"}
POOL = os.path.join(POND, "event_pool.json")

_TS = [0.0]
def _get(url, timeout=15):
    while time.time() - _TS[0] < 2.0:   # slower
        time.sleep(0.15)
    _TS[0] = time.time()
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(5):            # more retries
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                time.sleep(min(3 * (attempt + 1), 30)); continue
            return None
        except Exception:
            time.sleep(2)
    return None

def main():
    pool = json.load(open(POOL))
    empty = [k for k, v in pool.items() if not v]
    print(f"Retrying {len(empty)} still-empty dates (slower, more retries)...", flush=True)
    filled = 0
    for key in sorted(empty):
        if pool.get(key):
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
            print(f"  {key}: +{len(evs)} events", flush=True)
        else:
            print(f"  {key}: STILL EMPTY (api returned nothing)", flush=True)
        if filled % 5 == 0:
            json.dump(pool, open(POOL, "w"), indent=1)
    json.dump(pool, open(POOL, "w"), indent=1)
    nonempty = sum(1 for v in pool.values() if v)
    print(f"RETRY DONE: {nonempty}/{len(pool)} populated ({filled} filled this pass)", flush=True)

if __name__ == "__main__":
    main()
