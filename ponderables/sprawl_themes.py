#!/usr/bin/env python3
"""
Seymour Wins — THEME SPRAWL GENERATOR (New Game Plus / Mathematic Sprawl)
=========================================================================
Expands the 8 seed themes + mined stream vocabulary + Colonel-of-truth (MGS2)
categories + event/date axes into ~1000 distinct THEMES for the daily timeline.

Each theme = {id, label, axis, keywords[], clipart[], colonel_frame, meme_potential}
so fill_year.py can route any day's fact to the richest matching theme, and the
overlap graph can connect themes that share days/keywords (the sprawl).

Run: python3 sprawl_themes.py  ->  ponderables/themes.json
"""
import json, re, itertools
from collections import defaultdict

# ---------------------------------------------------------------------------
# AXIS 1 — SEED LIFE-TOPICS (the user's actual world, from memory + streams)
# ---------------------------------------------------------------------------
LIFE = {
    "penny":    {"label": "Penny / Copper Thread", "kw": ["penny","copper","coin","cent","heads-up","lucky penny","found penny","small change"], "clip": ["penny","coin","copper"], "colonel": "The smallest unit is the one the system ignores — that is where control lives."},
    "supercap": {"label": "Supercapacitor / Energy", "kw": ["supercapacitor","supercap","capacitor","energy storage","instant charge","battery","generator","solar","grid"], "clip": ["battery","energy","bolt"], "colonel": "Energy is stored time. They who control the charge control the clock."},
    "versa":    {"label": "Versa / Commute", "kw": ["versa","nissan","commute","mpg","gas","driving","highway","traffic","road","car","vehicle"], "clip": ["car","road","wheel"], "colonel": "Three hours a day spent between places — that is the rent the terrain collects."},
    "mother":   {"label": "Mother / Penny Motif", "kw": ["mother","mom","penny","diabetes","ran into streets","found pennies","wife","family"], "clip": ["heart","family","penny"], "colonel": "She ran into the streets for pennies. The system was built to make her run."},
    "foster":   {"label": "Foster / Devices Taken", "kw": ["foster","foster care","devices","confiscated","taken away","childhood","grew up"], "clip": ["book","key"], "colonel": "They took the devices so you'd read the world instead. That was the lesson."},
    "paulsen":  {"label": "Paulsen / Wilderness", "kw": ["paulsen","hatchet","gary paulsen","wilderness","survival","terrain","river","forest","cold"], "clip": ["tree","mountain","river"], "colonel": "The terrain does not negotiate. Nature collects what the machine promises you beat."},
    "metalgear": {"label": "Metal Gear / Colonel", "kw": ["metal gear","solid snake","colonel","codec","patriot","raiden","big boss","cyber","ai takeover"], "clip": ["codec","snake"], "colonel": "You are not fighting a villain. You are fighting the system that made the villain necessary."},
    "colonel":  {"label": "Colonel of Truth", "kw": ["colonel","truth","codec","patriot ai","meme theory","information control","propaganda","simulation"], "clip": ["codec","eye"], "colonel": "The Colonel was lying. So is the feed. The difference is the feed never admits it."},
    "cuda":     {"label": "CUDA / Compute", "kw": ["cuda","gpu","rtx","nvidia","compute","tensor","inference","model","llm","transformer","pytorch"], "clip": ["chip","gpu"], "colonel": "Compute is the new combustion. Whoever owns the chips sets the weather."},
    "llm":      {"label": "LLM / AI", "kw": ["llm","language model","ai","chatbot","gpt","prompt","hallucination","neural","inference"], "clip": ["brain","chip"], "colonel": "The model is a very fast opinion-haver. In 2020 the opinions got loud."},
    "diabetes": {"label": "Diabetes / Health", "kw": ["diabetes","insulin","health","blood sugar","illness","hospital","care"], "clip": ["heart","cross"], "colonel": "A body is the first system they told you was yours but billed you for."},
    "ev":       {"label": "EV / Hybrid Architecture", "kw": ["ev","electric","hybrid","supercapacitor","regenerative","motor","battery pack"], "clip": ["car","bolt"], "colonel": "The hybrid is a compromise the system forced. The supercapacitor is the dream it delayed."},
}

# ---------------------------------------------------------------------------
# AXIS 2 — MINED STREAM TOPICS (from mine_themes.py topics.json, top distinctive)
# ---------------------------------------------------------------------------
MINED = {
    "pokemon":   {"label": "Pokémon / Gaming Lore", "kw": ["pokemon","pikachu","trainer","gym","evolve"], "clip": ["game"], "colonel": "Every creature is a captured fact. The dex is just a timeline you can't close."},
    "jeff":      {"label": "Jeff (recurring bit)", "kw": ["jeff"], "clip": ["face"], "colonel": "A name repeated enough becomes a variable. Who is Jeff to the system?"},
    "daniel":    {"label": "Daniel (recurring bit)", "kw": ["daniel"], "clip": ["face"], "colonel": "The second name is the control group. Compare Jeff to Daniel and watch the pattern."},
    "gun":       {"label": "Gun / Conflict", "kw": ["gun","shoot","weapon","fire","attack"], "clip": ["gun"], "colonel": "A weapon is a fact that ends the argument. The feed is a weapon that starts them."},
    "chaos":     {"label": "Chaos / Systems", "kw": ["chaos","break","glitch","crash","error","fail"], "clip": ["storm"], "colonel": "Chaos is the system speaking without the press release."},
    "heat":      {"label": "Heat / Climate", "kw": ["heat","hot","fire","burn","summer","temperature"], "clip": ["sun","fire"], "colonel": "Heat is the bill for every combustion we refused to price."},
    "capture":   {"label": "Capture / Absorb", "kw": ["capture","absorb","record","save","collect"], "clip": ["net"], "colonel": "To capture is to refuse the feed's amnesia. The absorber remembers so you don't have to."},
    "gamer":     {"label": "Gamer / Stream", "kw": ["gamer","play","game","stream","controller","console"], "clip": ["game"], "colonel": "The console became a window when the world broke. We fled the bad sim for the working ones."},
    "car":       {"label": "Car / Machine", "kw": ["car","engine","drive","wheel","motor"], "clip": ["car"], "colonel": "Every vehicle is a thesis about how much of your day you'll sell to travel."},
    "black":     {"label": "Black / Contrast", "kw": ["black","dark","shadow","night"], "clip": ["moon"], "colonel": "The dark is where the feed can't see you. That is why they lit it."},
    "spider":    {"label": "Spider / Web", "kw": ["spider","web","net","tangle"], "clip": ["web"], "colonel": "The web was supposed to catch facts. It caught you instead."},
    "mission":   {"label": "Mission / Objective", "kw": ["mission","objective","task","quest","goal"], "clip": ["flag"], "colonel": "A mission is a story the system tells you so you'll walk the route."},
}

# ---------------------------------------------------------------------------
# AXIS 3 — COLONEL-OF-TRUTH CODEC CATEGORIES (MGS2 spine)
# ---------------------------------------------------------------------------
COLONEL_AXIS = {
    "codec":     {"label": "Codec Transmission", "kw": ["codec","radio","signal","frequency","transmit"], "colonel": "The codec only works if both ends agree on the lie."},
    "patriot":   {"label": "The Patriot AI", "kw": ["patriot","ai control","algorithmic","system","matrix"], "colonel": "The Patriot doesn't hate you. It simply has no use for you unmonetized."},
    "truth":     {"label": "Truth Decay", "kw": ["truth","lie","fake","misinfo","propaganda"], "colonel": "Truth decayed slowly, then all at once, then the feed sold the decay back to you."},
    "memory":    {"label": "Memory / FOXDIE", "kw": ["memory","remember","forget","foxdie","gene"], "colonel": "Memory is the only archive the system can't revoke. That is why they target it."},
    "paranoia":  {"label": "Paranoia / Control", "kw": ["surveil","watch","track","control","paranoia"], "colonel": "The paranoid are right on schedule. The system just renamed their fear 'engagement.'"},
    "simulation":{"label": "Simulation / VR", "kw": ["simulation","virtual","vr","matrix","fake world"], "colonel": "You were born inside a simulation someone else is still debugging."},
}

# ---------------------------------------------------------------------------
# AXIS 4 — EVENT/DATE AXES (onthisday event classes) -> combinatorial sprawl
# ---------------------------------------------------------------------------
EVENT_AXES = {
    "war":      ["war","battle","invasion","siege","attack","bomb","military"],
    "peace":    ["peace","treaty","ceasefire","armistice","agreement"],
    "science":  ["discover","invent","experiment","physics","chemistry","biology","space"],
    "culture":  ["film","music","book","art","premiere","publish","album"],
    "disaster": ["earthquake","flood","fire","crash","explosion","storm","pandemic"],
    "birth":    ["born","birth","founded","established"],
    "death":    ["died","death","killed","assassinated","passed"],
    "tech":     ["computer","internet","software","launch","satellite","chip"],
}

# ---------------------------------------------------------------------------
# BUILD THE SPRAWL
# ---------------------------------------------------------------------------
themes = {}
def add(tid, label, axis, kw, clip, colonel, meme=0):
    themes[tid] = {
        "id": tid, "label": label, "axis": axis,
        "keywords": kw, "clipart": clip,
        "colonel_frame": colonel, "meme_potential": meme,
    }

# 1) base themes (life + mined + colonel axis)
for tid, v in {**LIFE, **MINED, **COLONEL_AXIS}.items():
    kw = v.get("keywords", v.get("kw", []))
    add(tid, v["label"], "base", kw, v.get("clip", ["star"]),
        v.get("colonel", ""), meme=1 if tid in ("meme","gamer","spider") else 0)

# 2) combinatorial sprawl: base theme x event-axis  =>  ~ (32 base) * 8 = 256
combo = 0
for base_id in list(LIFE) + list(MINED):
    base_v = LIFE.get(base_id, MINED.get(base_id))
    base_kw = base_v.get("keywords", base_v.get("kw", []))
    for ev, evkw in EVENT_AXES.items():
        tid = f"{base_id}_{ev}"
        if tid in themes:
            continue
        kw = base_kw[:2] + evkw[:2]
        colonel = base_v.get("colonel", "")
        add(tid, f"{base_v['label']} × {ev.title()}",
            "cross", kw, base_v.get("clip",["star"]), colonel, meme=1)
        combo += 1

# 3) colonel-framed cross: each base theme gets a "truth" variant  => another layer
truth_layer = 0
for base_id in list(LIFE) + list(MINED):
    tid = f"{base_id}_truth"
    if tid in themes:
        continue
    base_v = LIFE.get(base_id, MINED.get(base_id))
    kw = base_v.get("keywords", base_v.get("kw", []))[:2] + ["truth","control"]
    add(tid, f"{base_v['label']} — Colonel's Cut", "colonel_truth", kw,
        base_v.get("clip",["eye"]), "The Colonel's version: " + base_v.get("colonel",""), meme=1)
    truth_layer += 1

# 4) meme dimension spread: internet-culture variants for high-meme bases
meme_layer = 0
for base_id in ["penny","versa","cuda","llm","gamer","spider","chaos"]:
    tid = f"{base_id}_meme"
    if tid in themes:
        continue
    base_v = LIFE.get(base_id, MINED.get(base_id))
    kw = base_v.get("keywords", base_v.get("kw", []))[:1] + ["meme","viral","trend","shitpost"]
    add(tid, f"{base_v['label']} (Meme)", "meme", kw, base_v.get("clip",["star"]),
        "The feed copied it faster than it copied code. That is the only honest archive.", meme=2)
    meme_layer += 1

# 5) multi-theme overlap seeds (the mathematic sprawl nodes): pick pair-combos
overlap_seeds = list(itertools.combinations(list(LIFE) + list(MINED), 2))
overlap_layer = 0
for a, b in overlap_seeds:  # all 496 pairs now
    tid = f"{a}__{b}"
    if tid in themes:
        continue
    va, vb = (LIFE.get(a,MINED.get(a)), LIFE.get(b,MINED.get(b)))
    ka = va.get("keywords", va.get("kw", []))
    kb = vb.get("keywords", vb.get("kw", []))
    ca = va.get("clip",["star"]); cb = vb.get("clip",["star"])
    add(tid, f"{va['label']} ⇄ {vb['label']}", "overlap",
        (ka[:1] + kb[:1]), ca[:1] + cb[:1],
        "Two systems, one feed. The overlap is where the truth leaks.", meme=1)
    overlap_layer += 1

# 6) DECADE layer: base theme x decade axis (the "through the years" sprawl)
DECADES = {
    "2020s": ["2020","2021","2022","2023","2024","covid","lockdown","pandemic"],
    "2010s": ["2010","2015","streaming","smartphone","tweet","meme war"],
    "2000s": ["2001","2008","internet bubble","war on terror","facebook"],
    "1990s": ["1990","1995","dialup","grunge","clinton","sega","nintendo"],
    "1980s": ["1980","1985","cold war","arcade","mtv","reagan"],
    "1970s": ["1970","1975","watergate","oil crisis","disco"],
    "1960s": ["1960","1965","vietnam","moon landing","civil rights"],
}
decade_layer = 0
for base_id in list(LIFE) + list(MINED):
    base_v = LIFE.get(base_id, MINED.get(base_id))
    base_kw = base_v.get("keywords", base_v.get("kw", []))
    base_clip = base_v.get("clip", ["star"])
    for dec, deckw in DECADES.items():
        tid = f"{base_id}_{dec}"
        if tid in themes:
            continue
        kw = base_kw[:1] + deckw[:2]
        add(tid, f"{base_v['label']} — {dec}", "decade",
            kw, base_clip, base_v.get("colonel",""), meme=1)
        decade_layer += 1

# 7) MEME-DEPTH layer: base x meme-format (shitpost / copypasta / viral / remix)
MEMEFMT = {
    "shitpost": ["shitpost","absurd","ironic"],
    "copypasta": ["copypasta","copy","paste","repeat"],
    "remix": ["remix","edit","reaction"],
    "deepfake": ["deepfake","ai face","synthetic"],
}
meme_depth = 0
for base_id in list(LIFE) + list(MINED) + list(COLONEL_AXIS):
    base_v = LIFE.get(base_id, MINED.get(base_id, COLONEL_AXIS.get(base_id, {})))
    base_kw = base_v.get("keywords", base_v.get("kw", []))
    base_clip = base_v.get("clip", ["star"])
    for mf, mkw in MEMEFMT.items():
        tid = f"{base_id}_{mf}"
        if tid in themes:
            continue
        kw = base_kw[:1] + mkw[:2]
        add(tid, f"{base_v['label']} — {mf.title()}", "meme_fmt",
            kw, base_clip, "The format is the message. The feed remixes the truth faster than it reports it.", meme=2)
        meme_depth += 1

# 8) NEWS layer: base x news-class (the "triple-checked news stories" axis)
NEWSCLASS = {
    "headline": ["headline","breaking","report","announce"],
    "investigative": ["investigation","leak","documents","reveal","probe"],
    "human": ["human interest","ordinary","story","person"],
    "technews": ["tech news","launch","update","release"],
    "weird": ["weird","odd","unusual","bizarre","random fact"],
}
news_layer = 0
for base_id in list(LIFE) + list(MINED) + list(COLONEL_AXIS):
    base_v = LIFE.get(base_id, MINED.get(base_id, COLONEL_AXIS.get(base_id, {})))
    base_kw = base_v.get("keywords", base_v.get("kw", []))
    base_clip = base_v.get("clip", ["star"])
    for nc, nckw in NEWSCLASS.items():
        tid = f"{base_id}_news_{nc}"
        if tid in themes:
            continue
        kw = base_kw[:1] + nckw[:2]
        add(tid, f"{base_v['label']} — {nc.title()} News", "news",
            kw, base_clip, "News is the first draft of the feed. Triple-check before you absorb.", meme=1)
        news_layer += 1

# 9) FORMAT layer: base x media-format (clipart/comic/book/audio/podcast)
FORMAT = {
    "clipart": ["clipart","svg","drawing","illustration"],
    "comic": ["comic","panel","strip","graphic"],
    "book": ["book","read","chapter","novel"],
    "audio": ["audio","podcast","voice","sound"],
    "zine": ["zine","pamphlet","leaflet","toilet book"],
}
format_layer = 0
for base_id in list(LIFE) + list(MINED):
    base_v = LIFE.get(base_id, MINED.get(base_id))
    base_kw = base_v.get("keywords", base_v.get("kw", []))
    base_clip = base_v.get("clip", ["star"])
    for fm, fmkw in FORMAT.items():
        tid = f"{base_id}_fmt_{fm}"
        if tid in themes:
            continue
        kw = base_kw[:1] + fmkw[:2]
        add(tid, f"{base_v['label']} — {fm.title()} Format", "format",
            kw, base_clip, base_v.get("colonel",""), meme=1)
        format_layer += 1

# summary + write
out = {
    "meta": {
        "total_themes": len(themes),
        "layers": {
            "base": len(LIFE)+len(MINED)+len(COLONEL_AXIS),
            "cross_event": combo,
            "colonel_truth": truth_layer,
            "meme": meme_layer,
            "overlap": overlap_layer,
            "decade": decade_layer,
            "meme_fmt": meme_depth,
            "news": news_layer,
            "format": format_layer,
        },
        "axes": ["life", "mined_stream", "colonel_codec", "event_date", "meme", "overlap"],
    },
    "themes": themes,
}
with open("ponderables/themes.json", "w") as f:
    json.dump(out, f, indent=2)
print(f"SPRAWL COMPLETE: {len(themes)} themes")
print("layers:", out["meta"]["layers"])
