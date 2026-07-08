#!/usr/bin/env python3
"""
Seymour Wins — MULTIVERSE GENERATOR (alternate-universe daily pages)
=====================================================================
For every real daily anchor (calendar/YYYY/MM/DD.md) we fork up to 30
ALTERNATE-UNIVERSE pages. Each AU page:
  * is clearly labeled SPECULATIVE (never presented as a real fact)
  * is grounded in the SAME real anchor (we mutate the anchor, not invent
    a new fake history)
  * carries a SKILL tag (what craft this universe exercises)
  * gets its own Colonel codec transmission + a "what-if" reflection

This fills multi-page days (target up to 30 pages/day) without ever
fabricating a real historical claim. The real anchor stays sacred.

Run: python3 multiverse.py 2020          (one year)
     python3 multiverse.py                (all years)
     python3 multiverse.py 2020 --per 5  (only 5 AUs/day, fast test)
"""
import os, re, sys, json, random, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme_router import base_of, colonel_frame, theme_label

CAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "calendar")
PER = int(os.environ.get("MV_PER", "30"))

# ---- AU universe archetypes (each = a skill + a mutation lens) ----
UNIVERSES = [
    ("u_whatif",      "What-If History",   "counterfactual", "Take the real anchor and flip ONE decisive variable; trace the branch."),
    ("u_sci-fi",      "Science Fiction",    "worldbuilding",  "Push the anchor's technology to its logical extreme in a future setting."),
    ("u_noir",        "Noir / Detective",   "narrative",      "Retell the anchor as a hardboiled investigation where the fact is a clue."),
    ("u_myth",        "Myth & Folklore",    "symbolism",      "Recast the anchor as a myth the descendants would tell around a fire."),
    ("u_cyber",       "Cyberpunk",          "systems",        "The anchor happens inside a network; the feed is the antagonist."),
    ("u_solarpunk",   "Solarpunk",          "design",         "The anchor resolved by a community that chose repair over extraction."),
    ("u_alt-hist",    "Alt-History",        "timeline",       "A different empire / calendar owned this date; map the divergence."),
    ("u_horror",      "Cosmic Horror",      "atmosphere",     "The anchor is the first symptom of something older waking up."),
    ("u_comedy",      "Absurdist Comedy",   "voice",          "The anchor as bureaucratic farce; the form ate the function."),
    ("u_western",     "Western Frontier",   "setting",        "The anchor on the frontier, where the terrain sets the rules."),
    ("u_anime",       "Anime Arc",          "structure",      "The anchor as a training-arc beat; failure is the curriculum."),
    ("u_kitchen",     "Kitchen-Sink Drama", "domestic",       "The anchor filtered through one household's ordinary evening."),
    ("u_conspiracy",  "Paranoia Spec",      "unreliable",     "The anchor is true but the surrounding story is the operation."),
    ("u_utopia",      "Utopian Mirror",     "critique",       "The anchor never happened because the system was built otherwise."),
    ("u_dystopia",    "Dystopian Caution",  "warning",        "The anchor is the seed of the world that followed."),
    ("u_magical",     "Magical Realism",    "lyric",          "The anchor with one impossible law added; everyone accepts it."),
    ("u_thriller",    "Political Thriller", "pace",           "The anchor as the inciting incident of a clock-ticking plot."),
    ("u_documentary", "Mock Doc",           "form",           "A faux field-producer's note about capturing the anchor on tape."),
    ("u_game",        "Game-Rules Spec",    "mechanics",      "The anchor expressed as a rule, a resource, a win condition."),
    ("u_poem",        "Prose Poem",         "language",       "The anchor compressed into image and rhythm."),
    ("u_letter",      "Future Letter",      "persona",        "A descendant writes back to the day the anchor happened."),
    ("u_trial",       "Courtroom",          "argument",       "The anchor on trial; evidence vs. the story we told about it."),
    ("u_radio",       "Radio Drama",        "sound",          "The anchor as a 1940s broadcast with static and a sponsor."),
    ("u_oral",        "Oral History",       "memory",         "The anchor as the version the survivor kept telling."),
    ("u_code",        "Codex / Law",        "codify",         "The anchor written as the first article of a new code."),
    ("u_dream",       "Dream Logic",        "surreal",        "The anchor dissolved into the logic of sleep."),
    ("u_market",      "Market Spec",        "economics",      "The anchor priced, shorted, and sold before it finished happening."),
    ("u_ritual",      "Ritual",             "practice",       "The anchor become a ceremony repeated so it cannot be lost."),
    ("u_archive",     "Dead-Letter Archive","curation",       "The anchor misfiled, rediscovered, re-framed by the archivist."),
    ("u_signal",      "First Contact",      "alien",          "The anchor is what the signal answers."),
]

def parse_anchor(path):
    t = open(path).read()
    m = re.search(r"\*\*FACT:\*\*\s*(\d{4}):\s*(.+?)(¹|$)", t, re.S)
    th = re.search(r"\*\*THEME:\*\*\s*(\S+)", t)
    if not m:
        return None, None, None
    return m.group(1), m.group(2).strip(), (th.group(1) if th else "meme")

def mutate(anchor_text, arche, lens):
    """Return a 2-3 sentence speculative AU paragraph grounded in the anchor."""
    a = anchor_text.rstrip(". ")
    # deterministic-ish variation by archetype keyword set
    openers = {
        "counterfactual": f"What if the one variable had flipped? {a}. ",
        "worldbuilding": f"Push the tech further: {a} — and then the system finished thinking. ",
        "narrative": f"A detective logs the clue: {a}. The file stays open. ",
        "symbolism": f"The elders would tell it this way: {a}, and the telling became the law. ",
        "systems": f"Inside the network it read as: {a}. The feed decided what you saw next. ",
        "design": f"A community chose repair: {a}, and built the fix before the news arrived. ",
        "timeline": f"Under a different calendar this date belonged to another empire; still: {a}. ",
        "atmosphere": f"The first symptom was small: {a}. Something older had noticed. ",
        "voice": f"Bureaucracy ate the event: {a}. Form triumphed over function, as usual. ",
        "setting": f"On the frontier the terrain ruled: {a}. The land set the terms. ",
        "structure": f"Training arc beat: {a}. Failure was the curriculum. ",
        "domestic": f"One household, that evening: {a}. The kettle kept boiling. ",
        "unreliable": f"The fact is true; the story around it is the operation. {a}. ",
        "critique": f"In a world built otherwise, this never happened — but notice: {a}. ",
        "warning": f"The seed of the world that followed: {a}. ",
        "lyric": f"One impossible law added, and everyone accepted it: {a}. ",
        "pace": f"Inciting incident, clock ticking: {a}. ",
        "form": f"Field note — we caught it on tape: {a}. ",
        "mechanics": f"RULE: {a}. COST: one truth. WIN: the copy that survives. ",
        "language": f"{a}. (say it small. say it again, slower.) ",
        "persona": f"Dear ancestor — on the day {a}, you did not know it was the hinge. ",
        "argument": f"Exhibit A: {a}. The story we told about it is not the evidence. ",
        "sound": f"...we interrupt this broadcast: {a}. Stay tuned. ",
        "memory": f"The version she kept telling: {a}. ",
        "codify": f"ARTICLE I: {a}. Let it be written so it cannot be unwritten. ",
        "surreal": f"In the dream the fact loosens: {a}, and then the room is a different room. ",
        "economics": f"Priced, shorted, sold before it finished: {a}. ",
        "practice": f"Made into ceremony so it could not be lost: {a}. ",
        "curation": f"Misfiled, rediscovered, re-framed: {a}. ",
        "alien": f"The signal answered: {a}. ",
    }
    body = openers.get(lens, f"In another world: {a}. ")
    body += "This is SPECULATIVE FICTION forked from a verified anchor — not a historical claim."
    return body

def gen_for(path, per):
    yrtxt, anchor, theme = parse_anchor(path)
    if not anchor:
        return 0
    base = base_of(theme)
    out_dir = path.replace(".md", "_au")
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for i, (uid, name, skill, lens_desc) in enumerate(UNIVERSES[:per]):
        para = mutate(anchor, name, skill)
        colonel = colonel_frame(f"{base}_{uid}") if f"{base}_{uid}" in __import__("theme_router").THEMES else colonel_frame(theme)
        page = f"""**PAGE:** ALTERNATE UNIVERSE {i+1:02d}/{per:02d}
**UNIVERSE:** {name} ({uid})
**SKILL:** {skill}
**GROUNDING FACT:** {yrtxt}: {anchor}¹
**MODE:** SPECULATIVE FICTION (forked from a verified anchor — not a historical claim)

{para}

> **COLONEL (codec transmission):** {colonel}

The fossil record above is real. This page is what the feed would have invented if the day had gone differently.
"""
        with open(os.path.join(out_dir, f"{uid}.md"), "w") as f:
            f.write(page)
        written += 1
    return written

def main():
    argv = sys.argv[1:]
    year_args = [a for a in argv if a.isdigit()]
    years = year_args if year_args else [d for d in os.listdir(CAL) if d.isdigit()]
    per = PER
    if "--per" in argv:
        per = int(argv[argv.index("--per") + 1])
    total = 0
    days = 0
    for y in years:
        files = sorted(glob.glob(f"{CAL}/{y}/*/*.md"))
        for f in files:
            if f.endswith("_au") or "_au/" in f:
                continue
            n = gen_for(f, per)
            if n:
                days += 1
                total += n
        print(f"  {y}: {days} days, {total} AU pages so far", flush=True)
    print(f"MULTIVERSE COMPLETE: {days} days, {total} alternate-universe pages ({per}/day target)")

if __name__ == "__main__":
    main()
