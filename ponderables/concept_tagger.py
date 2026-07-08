#!/usr/bin/env python3
"""
Seymour Wins — CONCEPT TAGGER (self-referential 'pastor' system)
================================================================
Scans stream transcripts for references to the core concepts. When the user
(names concepts) in a stream, we tag it with date + video + quote. Future
factoids/subscription posts cite these tags as 'pastors' (prior work), so the
system builds on itself instead of repeating from zero.

Output: ponderables/concept_tags.json
  { concept: [ {date, video, quote, theme}, ... ] }
Also writes a simple matcher the factoid_engine can call.
"""
import os, re, glob, json

HERE = os.path.dirname(os.path.abspath(__file__))
TRANS = os.path.join(HERE, "normalized_transcripts")
OUT = os.path.join(HERE, "concept_tags.json")

# concept -> regex (case-insensitive)
CONCEPTS = {
    "penny": r"\b(penny|pennies|penny gospel|street penny)\b",
    "supercap": r"\b(super ?capacitor|supercap|capacitor|generator hybrid|grid freedom)\b",
    "versa": r"\b(versa|nissan|40 mpg|commute|10 miles per dollar)\b",
    "gaming": r"\b(@wubustreams|raid|boss fight|the stream|stream highlight)\b",
    "cuda": r"\b(cuda|gpu|kernel|inference|llm|model)\b",
    "internet": r"\b(internet|open web|scraped|absorbed|context engine)\b",
    "paulsen": r"\b(paulsen|hatchet|foster|100 books|gary paulsen)\b",
    "meme": r"\b(meme|mimetic|viral|replicate)\b",
    "colonel": r"\b(colonel|metal gear|mgs2|create context)\b",
}

def tag_all():
    tags = {c: [] for c in CONCEPTS}
    for f in sorted(glob.glob(os.path.join(TRANS, "*.txt"))):
        vid = os.path.basename(f).replace(".txt", "")
        # try to get a date from the header comment
        date = None
        with open(f, errors="ignore") as fh:
            head = fh.read(400)
            m = re.search(r"(\d{4}-\d{2}-\d{2})", head)
            if m: date = m.group(1)
        text = open(f, errors="ignore").read()
        for concept, rx in CONCEPTS.items():
            for mm in re.finditer(rx, text, re.I):
                start = max(0, mm.start() - 60)
                end = min(len(text), mm.end() + 80)
                quote = text[start:end].replace("\n", " ").strip()
                tags[concept].append({"video": vid, "date": date, "quote": quote})
    # cap per concept to keep file sane
    for c in tags:
        tags[c] = tags[c][:200]
    return tags

def main():
    tags = tag_all()
    with open(OUT, "w") as f:
        json.dump(tags, f, indent=2)
    tot = sum(len(v) for v in tags.values())
    print(f"TAGGED {tot} concept refs across {len(tags)} concepts -> concept_tags.json")
    for c, v in tags.items():
        print(f"  {c}: {len(v)}")

if __name__ == "__main__":
    main()
