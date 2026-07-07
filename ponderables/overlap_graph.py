#!/usr/bin/env python3
"""
Seymour Wins — OVERLAP GRAPH BUILDER (Mathematic Sprawl)
=========================================================
Builds the cross-linked timeline graph:
  1. SAME-DATE-ACROSS-YEARS: every fact on MM/DD is linked to the same MM/DD
     in other years (the "through the years" spine). This is deterministic
     and needs no API.
  2. THEME-KEYWORD CO-OCCURRENCE: themes whose keywords appear in the same
     day's fact are linked (the sprawl mesh).
  3. OVERLAP NODES: the 276 overlap-pair themes become explicit graph edges.

Output: ponderables/overlap_index.json
  { "by_date": { "MM-DD": [list of issue paths] },
    "edges":   [ {from, to, weight, kind} ],
    "stats":   {...} }
"""
import os, re, glob, json
from collections import defaultdict, Counter

CAL = "ponderables/calendar"
THEMES = json.load(open("ponderables/themes.json"))["themes"]

def load_issues():
    out = []
    for f in glob.glob(f"{CAL}/*/*/*.md"):
        try:
            t = open(f).read()
        except Exception:
            continue
        m = re.search(r"\*\*THEME:\*\*\s*(\S+)", t)
        d = re.search(r"\*\*FACT:\*\*\s*(\d{4}):", t)
        if not m or not d:
            continue
        parts = f.split("/")
        yyyy, mm, dd = parts[-3], parts[-2], parts[-1].replace(".md", "")
        out.append({
            "path": f, "theme": m.group(1), "year": int(d.group(1)),
            "mm": mm, "dd": dd, "date": f"{mm}-{dd}", "text": t,
        })
    return out

def main():
    issues = load_issues()
    print(f"loaded {len(issues)} issues")
    # 1) same-date-across-years
    by_date = defaultdict(list)
    for it in issues:
        by_date[it["date"]].append(it["path"])
    # 2) theme keyword co-occurrence on same day
    edges = defaultdict(lambda: {"weight": 0, "kind": set()})
    theme_kw = {tid: set(th["keywords"]) for tid, th in THEMES.items()}
    for it in issues:
        # find which themes' keywords appear in this day's text
        hit = [tid for tid, kws in theme_kw.items()
               if any(k in it["text"].lower() for k in kws)]
        for i in range(len(hit)):
            for j in range(i + 1, len(hit)):
                key = tuple(sorted((hit[i], hit[j])))
                edges[key]["weight"] += 1
                edges[key]["kind"].add("keyword_cooccur")
    # 3) overlap-pair themes -> explicit edges (link back to base themes)
    for tid, th in THEMES.items():
        if "__" in tid:
            a, b = tid.split("__")
            edges[(a, b)]["weight"] += 5
            edges[(a, b)]["kind"].add("overlap_seed")
    # serialize edges
    edge_list = [
        {"from": a, "to": b, "weight": v["weight"],
         "kind": sorted(v["kind"])}
        for (a, b), v in edges.items()
    ]
    edge_list.sort(key=lambda e: -e["weight"])
    out = {
        "stats": {
            "issues": len(issues),
            "distinct_dates": len(by_date),
            "edges": len(edge_list),
            "max_same_date": max((len(v) for v in by_date.values()), default=0),
        },
        "by_date": {k: v for k, v in sorted(by_date.items())},
        "edges": edge_list[:500],  # top 500 strongest overlaps
    }
    with open("ponderables/overlap_index.json", "w") as f:
        json.dump(out, f, indent=2)
    print("OVERLAP GRAPH BUILT")
    print("  distinct dates:", out["stats"]["distinct_dates"])
    print("  edges (top500):", len(edge_list))
    print("  strongest overlap edges:")
    for e in edge_list[:8]:
        print(f"    {e['from']} ⇄ {e['to']}  w={e['weight']} {e['kind']}")

if __name__ == "__main__":
    main()
