#!/usr/bin/env python3
"""
Seymour Wins -- ISSUE BUILDER (alpha-faithful, real-content)
============================================================
Generalizes the proven alpha pipeline (build_pdf.py) onto the REAL
Seymour Wins essay drafts (drafts/seymour_wins_*.md). No calendar
test data, no AI filler sections. Cover + real entries + Colonel
codec callouts + colophon. Pocket toilet-book trim.

Usage:
  uv run --with pymupdf --with cairosvg python3 build_seymour_wins_v2.py \
        --issues 1 2 3 4 5 \
        --out pdf/seymour_wins/issue01.pdf
"""
import os, re, html, subprocess, base64, shutil, argparse, glob

ROOT = "/home/wubu/seymour-project"
DRAFTS = f"{ROOT}/ponderables/drafts"
ASSETS = f"{ROOT}/assets"
CLIP = f"{ASSETS}/clipart"
FONTS = f"{ASSETS}/fonts"
OUT = f"{ROOT}/ponderables/pdf/seymour_wins"
os.makedirs(OUT, exist_ok=True)

import theme_map
from theme_map import pick_svg

# ── Real essays -> theme (drives clipart) ──
ESSAYS = {
    1:  ("seymour_wins_01_religion_god.md",  "brain"),
    2:  ("seymour_wins_02_job_work.md",      "internet"),
    3:  ("seymour_wins_03_food_eating.md",   "meme"),
    4:  ("seymour_wins_04_car_commute.md",   "versa"),
    5:  ("seymour_wins_05_health.md",        "book"),
    6:  ("seymour_wins_06_book_reading.md",  "paulsen"),
    7:  ("seymour_wins_07_internet_culture.md","internet"),
    8:  ("seymour_wins_08_dog_pet.md",       "meme"),
    9:  ("seymour_wins_09_postal_mail.md",   "penny"),
    10: ("seymour_wins_10_mom_story.md",     "penny"),
}

COLONEL_QUOTES = [
    "Create context, not control content.",
    "Information is not the issue. The issue is the codec.",
    "We are formless. We are legion. We are the Patriots of our own inbox.",
    "The way you laugh at a thing is the way you survive it.",
    "A man who argues with the ceiling at 2 AM is still arguing. That counts.",
    "Memory is the only public domain nobody patented.",
    "You do not need to win the argument. You need to keep the thread.",
]

def read_md(name):
    with open(f"{DRAFTS}/{name}") as f:
        return f.read()

def svg_to_datauri(path):
    if not path:
        return ""
    with open(path) as f:
        s = f.read().strip()
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode()).decode()

def parse_draft(text):
    body, title = [], ""
    for ln in text.splitlines():
        m = re.match(r"\*\*TITLE:\s*(.+?)\*\*", ln) or re.match(r"\*\*TITLE:\s*(.+?)\*\*", ln)
        if m:
            title = m.group(1).strip()
            continue
        body.append(ln)
    return title, "\n".join(body).strip()

def render_body(body):
    """Identical to alpha build_pdf.py render_body."""
    out, lines, i = [], body.splitlines(), 0
    in_box, box = False, []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            if in_box:
                clean = re.sub(r"[┌┐└┘├┤┬┴┼─│]", "", "\n".join(box))
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
        if re.match(r"^[¹²³⁴⁵⁶⁷⁸⁹⁰\s]", ln) or re.search(r"[¹²³⁴⁵⁶⁷⁸⁹⁰]\s", ln):
            fn = ln.replace("¹","<sup>1</sup>").replace("²","<sup>2</sup>").replace("³","<sup>3</sup>").replace("⁴","<sup>4</sup>")
            out.append(f'<p class="footnotes">{fn}</p>'); i += 1; continue
        # blockquote (>) -> Colonel/stream pull
        if ln.strip().startswith(">"):
            q = html.escape(ln.strip().lstrip("> ").strip())
            out.append(f'<blockquote>{q}</blockquote>'); i += 1; continue
        p = ln.strip()
        if not p:
            i += 1; continue
        p = html.escape(p).replace("~", "about")
        p = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", p)
        p = re.sub(r"\*(.+?)\*", r"<i>\1</i>", p)
        out.append(f"<p>{p}</p>")
        i += 1
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
            css += f"""@font-face {{
  font-family: '{fam}';
  src: url(data:font/truetype;base64,{b64}) format('truetype');
  font-weight: normal; font-style: normal;
}}
"""
    return css

def build_html(issue_nums, cover_title, cover_sub):
    css = font_face_css()
    paper_bg = """
  background-color:#f7f1e1;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(180,160,120,0.10) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(150,130,90,0.12) 0%, transparent 45%),
    repeating-linear-gradient(0deg, rgba(120,100,70,0.025) 0px, rgba(120,100,70,0.025) 1px, transparent 1px, transparent 3px);
"""
    sections = []
    cq = 0
    for n in issue_nums:
        fname, theme = ESSAYS.get(n, (None, None))
        if not fname or not os.path.exists(f"{DRAFTS}/{fname}"):
            continue
        text = read_md(fname)
        title, body = parse_draft(text)
        svg = pick_svg(theme)
        img = ""
        if svg:
            uri = svg_to_datauri(svg)
            img = f'<img class="clip" src="{uri}" alt="{theme}"><p class="caption">CC0 clipart &middot; Openclipart</p>'
        rendered = render_body(body)
        colonel = COLONEL_QUOTES[cq % len(COLONEL_QUOTES)]
        cq += 1
        sections.append(f"""
<section class="entry">
  <div class="clipwrap">{img}</div>
  <h2>{html.escape(title)}</h2>
  {rendered}
  <div class="colonel"><span class="codec">COLONEL (codec)</span> &mdash; {html.escape(colonel)}</div>
</section>
<div class="pagebreak"></div>
""")
    cover = f"""
<section class="cover">
  <div class="coverwash"></div>
  <div class="covertitle">
    <p class="kicker">SEYMOUR WINS</p>
    <h1>ISSUE {roman(issue_nums[0]) if issue_nums else 'ONE'}</h1>
    <p class="vol">A Man, Indexed</p>
    <p class="sub">{html.escape(cover_sub)}</p>
    <p class="byline">a toilet book, by wubu</p>
  </div>
</section>
<div class="pagebreak"></div>
"""
    colophon = f"""
<section class="colophon">
  <h2>About This Book</h2>
  <p>Every clipart image in this book is <b>CC0</b> (public-domain-equivalent), sourced from Openclipart. Every typeface is <b>OFL</b> (SIL Open Font License) &mdash; Special Elite, Old Standard TT, Rye, Bungee, DM Serif Display.</p>
  <p>The words are the author's own &mdash; pulled verbatim from the @WuBuStreams archive and the Seymour absorption corpus. No commercial clip-art libraries were harmed, pirated, or borrowed.</p>
  <p class="price">$4.99 &middot; Print-on-demand &middot; wubu</p>
</section>
"""
    full = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{css}
@page {{
  size: 4.5in 7.125in;
  margin: 0.125in;
}}
* {{ box-sizing: border-box; }}
body {{ font-family: 'Old Standard TT', Georgia, serif; color:#222; {paper_bg} margin:0; }}
.entry {{ padding: 9px 11px; page-break-inside: avoid; }}
.clipwrap {{ text-align:center; margin: 2px 0 6px; }}
.clip {{ max-width: 72px; max-height: 72px; opacity:0.95;
  border:1px solid #c9bfa3; border-radius:6px; padding:5px; background:#fbf7ec;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12); }}
.caption {{ font-family:'Special Elite',monospace; font-size:6.5pt; color:#776; letter-spacing:1px; text-transform:uppercase; margin:1px 0 0; }}
h2 {{ font-family:'Special Elite','Courier New', monospace; font-size: 12.5pt; line-height:1.1; color:#1a1a1a; margin: 3px 0 6px; }}
p {{ font-size: 9pt; line-height: 1.38; margin: 0 0 6px; text-align: justify; }}
b {{ font-weight:700; }}
blockquote {{ font-family:'Special Elite',monospace; font-size:8.5pt; font-style:italic; border-left:3px solid #a8741a; padding:3px 0 3px 8px; margin:7px 0; color:#3a2f1a; background:#f4efe2; }}
.bonus {{ font-family:'Special Elite','Courier New', monospace; font-size:8pt; background:#f4efe2; border:1px solid #d8cda8; padding:6px 8px; margin:7px 0; border-radius:3px; line-height:1.4; }}
.colonel {{ font-family:'Special Elite',monospace; font-size:7.5pt; border:1px dashed #8a7a5a; background:#efe7d2; padding:5px 7px; margin:8px 0 0; border-radius:3px; color:#3a2f1a; }}
.colonel .codec {{ font-weight:700; color:#7a5a1a; letter-spacing:1px; }}
.footrule {{ border:0; border-top:1px solid #ccc; margin:7px 0 5px; }}
.footnotes {{ font-size:7pt; color:#555; line-height:1.4; }}
.footnotes sup {{ color:#a8741a; font-weight:700; margin-right:3px; }}
.pagebreak {{ page-break-after: always; }}
.cover {{ height: 6.875in; position:relative; display:flex; align-items:center; justify-content:center; background:#1c1c1c; color:#f3ecd8; text-align:center; }}
.coverwash {{ position:absolute; inset:0; background:
    radial-gradient(circle at 30% 20%, rgba(243,210,122,0.10), transparent 50%),
    radial-gradient(circle at 70% 80%, rgba(243,210,122,0.08), transparent 55%),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 4px);
  opacity:0.5; }}
.covertitle {{ position:relative; z-index:2; max-width:100%; padding:0 8px; box-sizing:border-box; text-align:center; }}
.kicker {{ font-family:'Special Elite',monospace; letter-spacing:2px; font-size:10pt; margin:0; }}
h1 {{ font-family:'Rye', serif; font-size:38pt; margin:6px 0; color:#f3d27a; line-height:1.0; }}
.vol {{ font-family:'Special Elite',monospace; letter-spacing:4px; font-size:11pt; margin:0; }}
.sub {{ font-family:'Old Standard TT', Georgia, serif; font-style:italic; font-size:11pt; margin:12px 0 0; line-height:1.3; text-align:center; }}
.byline {{ font-family:'Special Elite',monospace; font-size:9pt; color:#bbb; }}
.colophon {{ padding:20px 14px; }}
.colophon h2 {{ font-family:'Rye',serif; color:#1a1a1a; }}
.price {{ font-family:'Special Elite',monospace; text-align:center; margin-top:30px; font-size:11pt; }}
</style></head><body>
{cover}
{''.join(sections)}
{colophon}
</body></html>"""
    return full

def roman(n):
    r = {1:"ONE",2:"TWO",3:"THREE",4:"FOUR",5:"FIVE",6:"SIX",7:"SEVEN",8:"EIGHT",9:"NINE",10:"TEN"}
    return r.get(n, str(n))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", nargs="+", type=int, default=[1,2,3,4,5],
                    help="essay numbers to include (1-10)")
    ap.add_argument("--out", default=f"{OUT}/issue_sample.pdf")
    ap.add_argument("--sub", default="A Taxonomy of a Man Thinking Out Loud")
    args = ap.parse_args()
    html_doc = build_html(args.issues, "SEYMOUR WINS", args.sub)
    html_path = os.path.abspath(args.out.rsplit(".",1)[0] + ".html")
    with open(html_path, "w") as f:
        f.write(html_doc)
    chrome = shutil.which("chromium") or shutil.which("chromium-browser")
    out_abs = os.path.abspath(args.out)
    cmd = [chrome, "--headless", "--no-sandbox", "--disable-gpu",
           "--no-pdf-header-footer", f"--print-to-pdf={out_abs}", "file://" + html_path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-2000:]); return 1
    print(f"PDF written: {args.out} ({os.path.getsize(args.out)} bytes)")

if __name__ == "__main__":
    main()
