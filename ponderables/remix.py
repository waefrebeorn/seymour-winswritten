#!/usr/bin/env python3
"""
Seymour Wins — REMIX / RE-THEME (New Game Plus, offline-safe)
=============================================================
Re-processes EXISTING calendar issues locally: reads the real FACT already
stored in each DD.md, re-routes it through the 1087-theme sprawl, injects the
Colonel-of-truth codec block, and rewrites the file. No network calls — the
facts are already verified and saved from the earlier fill.

This is the "remix/reduce/prestige" pass: same real facts, richer themes +
Colonel layer, applied across the whole timeline in seconds.

Run: python3 remix.py 2020
     python3 remix.py            (all years)
"""
import os, re, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme_map
from theme_router import route_theme, theme_label, colonel_frame, base_of

CAL = "calendar"

def parse_fact(path):
    t = open(path).read()
    m = re.search(r"\*\*FACT:\*\*\s*(\d{4}):\s*(.+?)(¹|$)", t, re.S)
    s = re.search(r"\*\*SOURCE:\*\*\s*(\S+)", t)
    if not m:
        return None, None, None
    year = int(m.group(1))
    fact = m.group(2).strip()
    src = s.group(1) if s else "src_retheme"
    return year, fact, src

def write_issue(path, year, fact, src):
    mm = os.path.basename(os.path.dirname(path))
    dd = os.path.basename(path).replace(".md", "")
    theme = route_theme(fact)
    label = theme_label(theme)
    colonel = colonel_frame(theme)
    yrtxt = str(year)
    angle = theme_map.angle(base_of(theme), fact, year)
    body = f"""**TITLE:** {label} — {yrtxt}
**THEME:** {theme}
**THEME_LABEL:** {label}
**FACT:** {yrtxt}: {fact}¹

{angle}

> **COLONEL (codec transmission):** {colonel}

The fossil record states it plainly above. The folklore record — what people *felt* about it — is a different document, written six weeks later in group chat, mutated by the feed.

---
¹ Verified historical anchor. Source: {src}.
"""
    with open(path, "w") as f:
        f.write(body)

def main():
    years = [sys.argv[1]] if len(sys.argv) > 1 else [
        d for d in os.listdir(CAL) if d.isdigit()]
    total = 0
    for y in years:
        files = sorted(glob.glob(f"{CAL}/{y}/*/*.md"))
        for f in files:
            year, fact, src = parse_fact(f)
            if year is None:
                continue
            write_issue(f, year, fact, src)
            total += 1
        print(f"  {y}: re-themed {len(files)} issues")
    print(f"REMIX COMPLETE: {total} issues re-themed (offline, facts preserved)")

if __name__ == "__main__":
    main()
