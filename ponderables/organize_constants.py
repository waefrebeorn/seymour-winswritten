#!/usr/bin/env python3
"""
Seymour Wins — ORGANIZE CONSTANTS (Cambrian overlap engine)
Connects the 100 daily constants to the user's stream transcripts, producing
the memetic-overlap timeline: each constant becomes a thread; stream moments
attach as mutations on that thread.

Modes:
  --list                 show all 100 constants (id | theme | stream | name)
  --by-theme penny       filter constants by clipart theme
  --by-stream gaming_stream   filter by stream linkage
  --match "text..."      tag a stream moment to best-matching constants
  --thread DC001         show one constant's full record (its vertical thread)
  --calendar 2020 01     emit overlap entries into calendar/YYYY/MM from constants

The 'match' mode is the Cambrian engine: a raw transcript line -> ranked
constants by keyword + theme + stream affinity. This is how your streams
'radiate' memetic overlap onto the daily substrate.
"""
import os, sys, json, re, argparse
from collections import Counter

ROOT = "/home/wubu/seymour-project"
CAL_JSON = f"{ROOT}/ponderables/daily_constants.json"
CAL_DIR = f"{ROOT}/ponderables/calendar"

def load():
    with open(CAL_JSON) as f:
        return json.load(f)

# keyword hints per constant for matching transcript text
KW = {
    "DC001": ["sunrise", "dawn", "morning", "first light"],
    "DC002": ["sunset", "dusk", "evening", "golden hour"],
    "DC003": ["day", "night", "rotate", "cycle of the day"],
    "DC004": ["moon", "crescent", "lunar", "phase"],
    "DC005": ["tide", "tidal", "ocean level", "shore"],
    "DC007": ["solar wind", "aurora", "magnetosphere", "space weather"],
    "DC008": ["leaf", "plant", "photosynthesis", "green"],
    "DC009": ["rain", "storm", "wet", "downpour"],
    "DC010": ["wind", "gust", "breeze"],
    "DC011": ["current", "ocean current", "sea flow"],
    "DC015": ["tree", "ring", "growth", "forest"],
    "DC016": ["bacteria", "microbe", "cell divide", "colony"],
    "DC017": ["bird", "migration", "geese", "flock"],
    "DC018": ["aurora", "northern light", "polar"],
    "DC021": ["heart", "beat", "pulse", "cardiac"],
    "DC022": ["breath", "breathe", "inhale", "exhale"],
    "DC023": ["cell", "replace", "shed", "renew"],
    "DC024": ["dream", "rem", "sleep story", "night vision"],
    "DC025": ["blink", "eye flick", "micro-blackout"],
    "DC027": ["gut", "stomach", "digestion", "bacteria gut"],
    "DC028": ["neuron", "brain fire", "synapse", "thought spark"],
    "DC029": ["blood", "circulate", "oxygen", "vein"],
    "DC030": ["immune", "sick", "fight infection", "antibody"],
    "DC031": ["sleep", "pass out", "crash", "rest"],
    "DC032": ["hungry", "hunger", "eat", "food"],
    "DC033": ["thirst", "thirsty", "water", "drink"],
    "DC034": ["temperature", "fever", "cold", "warm"],
    "DC035": ["melatonin", "sleepy", "tired night", "drowsy"],
    "DC036": ["cortisol", "stress wake", "alarm", "anxious morning"],
    "DC037": ["tear", "cry", "weep", "eye water"],
    "DC039": ["skin", "regenerate", "callus", "heal"],
    "DC040": ["vocal", "voice", "talk", "speak", "narrate"],
    "DC041": ["commute", "drive", "traffic", "transit", "versa"],
    "DC042": ["meal", "eat", "food", "dinner", "breakfast"],
    "DC043": ["money", "buy", "spend", "cost", "penny", "coin"],
    "DC044": ["conversation", "talk", "chat", "speak"],
    "DC045": ["born", "birth", "baby", "new life"],
    "DC046": ["die", "death", "dead", "passed"],
    "DC047": ["love", "crush", "fall for", "affection"],
    "DC048": ["argument", "fight", "flame", "war"],
    "DC049": ["laugh", "lol", "funny", "humor"],
    "DC050": ["cry", "sad", "tears", "grief"],
    "DC051": ["phone", "check phone", "screen tap", "scroll phone"],
    "DC052": ["email", "mail", "inbox"],
    "DC053": ["news", "headline", "article", "read"],
    "DC054": ["ad", "commercial", "sponsor", "promo"],
    "DC055": ["lie", "fake", "bs", "cap"],
    "DC056": ["promise", "swear", "vow"],
    "DC057": ["stranger", "pass by", "crowd", "silent"],
    "DC058": ["queue", "line", "wait", "line up"],
    "DC059": ["decision", "choose", "decide", "pick"],
    "DC060": ["habit", "routine", "autopilot", "same"],
    "DC061": ["packet", "route", "network", "ping"],
    "DC062": ["search", "google", "query", "lookup"],
    "DC063": ["meme", "share", "repost", "clip spread"],
    "DC064": ["upload", "video", "post", "vod"],
    "DC065": ["deploy", "ship code", "patch", "update"],
    "DC066": ["ai", "model", "inference", "bot think"],
    "DC067": ["bot", "crawl", "scrape", "spider"],
    "DC068": ["password", "login", "log in", "auth"],
    "DC069": ["notification", "ping", "alert", "bell"],
    "DC070": ["stream", "live", "go live", "broadcast"],
    "DC071": ["encrypt", "key", "crypto", "secure"],
    "DC072": ["cache", "invalidate", "refresh stale"],
    "DC073": ["backup", "save", "archive", "preserve"],
    "DC074": ["feed", "rank", "algorithm", "for you"],
    "DC075": ["cookie", "track", "privacy", "profile"],
    "DC076": ["market", "stock", "trade open", "exchange"],
    "DC077": ["factory", "produce", "manufacture", "line"],
    "DC078": ["truck", "deliver", "ship", "cargo"],
    "DC079": ["light", "lamp", "switch on", "dusk light"],
    "DC080": ["engine", "ignite", "start car", "combustion"],
    "DC081": ["charge", "battery", "plug in", "dock"],
    "DC082": ["atm", "cash", "withdraw", "money wall"],
    "DC083": ["harvest", "crop", "farm", "reap"],
    "DC084": ["trash", "garbage", "collect", "bin"],
    "DC085": ["grid", "power", "electric balance", "blackout"],
    "DC086": ["train", "rail", "depart", "freight"],
    "DC087": ["ship", "dock", "port", "container"],
    "DC088": ["plane", "land", "flight", "jet"],
    "DC089": ["coin", "jingle", "change", "penny sound"],
    "DC090": ["traffic light", "red light", "stop", "green"],
    "DC091": ["attention", "focus shift", "distract", "adhd"],
    "DC092": ["memory", "remember", "recall", "forge"],
    "DC093": ["forget", "memory loss", "blank", "erase"],
    "DC094": ["worry", "anxiety", "stress", "fear"],
    "DC095": ["plan", "schedule", "intend", "map out"],
    "DC096": ["bored", "boredom", "itch", "nothing to do"],
    "DC097": ["song stuck", "earworm", "hum", "loop in head"],
    "DC098": ["deja vu", "familiar", "ghost memory"],
    "DC099": ["hope", "optimism", "believe", "small win"],
    "DC100": ["penny found", "heads up", "lucky cent", "sign"],
}

def match_constants(text, doc, top=5):
    t = text.lower()
    scores = []
    for c in doc["constants"]:
        s = 0
        kws = KW.get(c["id"], [])
        for kw in kws:
            if kw in t:
                s += 3
        # theme/stream affinity: weight by overlap text
        if c["name"].lower() in t:
            s += 5
        if c["stream_link"].replace("_", " ") in t:
            s += 2
        if s > 0:
            scores.append((s, c))
    scores.sort(key=lambda x: -x[0])
    return [c for s, c in scores[:top]]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--by-theme", help="filter by theme")
    ap.add_argument("--by-stream", help="filter by stream_link")
    ap.add_argument("--match", help="tag a transcript line to constants")
    ap.add_argument("--thread", help="show one constant's full record")
    ap.add_argument("--calendar", nargs=2, metavar=("YYYY", "MM"),
                    help="emit overlap entries into calendar/YYYY/MM")
    args = ap.parse_args()

    doc = load()
    if args.list:
        for c in doc["constants"]:
            print(f"{c['id']} | {c['theme']:9} | {c['stream_link']:13} | {c['name']}")
        return
    if args.by_theme:
        for c in doc["constants"]:
            if c["theme"] == args.by_theme:
                print(f"{c['id']} {c['name']}")
        return
    if args.by_stream:
        for c in doc["constants"]:
            if c["stream_link"] == args.by_stream:
                print(f"{c['id']} [{c['theme']}] {c['name']}")
        return
    if args.thread:
        c = next((x for x in doc["constants"] if x["id"] == args.thread), None)
        print(json.dumps(c, indent=2))
        return
    if args.match:
        hits = match_constants(args.match, doc)
        if not hits:
            print("no strong match — this moment may be a NEW constant (extend BASE).")
            return
        print(f"TRANSCRIPT: {args.match}\n=> overlaps:")
        for c in hits:
            print(f"  {c['id']} [{c['theme']}/{c['stream_link']}] {c['name']}")
            print(f"     thread: {c['overlap']}")
        return
    if args.calendar:
        y, m = int(args.calendar[0]), int(args.calendar[1])
        os.makedirs(f"{CAL_DIR}/{y:04d}/{m:02d}", exist_ok=True)
        n = 0
        for c in doc["constants"]:
            if c["stream_link"] == "all" or c["universal"]:
                # emit as a daily-overlap seed for the 1st of the month (demo)
                pass
        # emit all 100 as a single 'constants index' entry set across the month demo
        for i, c in enumerate(doc["constants"], 1):
            day = min(i, 28)
            path = f"{CAL_DIR}/{y:04d}/{m:02d}/{day:02d}_c{i:03d}.md"
            body = (f"**TITLE:** {c['name']} (Daily Constant {c['id']})\n"
                    f"**THEME:** {c['theme']}\n"
                    f"**STREAM:** {c['stream_link']}\n"
                    f"**FACT:** Every day, everywhere: {c['name']}. {c['overlap']}\n\n"
                    f"{c['instance']}\n\n"
                    f"This is thread {c['id']} in the memetic-overlap timeline. "
                    f"Your stream transcripts mutate it daily.\n")
            with open(path, "w") as f:
                f.write(body)
            n += 1
        print(f"emitted {n} constant-thread seeds into calendar/{y:04d}/{m:02d}/")
        return
    # default: report
    print(f"{doc['meta']['count']} constants. Use --list / --match / --calendar. "
          f"themes={doc['meta']['themes']}")

if __name__ == "__main__":
    main()
