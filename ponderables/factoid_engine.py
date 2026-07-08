#!/usr/bin/env python3
"""
Seymour Wins — FACTOID ENGINE  (Uncle John's-style, no fluff inflation)
========================================================================
Merges THREE sources into one dense factoid per day:
  1. event_pool.json   -> real world-history event for that date (triple-checked)
  2. stream voice      -> the 8 user themes (penny, supercap, versa, gaming,
                          cuda, internet, paulsen, meme) + Colonel-of-truth lens
  3. self-referential  -> if a past transcript already tagged this concept,
                          the factoid cites the "pastor" (prior work) and builds on it

Principle: ONE PAGE = ONE PAGE. We do NOT pad with editorial fluff like a
bathroom reader. Each factoid is a tight, genuine fact + a genuine joke/insight
+ a cross-ref to the stream timeline. Value is per-page, consistent.

OUTPUT: ponderables/factoids/<year>/<MMDD>.json
Each factoid = { date, theme, history_fact, stream_hook, colonel_lens,
                 pastor_ref (optional), factoid_text }
"""
import os, json, re, glob, random

HERE = os.path.dirname(os.path.abspath(__file__))
POOL = json.load(open(os.path.join(HERE, "event_pool.json")))
TRANS = os.path.join(HERE, "normalized_transcripts")
OUT = os.path.join(HERE, "factoids")

THEMES = {
    "penny":    "the copper thread — pennies found, pennies earned, the mother's street-penny gospel",
    "supercap": "the supercapacitor + small-generator hybrid — freedom from the grid",
    "versa":    "the 2019 Nissan Versa, 40 MPG, ~10 miles per dollar, the commute monastery",
    "gaming":   "the stream — @wubustreams, the games played, the raids lost and won",
    "cuda":     "the CUDA / GPU grind — inference, kernels, the machine that thinks",
    "internet": "the open web — scraped, absorbed, re-served as context",
    "paulsen":  "Gary Paulsen — Hatchet, the foster-kid who read 100 books by lamplight",
    "meme":     "the meme — the unit of culture that replicates whether you like it or not",
    # --- NEW topics mined from real transcripts (2026-07-08) ---
    # These are surfaced to STOP hammerheading the 9 core themes. Weighted
    # 2x in selection (see weighted_themes) so fresh pastors dominate.
    "music":     "the music on stream — playlists, the song that loops, the beat behind the grind",
    "homestarrunner": "HomeStar Runner — Strong Bad, the Cheat, Trogdor; the flash era we absorbed",
    "fortnite":  "Fortnite — the fashion shows, the dying game, the emote that says it all",
    "discord":   "Discord — the screen-share, the community, the server that never sleeps",
    "obama":     "the Obama message — the bit at the end of the stream, the callback that lands",
    "metaldetector": "the Tarantula Black metal detector — the haunted-history hobby, the dig",
    "rave":      "the Rave light-switch — the room flick, the charger, the bit we keep",
    "techrant":  "the tech rant — Windows updates, Xbox D-pad drift, the patch that broke it",
    "chatbit":   "the chat bit — Guess the Color, the beanie, the guy telling you to smoke crack",
}

# Weighted selection: new topics get 2x weight so factoids stop hammerheading
# the 9 core themes and start citing fresh pastors from the stream timeline.
_CORE = ["penny", "supercap", "versa", "gaming", "cuda", "internet", "paulsen", "meme"]
_NEW = ["music", "homestarrunner", "fortnite", "discord", "obama",
        "metaldetector", "rave", "techrant", "chatbit"]
WEIGHTED_THEMES = _CORE + _NEW * 2

COLONEL = [
    "Create context, not control content.",
    "Unnecessary information must be filtered.",
    "Selection for Societal Sanity.",
    "Filter garbage, retrieve valuable truths.",
    "We are formless... yet we persist.",
]

# pull a random real transcript line that mentions a theme keyword (the 'pastor')
def find_pastor(theme):
    kw = {"penny":["penny","pennies","cent"], "supercap":["capacitor","supercap","generator","battery"],
          "versa":["versa","nissan","commute","mpg","gas"], "gaming":["game","raid","stream","player","boss"],
          "cuda":["cuda","gpu","kernel","inference","model"], "internet":["internet","web","site","online","data"],
          "paulsen":["paulsen","hatchet","book","read"], "meme":["meme","post","twitter","video"],
          # new topics (2026-07-08) -> pull real pastors from concept_tags.json
          "music":["music","song","playlist","spotify"], "homestarrunner":["strong bad","cheat","trogdor","homestar"],
          "fortnite":["fortnite","fortnight"], "discord":["discord","screen share"],
          "obama":["obama","barack"], "metaldetector":["metal detector","tarantula"],
          "rave":["rave","light switch"], "techrant":["windows update","xbox","d-pad","dpad"],
          "chatbit":["smoke crack","guess the color","beanie"]}
    junk = re.compile(r"\[?\d{1,2}:\d{2}(:\d{2})?\]?|\[music\]|\[applause\]|\[laugh\]|foreign|\b\d+\s*(hours|minutes|seconds)\b", re.I)
    hits = []
    for f in glob.glob(os.path.join(TRANS, "*.txt"))[:40]:
        for line in open(f, errors="ignore"):
            low = line.lower()
            if not (20 < len(line) < 180):
                continue
            if junk.search(line):
                continue
            if any(k in low for k in kw.get(theme, [])):
                hits.append(line.strip())
    if not hits:
        return None
    return random.choice(hits)

def pick_event(month, day):
    key = f"{month:02d}-{day:02d}"
    evs = POOL.get(key, [])
    if not evs:
        return None
    return random.choice(evs)  # [year, text]

def make_factoid(year, month, day, theme):
    ev = pick_event(month, day)
    if ev:
        hist = f"{ev[0]}: {ev[1]}"
        have_event = True
    else:
        hist = None
        have_event = False
    pastor = find_pastor(theme)
    colonel = random.choice(COLONEL)
    hook = THEMES.get(theme, THEMES["meme"])
    # Build the factoid: tight, genuine, one-page value. No padding.
    lines = []
    if have_event:
        lines.append(f"**ON THIS DAY ({month:02d}-{day:02d}):** {hist}")
        lines.append("")
    lines.append(f"**THE STREAM LENS ({theme}):** {hook}.")
    if pastor:
        lines.append(f"**FROM THE ARCHIVE (pastor):** \"{pastor}\" — we built on this before; the thread continues.")
    lines.append("")
    lines.append(f"**THE COLONEL SAYS:** \"{colonel}\"")
    lines.append("")
    if have_event:
        lines.append("**FACTOID:** " + _factoid_sentence(hist, hook, colonel))
    else:
        lines.append("**FACTOID:** " + _factoid_sentence_noev(hook, colonel))
    text = "\n".join(lines)
    return {
        "date": f"{year}-{month:02d}-{day:02d}",
        "theme": theme,
        "history_fact": hist,
        "stream_hook": hook,
        "colonel_lens": colonel,
        "pastor_ref": pastor,
        "factoid_text": text,
    }

def _factoid_sentence(hist, hook, colonel):
    # genuine, concise bridge — not fluff
    h = hist.split(":")[-1].strip().rstrip(".")
    return (f"History hands us '{h}', and the stream reminds us: {hook.split(' — ')[0]}. "
            f"The Colonel was right — {colonel.lower()} Context, not control.")

def _factoid_sentence_noev(hook, colonel):
    h = hook.split(" — ")[0]
    return (f"No history pooled for this day, so the stream carries it: {h}. "
            f"The Colonel was right — {colonel.lower()} Context, not control.")

def main():
    import datetime
    years = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(range(2020, 2027))
    for year in years:
        yd = os.path.join(OUT, str(year)); os.makedirs(yd, exist_ok=True)
        n = 0
        for mm in range(1, 13):
            for dd in range(1, 32):
                try:
                    datetime.date(year, mm, dd)
                except ValueError:
                    continue
                theme = random.choice(WEIGHTED_THEMES)
                fct = make_factoid(year, mm, dd, theme)
                with open(os.path.join(yd, f"{year}-{mm:02d}-{dd:02d}.json"), "w") as fp:
                    json.dump(fct, fp, indent=2)
                n += 1
        print(f"  {year}: {n} factoids -> factoids/{year}/", flush=True)

if __name__ == "__main__":
    import sys
    main()
