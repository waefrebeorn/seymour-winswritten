#!/usr/bin/env python3
"""
Seymour Wins — LEGACY ODD & FUNNY volume
========================================
One curated print-ready PDF preserving the genuinely odd/funny *old* content
that the rejected magazine_engine line (v1/v2/v3, 2026-07-09) produced, before
those engines were deleted:

  - AU PERSONAS: 76,560 "alternate universe" speculative-fiction forks of real
    history (30 types: solarpunk, horror, comedy, conspiracy, utopia...). We
    pick a varied, genuinely-weird sample per type.
  - FROM THE STREAM: real quotable bits from funny_bits.json (the banked,
    cleaned stream quotes) as an appendix.

This is a LEGACY artifact — dead-to-rights only (CC0 fonts; no external
clipart required, but themed CC0 clipped if available). Not the live product.
"""
import os, re, html, json, glob, random, base64, shutil, subprocess

ROOT = "/home/wubu/seymour-project"
HERE = os.path.join(ROOT, "ponderables")
DRAFTS = os.path.join(HERE, "drafts")
ASSETS = os.path.join(ROOT, "assets")
CLIP = os.path.join(ASSETS, "clipart")
FONTS = os.path.join(ASSETS, "fonts")
OUT = os.path.join(HERE, "pdf")
os.makedirs(OUT, exist_ok=True)

random.seed(20260709)

# ── gather AU personas by type ──
AU_DIRS = glob.glob(os.path.join(HERE, "calendar", "**", "*_au"), recursive=True)
by_type = {}
for d in AU_DIRS:
    for f in glob.glob(os.path.join(d, "u_*.md")):
        t = os.path.basename(f)[2:-3]
        by_type.setdefault(t, []).append(f)

# pick a quirky, varied sample: 2 per type, prefer short + odd word signals
ODD_WORDS = ("conspiracy", "horror", "dystopia", "utopia", "anime", "solarpunk",
             "ritual", "comedy", "thriller", "magical", "conspiracy", "dream")
chosen = []
for t, files in by_type.items():
    files.sort(key=lambda p: os.path.getsize(p))
    # pick the 2 oddest-ish: shortest (condensed weird) + one random
    short = files[: max(1, len(files)//20)][:1]
    rnd = random.sample(files, 1)
    for p in short + rnd:
        try:
            txt = open(p, errors="ignore").read()
        except Exception:
            continue
        chosen.append((t, txt))
random.shuffle(chosen)
# cap to a sane volume (~44 entries)
chosen = chosen[:44]

# ── funny bits appendix ──
FB = json.load(open(os.path.join(HERE, "funny_bits.json")))
fb_samples = []
for t, lines in FB.items():
    if not lines:
        continue
    for ln in random.sample(lines, min(2, len(lines))):
        ln = re.sub(r"\s+", " ", ln).strip()
        if 30 <= len(ln) <= 160:
            fb_samples.append((t, ln))
random.shuffle(fb_samples)
fb_samples = fb_samples[:30]

# ── font face ──
def font_face_css():
    css = ""
    mapping = {"Special Elite": "SpecialElite-Regular.ttf",
               "Old Standard TT": "OldStandardTT-Regular.ttf",
               "Rye": "Rye-Regular.ttf"}
    for fam, fn in mapping.items():
        p = os.path.join(FONTS, fn)
        if os.path.exists(p):
            b64 = base64.b64encode(open(p, "rb").read()).decode()
            css += f"@font-face {{ font-family:'{fam}'; src:url(data:font/truetype;base64,{b64}) format('truetype'); font-weight:normal; font-style:normal; }}\n"
    return css

def esc(s):
    return html.escape(s).replace("~", "about")

def render_persona(t, txt):
    # pull the body after the MODE line, plus the GROUNDING FACT
    lines = txt.splitlines()
    grounding = ""
    body = []
    in_body = False
    for ln in lines:
        if ln.startswith("**GROUNDING FACT:**"):
            grounding = ln.split("**GROUNDING FACT:**", 1)[1].strip()
            continue
        if ln.startswith("**MODE:**"):
            in_body = True
            continue
        if ln.startswith("> **COLONEL"):
            continue
        if in_body and ln.strip():
            body.append(ln.strip())
    body = " ".join(body)
    body = re.sub(r"\s+", " ", body)
    return f"""
<div class="entry">
  <div class="tag">{esc(t.upper())}</div>
  <div class="ground">ANCHOR: {esc(grounding)}</div>
  <p>{esc(body[:600])}</p>
</div>"""

def render_fb(t, ln):
    return f'<p class="fb"><span class="fbtag">[{esc(t)}]</span> &ldquo;{esc(ln)}&rdquo;</p>'

def build_html():
    css = font_face_css()
    # pack 3 personas per page so pages aren't empty
    threes = [chosen[i:i+3] for i in range(0, len(chosen), 3)]
    persona_secs = ""
    for pr in threes:
        inner = "\n".join(render_persona(t, x) for t, x in pr)
        persona_secs += f'<div class="pair">{inner}</div><div class="pagebreak"></div>'
    fb_secs = "\n".join(render_fb(t, x) for t, x in fb_samples)
    cover = f"""
<section class="cover">
  <div class="covertitle">
    <p class="kicker">SEYMOUR WINS &middot; LEGACY</p>
    <h1>ODD &amp; FUNNY</h1>
    <p class="vol">THE LOST ALTERNATE UNIVERSES</p>
    <p class="sub">Speculative-fiction forks of real history + bits from the stream</p>
    <p class="byline">recovered from the rejected magazine_engine era &middot; wubu</p>
  </div>
</section>
<div class="pagebreak"></div>"""
    full = f"""<!doctype html><html><head><meta charset="utf-8"><style>
{css}
@page {{ size: 4.5in 7.125in; margin: 0.125in; }}
* {{ box-sizing: border-box; }}
body {{ font-family:'Old Standard TT',Georgia,serif; color:#222; background:#f7f1e1; margin:0; }}
.entry {{ padding: 10px 12px; page-break-inside: avoid; }}
.pair {{ display:flex; flex-direction:column; gap:14px; padding:10px 12px; }}
.tag {{ font-family:'Special Elite',monospace; font-size:8pt; letter-spacing:2px; color:#a8741a; text-transform:uppercase; margin-bottom:4px; }}
.ground {{ font-family:'Special Elite',monospace; font-size:7.5pt; color:#555; background:#efe7d2; border-left:3px solid #a8741a; padding:4px 6px; margin-bottom:7px; line-height:1.3; }}
p {{ font-size:9pt; line-height:1.4; margin:0 0 6px; text-align:justify; }}
.pagebreak {{ page-break-after: always; }}
.cover {{ height:6.875in; display:flex; align-items:center; justify-content:center; background:#161616; color:#f3ecd8; text-align:center; }}
.covertitle {{ max-width:90%; }}
.kicker {{ font-family:'Special Elite',monospace; letter-spacing:2px; font-size:9pt; margin:0; }}
h1 {{ font-family:'Rye',serif; font-size:34pt; margin:8px 0; color:#f3d27a; }}
.vol {{ font-family:'Special Elite',monospace; letter-spacing:3px; font-size:10pt; margin:0; }}
.sub {{ font-family:'Old Standard TT',serif; font-style:italic; font-size:10pt; margin:10px 0; }}
.byline {{ font-family:'Special Elite',monospace; font-size:8pt; color:#aaa; }}
.fbsec h2 {{ font-family:'Rye',serif; color:#1a1a1a; font-size:18pt; }}
.fb {{ font-size:9pt; line-height:1.4; margin:0 0 5px; }}
.fbtag {{ font-family:'Special Elite',monospace; font-size:7pt; color:#a8741a; margin-right:4px; }}
</style></head><body>
{cover}
{persona_secs}
<section class="fbsec"><h2>From the Stream</h2>{fb_secs}</section>
</body></html>"""
    return full

def main():
    doc = build_html()
    html_path = os.path.join(OUT, "legacy_odd_funny.html")
    open(html_path, "w").write(doc)
    chrome = shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome:
        print("CHROMIUM not found"); return 1
    pdf_path = os.path.join(OUT, "seymour_wins_legacy_odd_funny.pdf")
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        "file://" + html_path], capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-2000:]); return 1
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes) | personas={len(chosen)} funny={len(fb_samples)}")
    print("HTML:", html_path)

if __name__ == "__main__":
    main()
