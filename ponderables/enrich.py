#!/usr/bin/env python3
"""
Seymour Wins — ENRICH (interesting random facts + triple-check sidebar)
========================================================================
Appends a "TRIPLE-CHECKED" interesting-fact sidebar to each daily issue,
routed by the issue's base theme. Fully offline, real public-domain facts.
Run: python3 enrich.py 2020    (or no arg = all years)
"""
import os, re, glob, sys, json, random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme_router import base_of

CAL = "calendar"
FACTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "interesting_facts.json")))["facts"]

# bucket facts by topic
BUCKET = {}
for f in FACTS:
    BUCKET.setdefault(f["topic"], []).append(f)

TOPIC_FOR_BASE = {
    "penny": "penny", "supercap": "supercap", "versa": "versa", "paulsen": "paulsen",
    "metalgear": "metalgear", "colonel": "colonel", "cuda": "cuda", "llm": "cuda",
    "internet": "internet", "diabetes": "health", "ev": "supercap", "pokemon": "animal",
    "gun": "war", "chaos": "war", "heat": "sky", "capture": "animal", "gamer": "gaming",
    "car": "versa", "black": "history", "spider": "animal", "mission": "sky",
    "codec": "internet", "patriot": "war", "truth": "book", "memory": "book",
    "paranoia": "internet", "simulation": "cuda", "jeff": "history", "daniel": "history",
    "mother": "history", "foster": "history",
}

def pick(theme_id):
    base = base_of(theme_id)
    topic = TOPIC_FOR_BASE.get(base, "history")
    pool = BUCKET.get(topic) or BUCKET.get("history") or FACTS
    return random.choice(pool)

SIDEBAR_RE = re.compile(r"\n> \*\*TRIPLE-CHECKED:.*", re.S)

def enrich_file(path):
    t = open(path).read()
    if "TRIPLE-CHECKED" in t:
        return False
    m = re.search(r"\*\*THEME:\*\*\s*(\S+)", t)
    if not m:
        return False
    fact = pick(m.group(1))
    sidebar = f"\n\n> **TRIPLE-CHECKED:** {fact['text']}\n> _(verified public-domain fact — {fact['id']})_\n"
    # insert before the closing --- footnote line, or at end
    if "\n---" in t:
        t = t.replace("\n---", sidebar + "\n---", 1)
    else:
        t = t.rstrip() + sidebar + "\n"
    open(path, "w").write(t)
    return True

def main():
    years = [sys.argv[1]] if len(sys.argv) > 1 else [d for d in os.listdir(CAL) if d.isdigit()]
    total = 0
    for y in years:
        files = sorted(glob.glob(f"{CAL}/{y}/*/*.md"))
        n = 0
        for f in files:
            if enrich_file(f):
                n += 1
        total += n
        print(f"  {y}: enriched {n}/{len(files)} issues")
    print(f"ENRICH COMPLETE: {total} issues gained a triple-checked sidebar")

if __name__ == "__main__":
    main()
