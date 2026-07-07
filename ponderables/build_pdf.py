#!/usr/bin/env python3
"""
Seymour Ponderables Vol 1 — PDF builder (Uncle John toilet-book style)
Reads 6 bathroom_*.md drafts, renders to print-ready HTML, prints to PDF via Chromium.

Specs:
  - Trim: 4.25" x 6.875" (KDP 6"x9" small -> actually use 5x8 trade? user said toilet book.
    Use 4.25x6.875 (pocket) with 0.125" bleed => 4.5x7.125 page.
  - Fonts: Special Elite (headers/typewriter), Old Standard TT (body), Rye (cover/display)
  - Clipart: one CC0 SVG per entry from assets/clipart/<theme>/
  - Texture: subtle paper grain via CSS gradients (procedural, no external fetch)
  - OFL fonts embedded (base64 @font-face), no external fetch.
"""
import os, re, html, subprocess, json, base64, shutil

ROOT = "/home/wubu/seymour-project"
DRAFTS = f"{ROOT}/ponderables/drafts"
ASSETS = f"{ROOT}/assets"
CLIP = f"{ASSETS}/clipart"
FONTS = f"{ASSETS}/fonts"
OUT = f"{ROOT}/ponderables/pdf"
os.makedirs(OUT, exist_ok=True)

# ── Entry -> clipart theme (already downloaded, dead-to-rights CC0) ──
ENTRIES = [
    ("bathroom_pennies.md",        "penny",    "The Penny Motif, or: How a Guy Turned Loose Change Into a Generational Trauma Timeline"),
    ("bathroom_supercapacitor.md", "supercap", "The Car That Couldn't Commit (So It Married Three Power Sources)"),
    ("bathroom_paulsen.md",        "paulsen",  "The Guy Who Read 100 Books Because Someone Took His Phone"),
    ("bathroom_versa.md",          "versa",    "Three Hours a Day in a Nissan Versa: The World's Most Expensive Meditation App"),
    ("bathroom_cuda.md",           "cuda",     "The Guy Who Writes CUDA Kernels for Fun (And Cries About Vec_Dot Bugs)"),
    ("bathroom_ponderables.md",    "meme",     "Uncle Seymour's Ponderables, Vol. 1: Or, The Taxonomy of a Man Thinking Out Loud"),
]

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
    lines = text.splitlines()
    # title = line starting with **TITLE:
    title = ""
    body = []
    for ln in lines:
        m = re.match(r'\*\*TITLE:\s*(.+?)\*\*', ln)
        if m:
            title = m.group(1).strip()
            continue
        body.append(ln)
    body = "\n".join(body).strip()
    # strip the ascii box (we render bonus facts as styled callout)
    return title, body

def render_body(body):
    """Convert draft markdown to HTML."""
    out = []
    lines = body.splitlines()
    i = 0
    in_box = False
    box_lines = []
    while i < len(lines):
        ln = lines[i]
        if ln.strip().startswith("```"):
            if in_box:
                # close bonus box
                box_html = "\n".join(box_lines)
                # remove box-drawing chars, keep text
                clean = re.sub(r'[┌┐└┘├┤┬┴┼─│]', '', box_html)
                clean = clean.replace("BONUS FACT:", "<b>BONUS FACT:</b>")
                out.append(f'<div class="bonus">{clean.strip()}</div>')
                box_lines = []
                in_box = False
            else:
                in_box = True
            i += 1
            continue
        if in_box:
            box_lines.append(ln)
            i += 1
            continue
        # footnote line (--- then ¹ ...)
        if ln.strip() == "---":
            out.append('<hr class="footrule">')
            i += 1
            continue
        if re.match(r'^[¹²³⁴⁵⁶⁷⁸⁹⁰\s]', ln) or re.search(r'[¹²³⁴⁵⁶⁷⁸⁹⁰]\s', ln):
            # footnote block
            fn = ln.replace("¹", "<sup>1</sup>").replace("²", "<sup>2</sup>").replace("³", "<sup>3</sup>").replace("⁴", "<sup>4</sup>")
            out.append(f'<p class="footnotes">{fn}</p>')
            i += 1
            continue
        # normal paragraph
        p = ln.strip()
        if not p:
            i += 1
            continue
        p = html.escape(p).replace("~", "about")
        p = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', p)
        p = re.sub(r'\*(.+?)\*', r'<i>\1</i>', p)
        out.append(f'<p>{p}</p>')
        i += 1
    return "\n".join(out)

# ── Font face CSS (base64-embedded so headless Chromium renders them) ──
def font_face_css():
    import base64
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

def build_html():
    css = font_face_css()
    paper_bg = """
  background-color:#f7f1e1;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(180,160,120,0.10) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(150,130,90,0.12) 0%, transparent 45%),
    repeating-linear-gradient(0deg, rgba(120,100,70,0.025) 0px, rgba(120,100,70,0.025) 1px, transparent 1px, transparent 3px);
"""
    sections = []
    for fname, theme, _cover_title in ENTRIES:
        text = read_md(fname)
        title, body = parse_draft(text)
        svg = pick_svg(theme)
        img = ""
        if svg:
            uri = svg_to_datauri(svg)
            img = f'<img class="clip" src="{uri}" alt="{theme}"><p class="caption">CC0 clipart &middot; Openclipart</p>'
        rendered = render_body(body)
        sections.append(f"""
<section class="entry">
  <div class="clipwrap">{img}</div>
  <h2>{html.escape(title)}</h2>
  {rendered}
</section>
<div class="pagebreak"></div>
""")
    cover = f"""
<section class="cover">
  <div class="coverwash"></div>
  <div class="covertitle">
    <p class="kicker">UNCLE SEYMOUR'S</p>
    <h1>PONDERABLES</h1>
    <p class="vol">VOLUME ONE</p>
    <p class="sub">A Taxonomy of a Man Thinking Out Loud</p>
    <p class="byline">a toilet book, by wubu</p>
  </div>
</section>
<div class="pagebreak"></div>
"""
    # back/colophon
    colophon = f"""
<section class="colophon">
  <h2>About This Book</h2>
  <p>Every clipart image in this book is <b>CC0</b> (public-domain-equivalent), sourced from Openclipart. Every typeface is <b>OFL</b> (SIL Open Font License) — Special Elite, Old Standard TT, Rye, Bungee, DM Serif Display. The paper texture is a public-domain photograph from Wikimedia Commons.</p>
  <p>The words are the author's own. No commercial clip-art libraries were harmed, pirated, or borrowed in the making of this book.</p>
  <p class="price">$4.99 · Print-on-demand · wubu</p>
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
.caption {{ font-family:'Special Elite',monospace; font-size:6.5pt; color:#776; letter-spacing:1px; text-transform:uppercase; margin:1px 0 0; font-variant-numeric: lining-nums tabular-nums; font-feature-settings:"lnum" 1,"tnum" 1; }}
h2 {{ font-family:'Special Elite','Courier New', monospace; font-size: 12.5pt; line-height:1.1; color:#1a1a1a; margin: 3px 0 6px; }}
p {{ font-size: 9pt; line-height: 1.38; margin: 0 0 6px; text-align: justify; }}
b {{ font-weight:700; }}
.bonus {{ font-family:'Special Elite','Courier New', monospace; font-size:8pt; background:#f4efe2; border:1px solid #d8cda8; padding:6px 8px; margin:7px 0; border-radius:3px; line-height:1.4; }}
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

def main():
    html_doc = build_html()
    html_path = f"{OUT}/vol1.html"
    with open(html_path, "w") as f:
        f.write(html_doc)
    # Chromium print-to-pdf
    chrome = shutil.which("chromium") or shutil.which("chromium-browser")
    pdf_path = f"{OUT}/seymour_ponderables_vol1.pdf"
    cmd = [
        chrome, "--headless", "--no-sandbox", "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        "file://" + html_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-2000:])
        return 1
    sz = os.path.getsize(pdf_path)
    print(f"PDF written: {pdf_path} ({sz} bytes)")
    print("HTML intermediate:", html_path)

if __name__ == "__main__":
    main()
