#!/usr/bin/env python3
"""
Seymour Wins — DAILY ISSUE BUILDER (alpha-faithful)
====================================================
Rebuild of Seymour Wins on the ORIGINAL alpha foundation
(build_pdf.py / build_issue1_pdf.py): clean HTML + Chromium
print-to-PDF, real typography, framed clipart, footnotes.

The old magazine_engine*.py shredded each daily entry (DD.md) into a
30-page calendar collage with 90% empty editorial pages. This engine
instead feeds the REAL written entry whole, formatted like a toilet-book
page: cover + entry (title, verified FACT callout, body prose, Colonel
codec pull-quote, triple-checked note) + footnotes. No jumble.

Usage:
  python3 build_seymour_wins.py 2026 07 08      # one daily issue
  python3 build_seymour_wins.py 2026 07 --month  # whole month volume
  python3 build_seymour_wins.py                   # latest available day
"""
import os, re, html, subprocess, base64, glob, sys, datetime, argparse

ROOT = "/home/wubu/seymour-project"
PON = f"{ROOT}/ponderables"
DRAFTS = PON  # not used; we read calendar entries
CAL = f"{PON}/calendar"
ASSETS = f"{ROOT}/assets"
FONTS = f"{ASSETS}/fonts"
CLIP = f"{ASSETS}/clipart"
OUT = f"{PON}/pdf/seymour_wins"
os.makedirs(OUT, exist_ok=True)

import theme_map
from theme_map import pick_svg

# ── theme accent color (matches magazine_engine_v3 THEME_COLOR) ──
THEME_COLOR = {
    "penny": "#a8741a", "supercap": "#2e7d6b", "versa": "#3a6ea5",
    "gaming": "#7a3aa0", "cuda": "#2f6f3f", "internet": "#b5482e",
    "paulsen": "#6b5b2e", "meme": "#444444", "book": "#6b5b2e",
    "brain": "#5a4a8a", "colonel": "#8a1a1a", "metalgear": "#3a4a3a",
    "key": "#7a5a1a", "sky": "#3a7a9a", "flag": "#9a2e2e", "gun": "#555555",
}

def svg_to_datauri(path):
    if not path:
        return ""
    with open(path) as f:
        s = f.read().strip()
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode()).decode()

# ── parse a calendar daily entry (DD.md) ──
def parse_dd(path):
    raw = open(path, errors="ignore").read()
    title, theme, theme_label, fact = "", "meme", "", ""
    body, colonel, verify, footnotes = [], [], [], []
    in_foot = False
    for ln in raw.splitlines():
        s = ln.strip()
        if s == "---":
            in_foot = True
            continue
        if in_foot:
            if s:
                footnotes.append(s)
            continue
        m = re.match(r"\*\*TITLE:\*\*\s*(.+)", ln)
        if m: title = m.group(1).strip(); continue
        m = re.match(r"\*\*THEME:\*\*\s*(\S+)", ln)
        if m: theme = m.group(1).strip().lower(); continue
        m = re.match(r"\*\*THEME_LABEL:\*\*\s*(.+)", ln)
        if m: theme_label = m.group(1).strip(); continue
        m = re.match(r"\*\*FACT:\*\*\s*(.+)", ln)
        if m: fact = m.group(1).strip(); continue
        if ln.startswith(">"):
            inner = re.sub(r"^>\s*", "", ln)
            im = re.match(r"\*\*(COLONEL[^:]*):\*\*\s*(.*)", inner)
            if im:
                colonel.append(im.group(2).strip())
                continue
            vm = re.match(r"\*\*(TRIPLE-CHECKED[^:]*):\*\*\s*(.*)", inner)
            if vm:
                verify.append(vm.group(2).strip())
                continue
            if inner:
                colonel.append(inner.strip())
            continue
        if not s:
            continue
        body.append(s)
    return dict(title=title, theme=theme, theme_label=theme_label,
                fact=fact, body=body, colonel=colonel, verify=verify,
                footnotes=footnotes)

def md_inline(s):
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<!\*)\*(?!\*)(.+?)\*(?!\*)", r"<i>\1</i>", s)
    s = s.replace("~", "about")
    return s

def render_body(block):
    """block = list of paragraph strings. Returns HTML."""
    out = []
    for para in block:
        p = para.strip()
        if not p:
            continue
        out.append(f"<p>{md_inline(p)}</p>")
    return "\n".join(out)

def font_face_css():
    css = ""
    mapping = {
        "Special Elite": "SpecialElite-Regular.ttf",
        "Old Standard TT": "OldStandardTT-Regular.ttf",
        "Rye": "Rye-Regular.ttf",
        "Bungee": "Bungee-Regular.ttf",
        "DM Serif Display": "DMSerifDisplay-Regular.ttf",
    }
    for fam, fn in mapping.items():
        p = f"{FONTS}/{fn}"
        if os.path.exists(p):
            b64 = base64.b64encode(open(p, "rb").read()).decode()
            css += (f"@font-face {{ font-family: '{fam}'; "
                     f"src: url(data:font/truetype;base64,{b64}) format('truetype'); "
                     f"font-weight: normal; font-style: normal; }}\n")
    return css

CSS = """
@page { size: 4.5in 7.125in; margin: 0.125in; }
* { box-sizing: border-box; }
body { font-family: 'Old Standard TT', Georgia, serif; color:#222; margin:0;
  background-color:#f7f1e1;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(180,160,120,0.10) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(150,130,90,0.12) 0%, transparent 45%),
    repeating-linear-gradient(0deg, rgba(120,100,70,0.025) 0px, rgba(120,100,70,0.025) 1px, transparent 1px, transparent 3px);
}
.entry { padding:9px 11px; page-break-inside: avoid; }
.clipwrap { text-align:center; margin:2px 0 6px; }
.clip { max-width:84px; max-height:84px; opacity:0.95;
  border:1px solid #c9bfa3; border-radius:6px; padding:5px; background:#fbf7ec;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
.caption { font-family:'Special Elite',monospace; font-size:6.5pt; color:#776; letter-spacing:1px; text-transform:uppercase; margin:1px 0 0; font-variant-numeric: lining-nums tabular-nums; font-feature-settings:"lnum" 1,"tnum" 1; }
h2 { font-family:'Special Elite','Courier New', monospace; font-size:12.5pt; line-height:1.1; color:#1a1a1a; margin:3px 0 6px; }
p { font-size:9pt; line-height:1.38; margin:0 0 6px; text-align:justify; }
b { font-weight:700; }
.fact { font-family:'Special Elite','Courier New', monospace; font-size:8pt; background:#efe7d2; border:1px solid #d8cda8; border-left:3px solid #a8741a; padding:6px 8px; margin:7px 0; border-radius:3px; line-height:1.4; }
.fact b { color:#7a5a12; }
.colonel { font-family:'Special Elite',monospace; font-size:8.5pt; background:#1c1c1c; color:#f3ecd8; padding:9px 11px; margin:9px 0; border-radius:3px; line-height:1.45; }
.colonel b { color:#f3d27a; }
.verify { font-family:'Special Elite',monospace; font-size:7pt; color:#5a6b4a; border-top:1px dashed #b9c2a8; padding-top:4px; margin:6px 0; line-height:1.4; }
.verify b { color:#3a5a2a; }
.footrule { border:0; border-top:1px solid #ccc; margin:7px 0 5px; }
.footnotes { font-size:7pt; color:#555; line-height:1.4; }
.footnotes sup { color:#a8741a; font-weight:700; margin-right:3px; }
.pagebreak { page-break-after: always; }
.cover { height:6.875in; display:flex; align-items:center; justify-content:center; background:#1c1c1c; color:#f3ecd8; text-align:center; }
.coverwash { position:absolute; inset:0; background:
    radial-gradient(circle at 30% 20%, rgba(243,210,122,0.10), transparent 50%),
    radial-gradient(circle at 70% 80%, rgba(243,210,122,0.08), transparent 55%),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 4px);
  opacity:0.5; }
.covertitle { position:relative; z-index:2; padding:0 10px; }
.kicker { font-family:'Special Elite',monospace; letter-spacing:2px; font-size:11pt; margin:0; }
h1 { font-family:'Rye', serif; font-size:34pt; margin:8px 0; color:#f3d27a; line-height:1.0; }
.vol { font-family:'Special Elite',monospace; letter-spacing:4px; font-size:12pt; margin:0; }
.sub { font-family:'Old Standard TT', Georgia, serif; font-style:italic; font-size:10.5pt; margin:14px 0 0; line-height:1.3; max-width:90%; }
.byline { font-family:'Special Elite',monospace; font-size:9pt; color:#bbb; margin-top:10px; }
.price { font-family:'Special Elite',monospace; text-align:center; margin-top:18px; font-size:10pt; }
"""

def build_entry_html(d, rotation):
    accent = THEME_COLOR.get(d["theme"], "#444444")
    svg = pick_svg(d["theme"], rotation_index=rotation)
    img = ""
    if svg:
        uri = svg_to_datauri(svg)
        cap = d["theme_label"] or d["theme"]
        img = (f'<div class="clipwrap"><img class="clip" src="{uri}" alt="{d["theme"]}">'
                f'<p class="caption">{cap} &middot; CC0 clipart &middot; Openclipart</p></div>')
    title = d["title"] or "Untitled"
    parts = [f'<section class="entry">{img}<h2>{html.escape(title)}</h2>']
    if d["fact"]:
        parts.append(f'<div class="fact"><b>VERIFIED ANCHOR &mdash; </b>{md_inline(d["fact"])}</div>')
    if d["body"]:
        parts.append(render_body(d["body"]))
    for c in d["colonel"]:
        if c:
            parts.append(f'<div class="colonel"><b>COLONEL (codec transmission):</b> {md_inline(c)}</div>')
    for v in d["verify"]:
        if v:
            parts.append(f'<div class="verify"><b>TRIPLE-CHECKED:</b> {md_inline(v)}</div>')
    if d["footnotes"]:
        parts.append('<hr class="footrule">')
        for fn in d["footnotes"]:
            fn_h = re.sub(r"([¹²³⁴⁵⁶⁷⁸⁹⁰])", r"<sup>\1</sup>", fn)
            parts.append(f'<p class="footnotes">{fn_h}</p>')
    parts.append('</section><div class="pagebreak"></div>')
    return "\n".join(parts)

def build_cover_html(d, issue_label):
    label = d["theme_label"] or d["theme"]
    sub = d["title"] or ""
    return f"""
<section class="cover">
  <div class="coverwash"></div>
  <div class="covertitle">
    <p class="kicker">SEYMOUR WINS</p>
    <h1>{html.escape(issue_label)}</h1>
    <p class="vol">{html.escape(label.upper())}</p>
    <p class="sub">{html.escape(sub)}</p>
    <p class="byline">a daily toilet-book entry, by wubu &middot; TDA-audited</p>
  </div>
</section>
<div class="pagebreak"></div>
"""

def build_pdf(year, month, day, css):
    dd = os.path.join(CAL, str(year), f"{month:02d}", f"{day:02d}.md")
    if not os.path.exists(dd):
        return None
    d = parse_dd(dd)
    issue_label = f"{month:02d}-{day:02d}"
    cover = build_cover_html(d, issue_label)
    entry = build_entry_html(d, rotation=day)
    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>{cover}{entry}</body></html>")
    return full, issue_label

def main():
    ap = argparse.ArgumentParser(description="Seymour Wins daily issue builder (alpha-faithful)")
    ap.add_argument("year", nargs="?", type=int)
    ap.add_argument("month", nargs="?", type=int)
    ap.add_argument("day", nargs="?", type=int)
    ap.add_argument("--volume", action="store_true", help="build whole-month volume")
    a = ap.parse_args()
    css = font_face_css() + CSS

    chrome = shutil_which()
    if not chrome:
        print("ERROR: chromium not found"); sys.exit(1)

    # resolve target days
    targets = []
    if a.year and a.month and a.day:
        targets = [(a.year, a.month, a.day)]
    elif a.year and a.month:
        # month volume
        y, m = a.year, a.month
        for dd in range(1, 32):
            try: datetime.date(y, m, dd)
            except ValueError: continue
            p = os.path.join(CAL, str(y), f"{m:02d}", f"{dd:02d}.md")
            if os.path.exists(p):
                targets.append((y, m, dd))
    else:
        # latest available day
        found = None
        for y in range(2026, 2019, -1):
            for m in range(12, 0, -1):
                p = os.path.join(CAL, str(y), f"{m:02d}")
                if not os.path.isdir(p):
                    continue
                days = sorted(int(os.path.basename(f)[:-3])
                             for f in os.listdir(p) if f.endswith(".md") and f[:2].isdigit())
                if days:
                    found = (y, m, days[-1]); break
            if found:
                break
        if found:
            targets = [found]

    if not targets:
        print("No calendar entries found."); sys.exit(1)

    # build combined HTML
    sections = []
    label_parts = []
    for (y, m, dd) in targets:
        res = build_pdf(y, m, dd, css)
        if not res:
            continue
        html_doc, label = res
        # extract body between <body> and </body>
        body = html_doc.split("<body>",1)[1].rsplit("</body>",1)[0]
        sections.append(body)
        label_parts.append(label)

    if not sections:
        print("Nothing built."); sys.exit(1)

    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>"
            + "\n".join(sections) + "</body></html>")

    # filename
    if len(targets) == 1:
        y, m, dd = targets[0]
        fname = f"seymour_wins_{y}_{m:02d}-{dd:02d}.pdf"
    else:
        y, m = targets[0][0], targets[0][1]
        fname = f"seymour_wins_{y}_{m:02d}_month.pdf"
    out_path = os.path.join(OUT, fname)
    html_path = out_path.rsplit(".",1)[0] + ".html"
    with open(html_path, "w") as f:
        f.write(full)
    cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu",
           "--no-pdf-header-footer", f"--print-to-pdf={out_path}",
           "file://" + html_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-2000:]); sys.exit(1)
    print(f"PDF written: {out_path} ({os.path.getsize(out_path)} bytes)")

def shutil_which():
    for c in ("chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        import shutil
        p = shutil.which(c)
        if p:
            return p
    return None

if __name__ == "__main__":
    main()
