#!/usr/bin/env python3
"""
Seymour Wins — CALENDAR BUILD ENGINE
issue = 1 day = 1 page; volume = 1 month; annual = 1 year.

Usage:
  python3 build_calendar.py YYYY MM            -> pdf/seymour_wins_YYYY_MM_<mon>.pdf
  python3 build_calendar.py YYYY               -> pdf/seymour_wins_YYYY_annual.pdf
  python3 build_calendar.py YYYY MM DD --through-years
                                            -> single date column across all years

Each issue file calendar/YYYY/MM/DD.md uses:
  **TITLE:** ...
  **THEME:** penny            (clipart theme dir under assets/clipart/)
  **FACT:**  <verified real-world anchor for this date>
  **OVERLAP:** [[2021-01-20]]  (optional cross-year echo, repeatable)

  body paragraphs... (markdown-ish: **bold**, *italic*, ~ -> about)
  ---
  footnotes with ¹²³...
"""
import os, re, html, subprocess, base64, shutil, json, sys

import theme_map
from theme_map import pick_svg

ROOT = "/home/wubu/seymour-project"
POND = f"{ROOT}/ponderables"
CAL = f"{POND}/calendar"
ASSETS = f"{ROOT}/assets"
CLIP = f"{ASSETS}/clipart"
FONTS = f"{ASSETS}/fonts"
OUT = f"{POND}/pdf"
os.makedirs(OUT, exist_ok=True)

MONTHS = ["", "jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]
MONTH_NAMES = ["", "January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# ---------- shared helpers (from build_issue1_pdf.py, verified) ----------
# pick_svg is imported from theme_map (curated on-theme mapping)

def svg_to_datauri(path):
    if not path:
        return ""
    with open(path) as f:
        s = f.read().strip()
    return "data:image/svg+xml;base64," + base64.b64encode(s.encode()).decode()

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
.entry { padding: 9px 11px; page-break-inside: avoid; }
.clipwrap { text-align:center; margin: 2px 0 6px; }
.clip { max-width: 72px; max-height: 72px; opacity:0.95;
  border:1px solid #c9bfa3; border-radius:6px; padding:5px; background:#fbf7ec;
  box-shadow: 0 1px 3px rgba(0,0,0,0.12); }
.body, .cover { font-variant-numeric: lining-nums tabular-nums; font-feature-settings: "lnum" 1, "tnum" 1; }
.caption { font-family:'Special Elite',monospace; font-size:6.5pt; color:#776; letter-spacing:1px; text-transform:uppercase; margin:1px 0 0; font-variant-numeric: lining-nums tabular-nums; font-feature-settings:"lnum" 1,"tnum" 1; }
.datestamp { font-family:'Special Elite',monospace; font-size:7.5pt; color:#a8741a; letter-spacing:1px; text-transform:uppercase; margin: 0 0 4px; font-variant-numeric: lining-nums tabular-nums; font-feature-settings:"lnum" 1,"tnum" 1; }
.fact { font-family:'Special Elite','Courier New', monospace; font-size:7.5pt; background:#efe9d8; border-left:3px solid #c9a23a; padding:6px 8px; margin:0 0 7px; line-height:1.4; }
h2 { font-family:'Special Elite','Courier New', monospace; font-size: 12.5pt; line-height:1.1; color:#1a1a1a; margin: 3px 0 6px; }
p { font-size: 9pt; line-height: 1.38; margin: 0 0 6px; text-align: justify; }
b { font-weight:700; }
.bonus { font-family:'Special Elite','Courier New', monospace; font-size:8pt; background:#f4efe2; border:1px solid #d8cda8; padding:6px 8px; margin:7px 0; border-radius:3px; line-height:1.4; }
.footrule { border:0; border-top:1px solid #ccc; margin:7px 0 5px; }
.footnotes { font-size:7pt; color:#555; line-height:1.4; }
.footnotes sup { color:#a8741a; font-weight:700; margin-right:3px; }
.pagebreak { page-break-after: always; }
.overlap { font-family:'Special Elite',monospace; font-size:7pt; color:#776; border-top:1px dashed #cbb; margin-top:6px; padding-top:4px; font-variant-numeric: lining-nums tabular-nums; font-feature-settings:"lnum" 1,"tnum" 1; }
.cover { height: 6.875in; display:flex; align-items:center; justify-content:center; background:#1c1c1c; color:#f3ecd8; text-align:center; }
.coverwash { position:absolute; inset:0; background:
    radial-gradient(circle at 30% 20%, rgba(243,210,122,0.10), transparent 50%),
    radial-gradient(circle at 70% 80%, rgba(243,210,122,0.08), transparent 55%),
    repeating-linear-gradient(0deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 4px);
  opacity:0.5; }
.covertitle { position:relative; z-index:2; padding:0 10px; }
.kicker { font-family:'Special Elite',monospace; letter-spacing:2px; font-size:11pt; margin:0; }
h1 { font-family:'Rye', serif; font-size:30pt; margin:8px 0; color:#f3d27a; line-height:1.0; }
.vol { font-family:'Special Elite',monospace; letter-spacing:4px; font-size:12pt; margin:0; }
.sub { font-family:'Old Standard TT', Georgia, serif; font-style:italic; font-size:11pt; margin:14px 0 0; line-height:1.3; }
.byline { font-family:'Special Elite',monospace; font-size:9pt; color:#bbb; margin-top:8px; }
"""

# ---------- issue parsing ----------

ISSUE_RE = re.compile(r"\*\*([A-Z]+):\*\*\s*(.*)")

def parse_issue(text):
    meta = {}
    body = []
    for ln in text.splitlines():
        m = ISSUE_RE.match(ln.strip())
        if m and m.group(1) in ("TITLE", "THEME", "FACT", "OVERLAP"):
            key = m.group(1).lower()
            if key == "overlap":
                meta.setdefault("overlap", []).append(m.group(2).strip())
            else:
                meta[key] = m.group(2).strip()
            continue
        body.append(ln)
    meta["body"] = "\n".join(body).strip()
    return meta

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

def issue_html(meta, datestamp):
    theme = meta.get("theme", "")
    svg = pick_svg(theme)
    img = ""
    if svg:
        uri = svg_to_datauri(svg)
        img = (f'<div class="clipwrap"><img class="clip" src="{uri}" alt="{theme}">'
               f'<p class="caption">CC0 clipart &middot; Openclipart</p></div>')
    fact = ""
    if meta.get("fact"):
        fact = f'<div class="fact">REAL-WORLD ANCHOR: {html.escape(meta["fact"])}</div>'
    overlap = ""
    if meta.get("overlap"):
        links = " &middot; ".join(html.escape(o) for o in meta["overlap"])
        overlap = f'<p class="overlap">OVERLAP-TIME &rarr; {links}</p>'
    rendered = render_body(meta.get("body", ""))
    title = html.escape(meta.get("title", "Untitled"))
    return f"""
<section class="entry">
  <p class="datestamp">{datestamp}</p>
  {img}
  <h2>{title}</h2>
  {fact}
  {rendered}
  {overlap}
</section>
<div class="pagebreak"></div>
"""

def cover_html(year, month=None, day=None, subtitle="", through=False):
    if through:
        t = "THROUGH THE YEARS"
        v = datestamp_str(year, month, day)
        s = "one date, every year &mdash; the memetic column"
    elif day:
        t = "SEYMOUR WINS"
        v = datestamp_str(year, month, day)
        s = subtitle or "a daily ponderable"
    elif month:
        t = "SEYMOUR WINS"
        v = f"{MONTH_NAMES[month].upper()} {year}"
        s = subtitle or "a month of ponderables"
    else:
        t = "SEYMOUR WINS"
        v = f"ANNUAL {year}"
        s = subtitle or "a year of ponderables"
    return f"""
<section class="cover">
  <div class="coverwash"></div>
  <div class="covertitle">
    <p class="kicker">{t}</p>
    <h1>{v}</h1>
    <p class="sub">{s}</p>
    <p class="byline">a toilet book, by wubu &middot; TDA-audited &middot; memetic overlap-time</p>
  </div>
</section>
<div class="pagebreak"></div>
"""

def datestamp_str(y, m, d):
    if d:
        return f"{MONTHS[m].upper()} {int(d):02d} {y}"
    if m:
        return f"{MONTH_NAMES[m].upper()} {y}"
    return str(y)

def list_days(y, m):
    d = f"{CAL}/{y:04d}/{m:02d}"
    if not os.path.isdir(d):
        return []
    return sorted(int(f[:2]) for f in os.listdir(d)
                  if f.endswith(".md") and f[:2].isdigit())

def load_issue(y, m, d):
    p = f"{CAL}/{y:04d}/{m:02d}/{d:02d}.md"
    if not os.path.exists(p):
        return None
    return parse_issue(open(p).read())

# ---------- build targets ----------

def build_month(y, m):
    days = list_days(y, m)
    if not days:
        print(f"no issues for {y}-{m:02d}"); return None
    css = font_face_css() + CSS
    parts = [cover_html(y, m, subtitle=f"{MONTH_NAMES[m]} {y} &mdash; COVID Cambrian Explosion")]
    for d in days:
        meta = load_issue(y, m, d)
        if not meta:
            continue
        parts.append(issue_html(meta, datestamp_str(y, m, d)))
    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>\n" + "\n".join(parts) + "</body></html>")
    html_path = f"{OUT}/_tmp_{y}{m:02d}.html"
    with open(html_path, "w") as f:
        f.write(full)
    pdf_path = f"{OUT}/seymour_wins_{y}_{m:02d}_{MONTHS[m]}.pdf"
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or "/snap/bin/chromium"
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        "file://" + html_path], capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-1500:]); return None
    os.remove(html_path)
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes), {len(days)} issues")
    return pdf_path

def build_year(y):
    months = [m for m in range(1, 13) if list_days(y, m)]
    if not months:
        print(f"no issues for {y}"); return None
    css = font_face_css() + CSS
    parts = [cover_html(y, subtitle="COVID Cambrian Explosion &mdash; the year it all mutated")]
    for m in months:
        for d in list_days(y, m):
            meta = load_issue(y, m, d)
            if meta:
                parts.append(issue_html(meta, datestamp_str(y, m, d)))
    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>\n" + "\n".join(parts) + "</body></html>")
    html_path = f"{OUT}/_tmp_{y}_annual.html"
    with open(html_path, "w") as f:
        f.write(full)
    pdf_path = f"{OUT}/seymour_wins_{y}_annual.pdf"
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or "/snap/bin/chromium"
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        "file://" + html_path], capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-1500:]); return None
    os.remove(html_path)
    n = sum(len(list_days(y, m)) for m in months)
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes), {n} issues")
    return pdf_path

def build_through(y, m, d):
    """single date, every year that has it, as a column"""
    css = font_face_css() + CSS
    parts = [cover_html(y, m, d, through=True)]
    years = sorted({int(f) for f in os.listdir(CAL)
                    if f.isdigit() and os.path.exists(f"{CAL}/{f}/{m:02d}/{d:02d}.md")})
    for yy in years:
        meta = load_issue(yy, m, d)
        if meta:
            parts.append(issue_html(meta, datestamp_str(yy, m, d)))
    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>\n" + "\n".join(parts) + "</body></html>")
    html_path = f"{OUT}/_tmp_through_{m:02d}_{d:02d}.html"
    with open(html_path, "w") as f:
        f.write(full)
    pdf_path = f"{OUT}/seymour_wins_through_{m:02d}_{d:02d}.pdf"
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or "/snap/bin/chromium"
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        "file://" + html_path], capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-1500:]); return None
    os.remove(html_path)
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes), {len(years)} years")
    return pdf_path

def build_constants_volume():
    """Render all 100 daily constants as a standalone 'Daily Constants' volume.
    Each constant = 1 page, themed clipart, the overlap thread, and an instance.
    This is the structural substrate; stream transcripts mutate it (Cambrian)."""
    import json as _json
    cj = f"{POND}/daily_constants.json"
    if not os.path.exists(cj):
        print("daily_constants.json missing — run build_constants.py first"); return None
    doc = _json.load(open(cj))
    css = font_face_css() + CSS
    cover = f"""
<section class="cover">
  <div class="coverwash"></div>
  <div class="covertitle">
    <p class="kicker">SEYMOUR WINS</p>
    <h1>DAILY CONSTANTS</h1>
    <p class="sub">100 things that happen every day &mdash; the substrate for memetic overlap</p>
    <p class="byline">a toilet book, by wubu &middot; TDA-audited &middot; Cambrian overlap engine</p>
  </div>
</section>
<div class="pagebreak"></div>
"""
    parts = [cover]
    for c in doc["constants"]:
        theme = c["theme"]
        svg = pick_svg(theme, c.get("rotation_index", 0))
        img = ""
        if svg:
            uri = svg_to_datauri(svg)
            img = (f'<div class="clipwrap"><img class="clip" src="{uri}" alt="{theme}">'
                   f'<p class="caption">CC0 clipart &middot; Wikimedia/Openclipart</p></div>')
        thread = c.get("thread", f"THREAD {c['id']} &rarr; your streams mutate this daily.")
        body = (f'<section class="entry">\n'
                f'  <p class="datestamp">{c["id"]} &middot; {c["category"].upper()} &middot; stream: {c["stream_link"]}</p>\n'
                f'  {img}\n'
                f'  <h2>{html.escape(c["name"])}</h2>\n'
                f'  <div class="fact">DAILY CONSTANT: {html.escape(c["overlap"])}</div>\n'
                f'  <p>{html.escape(c["instance"])}</p>\n'
                f'  <p class="overlap">{thread}</p>\n'
                f'</section>\n<div class="pagebreak"></div>\n')
        parts.append(body)
    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>\n" + "\n".join(parts) + "</body></html>")
    html_path = f"{OUT}/_tmp_constants.html"
    with open(html_path, "w") as f:
        f.write(full)
    pdf_path = f"{OUT}/seymour_wins_daily_constants.pdf"
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or "/snap/bin/chromium"
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        "file://" + html_path], capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-1500:]); return None
    os.remove(html_path)
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes), {len(doc['constants'])} constants")
    return pdf_path

def parse_au(text):
    meta = {}
    body = []
    for ln in text.splitlines():
        m = ISSUE_RE.match(ln.strip())
        if m and m.group(1) in ("PAGE", "UNIVERSE", "SKILL", "GROUNDING FACT", "MODE"):
            meta[m.group(1).lower()] = m.group(2).strip()
            continue
        body.append(ln)
    meta["body"] = "\n".join(body).strip()
    return meta

def au_html(meta, datestamp):
    universe = html.escape(meta.get("universe", "AU"))
    skill = html.escape(meta.get("skill", ""))
    grounding = html.escape(meta.get("grounding fact", ""))
    mode = html.escape(meta.get("mode", "SPECULATIVE FICTION"))
    rendered = render_body(meta.get("body", ""))
    return f"""
<section class="entry au">
  <p class="datestamp">{datestamp}</p>
  <p class="aulabel">ALTERNATE UNIVERSE &middot; {universe} &middot; SKILL: {skill}</p>
  <div class="grounding">GROUNDING FACT: {grounding}</div>
  <div class="modeflag">{mode}</div>
  {rendered}
</section>
<div class="pagebreak"></div>
"""

def build_year_mv(y):
    """Annual PDF WITH the multiverse: real day, then its AU pages interleaved."""
    months = [m for m in range(1, 13) if list_days(y, m)]
    if not months:
        print(f"no issues for {y}"); return None
    css = font_face_css() + CSS
    parts = [cover_html(y, subtitle="COVID Cambrian Explosion &mdash; the year it all mutated &middot; MULTIVERSE EDITION")]
    n_au = 0
    for m in months:
        for d in list_days(y, m):
            meta = load_issue(y, m, d)
            if meta:
                parts.append(issue_html(meta, datestamp_str(y, m, d)))
            au_dir = f"{CAL}/{y:04d}/{m:02d}/{d:02d}_au"
            if os.path.isdir(au_dir):
                for af in sorted(os.listdir(au_dir)):
                    if af.endswith(".md"):
                        am = parse_au(open(f"{au_dir}/{af}").read())
                        parts.append(au_html(am, datestamp_str(y, m, d)))
                        n_au += 1
    full = (f"<!doctype html><html><head><meta charset='utf-8'>"
            f"<style>{css}</style></head><body>\n" + "\n".join(parts) + "</body></html>")
    html_path = f"{OUT}/_tmp_{y}_mv.html"
    with open(html_path, "w") as f:
        f.write(full)
    pdf_path = f"{OUT}/seymour_wins_{y}_multiverse.pdf"
    chrome = shutil.which("chromium") or shutil.which("chromium-browser") or "/snap/bin/chromium"
    r = subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}",
                        "file://" + html_path], capture_output=True, text=True)
    if r.returncode != 0:
        print("CHROMIUM ERR:\n", r.stderr[-1500:]); return None
    os.remove(html_path)
    n = sum(len(list_days(y, m)) for m in months)
    print(f"PDF: {pdf_path} ({os.path.getsize(pdf_path)} bytes), {n} real + {n_au} AU pages")
    return pdf_path

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__); sys.exit(1)
    if args[0] == "constants":
        build_constants_volume()
        sys.exit(0)
    y = int(args[0])
    through = "--through-years" in args
    mv = "--multiverse" in args
    if mv:
        build_year_mv(y)
        sys.exit(0)
    if len(args) >= 2 and not through:
        m = int(args[1])
        if len(args) >= 3:
            d = int(args[2])
            build_through(y, m, d)
        else:
            build_month(y, m)
    else:
        build_year(y)
