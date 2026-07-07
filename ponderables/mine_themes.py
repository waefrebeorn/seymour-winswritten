#!/usr/bin/env python3
"""
Seymour Wins — STREAM THEME MINER (New Game Plus)
==================================================
Mines the REAL stream-transcript corpus (local, already-absorbed) to extract
the vocabulary @wubustreams actually talks about. No scraping — only the
local transcript archive. Output: topics.json (ranked stream topics with
frequency + co-occurrence), used to build the 1000-theme sprawl taxonomy.

Run: python3 mine_themes.py
"""
import os, re, glob, json, math
from collections import Counter, defaultdict

CORPORA = [
    "absorption/data/transcripts",
    "ponderables/normalized_transcripts",
]

# Strip transcript artifacts: [MM:SS] N seconds, [Music]/[Applause]/foreign tags
TS_RE = re.compile(r"\[?\d{1,2}:\d{2}\]?\s*\d*\s*(seconds?|minutes?|minute)", re.I)
TAG_RE = re.compile(r"\[(music|applause|foreign|laughter|noise|cheering|speaking)\]|\b(foreign|music|applause)\b", re.I)

STOP = set("""a an the and or but if then else for to of in on at by with from as is are was were be been being this that these those it its he she they them his her their our your my we you i not no yes do does did done have has had will would can could should may might must about into over under between out up down off so than too very just also more most much many few some any all each other own same such only here there when where why how what who whom which while because before after during without within again once every per via etc one two three get got make made use used using go going like see saw know think said tell say ask want need feel felt come came take took give gave find found look looking put set let hey man people thing things world time day days year years way ways life live really gonna yeah ok okay uh um alright right left good bad big small long short high low part end back front top bottom side call called name number bit kind sort type sorta kinda lot little able new now old first last next different only minutes timestamp hour hours second seconds music don guys well wait him play doing shit god mean applause rally battle through stop help keep ready money actually something even better trying getting cuz stream guy playing real gonna alright okay bro lol dude fuck damn hell wanna gotta aint yall things going let's im i'm you're we're they're that's it's that'll don't cant can't wont won't thank sure maybe already another pretty hit love work dead area looks saying never try around still didn didn wasn secondsthis secondsokay secondswe secondswhat secondsall secondsyou secondsoh secondsit secondsthe""".split())

def clean(text):
    text = TS_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    # drop any residual timestamp-glued tokens
    text = re.sub(r"\b(second|minute|hour|foreign|applause|music|laughter|cheering|noise|speaking)[a-z]*\b", " ", text, flags=re.I)
    text = re.sub(r"\b\d+[a-z]*\b", " ", text)  # any lone numbers
    return text

def tokens(text):
    text = clean(text)
    toks = [w for w in re.findall(r"[a-z][a-z]{2,}", text.lower())
            if w not in STOP and len(w) > 2]
    return toks

def main():
    files = []
    for d in CORPORA:
        for f in glob.glob(d + "/*"):
            if os.path.isfile(f) and f.endswith((".txt", ".json", ".md", ".vtt")):
                files.append(f)
    print(f"scanning {len(files)} transcript files...")
    tf = Counter()
    doc_freq = Counter()
    co = defaultdict(Counter)  # co-occurrence within window
    n = 0
    for f in files:
        try:
            t = open(f, errors="ignore").read()
        except Exception:
            continue
        toks = tokens(t)
        if not toks:
            continue
        n += 1
        seen = set(toks)
        for w in toks:
            tf[w] += 1
        for w in seen:
            doc_freq[w] += 1
        # co-occurrence in a 15-token sliding window
        for i in range(len(toks)):
            wi = toks[i]
            if wi in STOP:
                continue
            for j in range(i + 1, min(i + 15, len(toks))):
                wj = toks[j]
                if wj in STOP:
                    continue
                co[wi][wj] += 1
                co[wj][wi] += 1
    # TF-IDF-ish scoring: term freq * log(N/df) to surface distinctive stream vocabulary
    import math
    scored = []
    for w, c in tf.items():
        if doc_freq[w] < 3:
            continue
        idf = math.log((n + 1) / (doc_freq[w] + 1)) + 1
        scored.append((w, c, doc_freq[w], round(c * idf, 2)))
    scored.sort(key=lambda x: -x[3])
    top = scored[:400]
    # build co-occurrence edges for top terms
    edges = {}
    for w, c, df, sc in top:
        partners = co[w].most_common(12)
        edges[w] = [p for p, cnt in partners if cnt >= 3 and p in set(t for t, *_ in top)]
    out = {
        "docs": n,
        "total_tokens": sum(tf.values()),
        "topics": [
            {"term": w, "tf": c, "df": df, "score": sc, "related": edges.get(w, [])}
            for w, c, df, sc in top
        ],
    }
    with open("ponderables/topics.json", "w") as f:
        json.dump(out, f, indent=2)
    print(f"mined {len(top)} distinctive stream topics from {n} docs.")
    print("top 30:", ", ".join(t["term"] for t in out["topics"][:30]))

if __name__ == "__main__":
    main()
