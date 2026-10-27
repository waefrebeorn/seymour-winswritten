#!/usr/bin/env python3
"""
Seymour Wins — THEME MAPPER
Maps a real-world event text -> a clipart theme + a memetic-angle template.

Used by fill_year.py so every daily issue gets on-theme clipart and a
Seymour-voice reflection, without hand-authoring 2,190 entries.
"""
import re

# theme -> list of keyword matches (lowercased substring or regex)
THEME_KEYWORDS = {
    "penny":     [r"\b(coin|cent|penny|currency|mint|econom|inflation|bank|stock|trade|tariff|price)\b"],
    "supercap":  [r"\b(battery|capacitor|energy|power|grid|electric|engine|motor|solar|reactor|fuel)\b"],
    "versa":     [r"\b(car|vehicle|truck|road|highway|driver|crash|traffic|auto|transport|train|plane|flight)\b"],
    "gaming":    [r"\b(game|console|video|playstation|xbox|nintendo|arcade|esports|gamer)\b"],
    "cuda":      [r"\b(computer|software|chip|processor|silicon|ai |algorithm|data|internet|website|social media|app|google|apple|microsoft|tech)\b"],
    "internet":  [r"\b(internet|web|online|social|meme|virus|hack|leak|privacy|facebook|twitter|youtube|reddit)\b"],
    "paulsen":   [r"\b(book|novel|author|writer|library|wilderness|survive|forest|nature|explore|expedition)\b"],
    "meme":      [r"\b(war|peace|treaty|election|president|king|queen|revolution|protest|court|law|political|scandal|celebrity|death|born|died)\b"],
}

# ordered preference when multiple match (first wins)
THEME_ORDER = ["penny", "supercap", "versa", "gaming", "cuda", "internet", "paulsen", "meme"]

def map_theme(text):
    t = text.lower()
    for theme in THEME_ORDER:
        for pat in THEME_KEYWORDS[theme]:
            if re.search(pat, t):
                return theme
    return "meme"  # default: history is mostly people/events -> meme theme

# memetic-angle template per theme (Seymour voice, parameterized by event + year)
ANGLE = {
    "penny": (
        "The copper thread again. Under the memetic lens, it's a transaction of meaning "
        "disguised as a transaction of money. The price moves; the *story* about the price moves "
        "faster. Seymour's law: a penny is the only coin small enough that everybody ignores it "
        "and significant enough that nobody forgets finding one heads-up."),
    "supercap": (
        "It's an energy story, and energy is just stored time. The Cambrian explosion of "
        "2020 was partly an energy story — suddenly every screen was a battery with a hostage "
        "inside. The supercapacitor dream (instant charge, no decay) is the human dream of patience "
        "without waiting. We keep trying to engineer the wait out of life."),
    "versa": (
        "It's a movement story. The Versa gets ~40mpg and the commute is 1.5 hours each way — "
        "three hours of life per day spent *between* places, which is exactly where the mind does "
        "its best wandering. Every vehicle is a thesis about how much of your day you're willing to "
        "sell to travel. The crash, the road, the traffic: the terrain collects its rent."),
    "gaming": (
        "It's a play story, and play is how the species rehearses survival. The lockdown made "
        "the console a window — gaming went from pastime to primary social substrate in ten weeks. "
        "Every game is a tiny contained world with fair rules; the pandemic was an uncontained world "
        "with none. We fled the broken simulation for the working ones."),
    "cuda": (
        "It's a compute story. Compute is the new combustion — whoever has the chips sets the "
        "weather. The Cambrian explosion ran on GPUs; the memes that won were the ones rendered "
        "fastest. A processor is just a very fast opinion-haver, and in 2020 the opinions got loud."),
    "internet": (
        "It's a network story. The internet is the only organism that grew a new body plan "
        "every time someone was bored on a Tuesday. 2020 was its Cambrian: Zoom, TikTok, the "
        "toilet-paper-hoarder meme — all evolved in weeks. The fact and the feed diverged by six "
        "weeks, and the feed won."),
    "paulsen": (
        "It's a wilderness story. Paulsen's lesson: the terrain doesn't negotiate. A machine "
        "promises you've beaten nature; nature collects. The lockdown was a wilderness of the living "
        "room — we rediscovered that four walls are also terrain, and they also charge rent."),
    "meme": (
        "It's a people story, and people are the original meme — we copy each other faster than "
        "we copy code. History is the fossil record of which copies survived. The Cambrian explosion "
        "of 2020 proved the rule: when the environment changes fast, the copies that propagate are "
        "the ones built for speed, not truth."),
}

def angle(theme, event, year):
    return ANGLE.get(theme, ANGLE["meme"]).format(event=event, year=year)

# Curated clipart per theme (on-theme SVG chosen by hand from assets/clipart/<theme>/)
# so the art matches the entry instead of grabbing the alphabetically-first file.
CURATED_SVG = {
    "penny":     "oc_coiny-bfdi-lemmling-style.svg",   # cohesive cartoon coin
    "supercap":  "oc_energy-level-4-in-blue.svg",       # battery/energy meter
    "versa":     "oc_old-car.svg",                       # car (the commute)
    "gaming":    "oc_gaming-console-gamepad-icon.svg",  # gamepad
    "cuda":      "oc_retro-beige-pc-computer-case-icon.svg",  # beige PC
    "internet":  "oc_neo-fluo-tribalism-face.svg",      # network/meme face
    "paulsen":   "oc_open-book-black-and-white.svg",    # book / wilderness lore
    "meme":      "oc_neo-fluo-tribalism-face.svg",      # tribalism face (on-theme)
    "gaming_stream": "oc_gaming-console-gamepad-icon.svg",  # gamepad (gaming theme)
    "night_think": "oc_open-book-black-and-white.svg",  # book / night reading
}

import os
CLIP = "/home/wubu/seymour-project/assets/clipart"

# theme -> actual clipart directory (handles stream/think suffixes that have no own dir)
THEME_DIR = {
    "gaming_stream": "gaming",
    "night_think": "paulsen",
}

def _dir_for(theme):
    if os.path.isdir(f"{CLIP}/{theme}"):
        return f"{CLIP}/{theme}"
    d = THEME_DIR.get(theme)
    if d and os.path.isdir(f"{CLIP}/{d}"):
        return f"{CLIP}/{d}"
    # strip suffix (gaming_stream -> gaming, night_think -> night)
    base = theme.split("_")[0]
    if base != theme and os.path.isdir(f"{CLIP}/{base}"):
        return f"{CLIP}/{base}"
    return None

def _svgs_in(theme):
    d = _dir_for(theme)
    if not d:
        return []
    return sorted(f for f in os.listdir(d) if f.endswith(".svg"))

def pick_svg(theme, rotation_index=0):
    """Return an on-theme SVG path, rotating through all SVGs in the dir so a
    100-page volume doesn't repeat the same 3 images. `rotation_index` selects
    which file; we prefer the curated pick first, then cycle the rest."""
    d = _dir_for(theme)
    if not d:
        return None
    svgs = _svgs_in(theme)
    if not svgs:
        return None
    pref = CURATED_SVG.get(theme)
    # Build an ordering: curated first (if present), then the rest in dir order.
    ordered = []
    if pref and pref in svgs:
        ordered.append(pref)
    ordered += [s for s in svgs if s != pref]
    if not ordered:
        ordered = svgs
    chosen = ordered[rotation_index % len(ordered)]
    return f"{d}/{chosen}"
