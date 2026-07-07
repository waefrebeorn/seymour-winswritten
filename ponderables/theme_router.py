#!/usr/bin/env python3
"""
Seymour Wins — THEME ROUTER (uses the 1087-theme sprawl taxonomy)
=================================================================
Routes a day's fact text to the richest matching theme from themes.json,
with deterministic even-spread fallback so no theme pile-up occurs.
Also exposes the Colonel-of-truth codec frame for the assigned theme.

Run inside fill_year.py:  from theme_router import route_theme, colonel_frame
"""
import json, re, random, os

THEMES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "themes.json")))["themes"]

# base themes (axis=='base') used for the even-spread fallback ring
BASE = [tid for tid, t in THEMES.items() if t["axis"] == "base"]
# order base themes for round-robin
RING = [t for t in ["penny","supercap","versa","mother","foster","paulsen",
                    "metalgear","colonel","cuda","llm","diabetes","ev",
                    "pokemon","jeff","daniel","gun","chaos","heat","capture",
                    "gamer","car","black","spider","mission","codec","patriot",
                    "truth","memory","paranoia","simulation"]
        if t in BASE] or BASE

_state = {"i": 0}

def _kw_hits(text):
    """Return list of (theme_id, weight) for themes whose keywords appear in text."""
    text = text.lower()
    hits = []
    for tid, th in THEMES.items():
        w = 0
        for k in th["keywords"]:
            if k and k in text:
                w += 1
        if w:
            hits.append((tid, w))
    return hits

def route_theme(text):
    """Pick the best theme for this fact. Prefer specific (non-base cross/truth)
    hits; else a base hit; else even-spread round-robin."""
    global _state
    hits = _kw_hits(text)
    if hits:
        rank = {"base": 0, "cross": 1, "colonel_truth": 2, "news": 3,
                "decade": 4, "meme_fmt": 5, "meme": 6, "format": 7, "overlap": 8}
        hits.sort(key=lambda h: (-h[1], rank.get(THEMES[h[0]]["axis"], 9)))
        return hits[0][0]
    tid = RING[_state["i"] % len(RING)]
    _state["i"] += 1
    return tid

def base_of(theme_id):
    """Extract the base theme id from any sprawl theme id (x_event, x_truth, x__y, x_2020s, x_memt, x_news_nc, x_fmt_fm)."""
    if theme_id in THEMES and THEMES[theme_id]["axis"] == "base":
        return theme_id
    # split on first separator
    for sep in ["__", "_news_", "_fmt_", "_20", "_19", "_201", "_200", "_199", "_198", "_197", "_196"]:
        if sep in theme_id:
            cand = theme_id.split(sep)[0]
            if cand in THEMES:
                return cand
    # generic: strip trailing _word
    parts = theme_id.rsplit("_", 1)
    if len(parts) == 2 and parts[0] in THEMES:
        return parts[0]
    return theme_id

def colonel_frame(theme_id):
    th = THEMES.get(theme_id, {})
    return th.get("colonel_frame", "")

def theme_label(theme_id):
    return THEMES.get(theme_id, {}).get("label", theme_id)

def theme_clipart(theme_id):
    return THEMES.get(theme_id, {}).get("clipart", ["star"])

if __name__ == "__main__":
    import glob, os
    for f in sorted(glob.glob("ponderables/calendar/2020/*/*.md"))[:5]:
        t = open(f).read()
        m = re.search(r"\*\*FACT:\*\*\s*\d{4}:\s*(.+)", t)
        if m:
            fact = m.group(1)
            tid = route_theme(fact)
            print(f"{os.path.basename(f)} -> {tid} ({theme_label(tid)})")
            print("   colonel:", colonel_frame(tid)[:70])
