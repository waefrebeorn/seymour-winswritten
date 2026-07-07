#!/usr/bin/env python3
"""
Seymour Wins — ISSUE ONE (The Penny Motif)
Standalone toilet-book PDF: cover + entry + TDA verdict appendix.
Fixed layout: fits page, readable footnotes, framed+captioned clipart.
"""
import os, re, html, subprocess, base64, shutil

ROOT = "/home/wubu/seymour-project"
DRAFTS = f"{ROOT}/ponderables/drafts"
ASSETS = f"{ROOT}/assets"
CLIP = f"{ASSETS}/clipart"
FONTS = f"{ASSETS}/fonts"
OUT = f"{ROOT}/ponderables/pdf"
os.makedirs(OUT, exist_ok=True)

ENTRY_FILE = "bathroom_pennies.md"
THEME = "penny"

def read_md(name):
    with open(f"{DRAFTS}/{name}") as f:
        return f.read()

import theme_map
from theme_map import pick_svg


def svg_to_datauri(path):
    if not path:
        return ""
    with open(path) as f:
        s = f.read().strip()
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode()).decode()

def parse_draft(text):
    body = []
    title = ""
    for ln in text.splitlines():
        m = re.match(r'\*\*\s*TITLE:\s*(.+?)\s*\*\*', ln) or re.match(r'\*\*TITLE:\s*(.+?)\*\*', ln)
        if m:
            title = m.group(1).strip()
            continue
        body.append(ln)
    return title, "\n".join(body).strip()

def render_body(body):
    out, lines, i = [], body.splitlines(), 0
    in_box, box = False, []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            if in_box:
                clean = re.sub(r'[┌┐└┘├┤┬┴┼─│]', '', "\n".join(box))
                clean = clean.replace("BONUS FACT:", "<b>BONUS FACT:</b>")
                out.append(f'<div class="bonus">{clean.strip()}</div>')
                box, in_box = [], False
            else:
                in_box = True
            i += 1; continue
        if in_box:
            box.append(ln); i += 1; continue
        if ln.strip() == "---":
            out.append('<hr class="footrule">'); i += 1; continue
        if re.search(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]\s', ln) or re.match(r'^[¹²³⁴⁵⁶⁷⁸⁹⁰]', ln):
            fn = ln
            for idx, sup in enumerate("¹²³⁴⁵⁶⁷⁸⁹⁰"):
                fn = fn.replace(sup, f"<sup>{idx+1}</sup>")
            out.append(f'<p class="footnotes">{fn}</p>'); i += 1; continue
        p = ln.strip()
        if not p:
            i += 1; continue
        p = html.escape(p).replace("~", "about")
        p = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', p)
        p = re.sub(r'\*(.+?)\*', r'<i>\1</i>', p)
        out.append(f'<p>{p}</p>'); i += 1
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
            css += f"""@font-face {{ font-family: '{fam}'; src: url(data:font/truetype;base64,{b64}) format('truetype'); font-weight: normal; font-style: normal; }}\n"""
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
.entry { padding: 9px 11px; page-break-inside: avoid; }
.clipwrap { text-align:center; margin: 2px 0 6px; }
.clip { max-width: 72px; max-height: 72px; opacity:0.95;
  border:1px solid #c9bfa3; border-radius:6px; padding:5px; background:#fbf7ec;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
.caption { font-family:'Special Elite',monospace; font-size:6.5pt; color:#776; letter-spacing:1px; text-transform:uppercase; margin:1px 0 0; font-variant-numeric: lining-nums tabular-nums; font-feature-settings:"lnum" 1,"tnum" 1; }
h2 { font-family:'Special Elite','Courier New', monospace; font-size: 12.5pt; line-height:1.1; color:#1a1a1a; margin: 3px 0 6px; }
p { font-size: 9pt; line-height: 1.38; margin: 0 0 6px; text-align: justify; }
b { font-weight:700; }
.bonus { font-family:'Special Elite','Courier New', monospace; font-size:8pt; background:#f4efe2; border:1px solid #d8cda8; padding:6px 8px; margin:7px 0; border-radius:3px; line-height:1.4; }
.footrule { border:0; border-top:1px solid #ccc; margin:7px 0 5px; }
.footnotes { font-size:7pt; color:#555; line-height:1.4; }
.footnotes sup { color:#a8741a; font-weight:700; margin-right:3px; }
.pagebreak { page-break-after: always; }
.verdict { font-family:'Special Elite',monospace; font-size:9.5pt; background:#efe9d8; border-left:3px solid #c9a23a; padding:9px 11px; margin:12px 0; }
.verdict b { color:#7a5a12; }
.cover { height: 6.875in; display:flex; align-items:center; justify-content:center; background:#1c1c1c; color:#f3ecd8; text-align:center; }
.coverwash { position:absolute; inset:0; background:
    radial-gradient(circle at 30% 20%, rgba(243,210,122,0.10), transparent 50%),
    radial-gradient(circle at 70% 80%, rgba(243,210,122,0.08), transparent 55%),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 4px);
  opacity:0.5; }
.covertitle { position:relative; z-index:2; padding:0 10px; }
.kicker { font-family:'Special Elite',monospace; letter-spacing:2px; font-size:11pt; margin:0; }
h1 { font-family:'Rye', serif; font-size:36pt; margin:8px 0; color:#f3d27a; line-height:1.0; }
.vol { font-family:'Special Elite',monospace; letter-spacing:4px; font-size:12pt; margin:0; }
.sub { font-family:'Old Standard TT', Georgia, serif; font-style:italic; font-size:11pt; margin:14px 0 0; line-height:1.3; }
.byline { font-family:'Special Elite',monospace; font-size:9pt; color:#bbb; margin-top:8px; }
.price { font-family:'Special Elite',monospace; text-align:center; margin-top:18px; font-size:10pt; }
"""

def build_html():
    css = font_face_css() + CSS
    text = read_md(ENTRY_FILE)
    title, body = parse_draft(text)
    svg = pick_svg(THEME)
    img = ""
    if svg:
        uri = svg_to_datauri(svg)
        img = (f'<div class="clipwrap"><img class="clip" src="{uri}" alt="{THEME}">'
               f'<p class="caption">CC0 clipart &middot; Openclipart</p></div>')
    rendered = render_body(body)

    cover = f"""
<section class="cover">
  <div class="coverwash"></div>
  <div class="covertitle">
    <p class="kicker">SEYMOUR WINS</p>
    <h1>ISSUE ONE</h1>
    <p class="vol">THE PENNY MOTIF</p>
    <p class="sub">Loose change, three generations, one copper thread</p>
    <p class="byline">a toilet book entry, by wubu &middot; TDA-audited</p>
  </div>
</section>
<div class="pagebreak"></div>
"""
    entry = f"""
<section class="entry">
  {img}
  <h2>{html.escape(title)}</h2>
  {rendered}
</section>
<div class="pagebreak"></div>
"""
    verdict = f"""
<section class="entry">
  <h2>Triple Devil's Advocate &mdash; Verdict (Issue One)</h2>
  <p><b>PASS 1 &mdash; is the fact real?</b> Penny cost (about 3&cent;), US Mint loss (about $85M/yr), Canada 2012 &mdash; all hold. The &ldquo;heads-up = good luck&rdquo; rule is flagged as <i>family lore</i>, not universal fact. &#10003;</p>
  <p><b>PASS 2 &mdash; does the structure hold?</b> The 5-persona taxonomy (Colonel / Clipart / Devil / Philosopher / Engineer) is the series spine &mdash; showing the <i>method</i>, not just the result. Holds. &#10003;</p>
  <p><b>PASS 3 &mdash; what's the trap?</b> Self-aware to the point of pre-empting critique. Keep the confession (it's the voice) but don't let it defang the analysis. &#9888;</p>
  <p class="verdict">&#128993; PUBLISH WITH FIXES &mdash; soften 2.7&cent;&rarr;about 3&cent; (done) and verify the &ldquo;Taco Bell&rdquo; transcript color.</p>
  <hr class="footrule">
  <p class="price">SEYMOUR WINS &middot; ISSUE ONE &middot; wubu</p>
</section>
"""
    full = f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head><body>
{cover}
{entry}
{verdict}
</body></html>"""
    return full

def main():
    html_doc = build_html()
    html_path = f"{OUT}/issue1_penny.html"
    with open(html_path, "w") as f:
        f.write(html_doc)
    chrome = shutil.which("chromium") or shutil.which("chromium-browser")
    pdf_path = f"{OUT}/seymour_wins_issue_one_penny.pdf"
    cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu",
           "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", "file://" + html_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-2000:]); return 1
    print(f"PDF written: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")
    print("HTML intermediate:", html_path)

if __name__ == "__main__":
    main()

