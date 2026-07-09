#!/usr/bin/env python3
"""
Seymour Wins -- MAGAZINE ENGINE v2 (layout-overhaul)
=====================================================
v1 was functionally complete but visually vacant: covers were ~85% empty
whitespace, clip pages were one floating icon + 3 lines, and the single
most important asset -- the "through the years" spine (same date, every
year, side by side) -- was NEVER rendered. v2 keeps v1's proven
data machinery (event_pool, factoid_text, wiki_pd_image, clip_for,
raster) and adds REAL composition:

  P1  COVER        -- themed accent + hero clip + "on this day through
                      the years" teaser strip + issue number. No void.
  P2  FACTOID      -- two-column: factoid text | themed clip accent.
  P3  EDITORIAL   -- real issue text, drop-line, Colonel pull-quote.
  P4  THROUGH YEARS -- THE SPINE: every year's event for this date,
                      as a tagged timeline. The whole thesis, visible.
  P5  DISPATCH     -- Wikipedia PD image (improved resolver) or themed
                      clip, large, framed, captioned + sourced.
  P6.. CLIP SPREAD -- 2-up grid: image + caption pulled from the
                      day's REAL content, themed rule, varied.
  ..   PERSONAE    -- AI-personality pages: byline + universe, grounding
                      fact pull-quote, clip, speculative excerpt.

Requires: uv run --with cairosvg --with pymupdf python3 magazine_engine_v2.py [opts]
"""
import os, re, json, glob, random, datetime, argparse, time, sys, urllib.request, urllib.parse, urllib.error
from collections import defaultdict
import fitz

import magazine_engine as v1   # reuse proven machinery

HERE = v1.HERE
ROOT = v1.ROOT
OUT  = v1.OUT
IMG_CACHE = v1.IMG_CACHE

# ---- theme accent colors (RGB 0-1) ----
THEME_COLOR = {
    "penny":    (0.72, 0.52, 0.10),
    "supercap": (0.15, 0.55, 0.55),
    "versa":    (0.20, 0.40, 0.70),
    "gaming":   (0.55, 0.20, 0.65),
    "cuda":     (0.10, 0.60, 0.30),
    "internet":  (0.30, 0.50, 0.75),
    "paulsen":  (0.45, 0.35, 0.20),
    "meme":     (0.70, 0.30, 0.30),
    "gun":      (0.35, 0.35, 0.40),
    "flag":     (0.60, 0.20, 0.20),
    "book":     (0.40, 0.30, 0.55),
    "brain":    (0.50, 0.45, 0.20),
    "colonel":  (0.25, 0.45, 0.45),
    "metalgear": (0.30, 0.30, 0.35),
    "key":      (0.55, 0.45, 0.15),
    "sky":      (0.25, 0.55, 0.80),
}
INK = (0.12, 0.12, 0.14)
PAPER = (0.97, 0.96, 0.93)

COLONEL = [
    "Create context, not control content.",
    "Unnecessary information must be filtered.",
    "Selection for Societal Sanity.",
    "Filter garbage, retrieve valuable truths.",
    "We are formless... yet we persist.",
]

CONFIG = {
    "target_pages": 30,
    "front_pages": 5,
    "clips_per_day": 8,
    "personas_per_day": 18,
    "use_wiki": True,
    "wiki_dpi": 500,
    "clip_dpi": 360,
    "locked_theme": None,
}

# ---------------------------------------------------------------------------
# drawing helpers
# ---------------------------------------------------------------------------
def _col(t):
    return (t[0], t[1], t[2], 1.0)

def rect(doc, page, x0, y0, x1, y1, color, fill=None, width=1.0):
    r = fitz.Rect(x0, y0, x1, y1)
    page.draw_rect(r, color=_col(color), fill=_col(fill) if fill else None, width=width)

def line(page, x0, y0, x1, y1, color, width=1.0):
    page.draw_line(fitz.Point(x0, y0), fitz.Point(x1, y1), color=_col(color), width=width)

FONT_DIR = os.path.join(ROOT, "assets", "fonts")
_FONT_FILES = {
    "dmserif": "DMSerifDisplay-Regular.ttf",
    "specialelite": "SpecialElite-Regular.ttf",
}

def _ensure_font(page, name):
    """Embed a display font on the page if not already present."""
    if name in _FONT_FILES:
        p = os.path.join(FONT_DIR, _FONT_FILES[name])
        if os.path.exists(p):
            try:
                page.insert_font(fontname=name, fontfile=p)
            except Exception:
                pass

def text(page, pos, s, size=10, color=INK, bold=False, font=None, fontfile=None):
    fn = font or ("Helvetica-Bold" if bold else "Helvetica")
    if fontfile:
        fn = fontfile
        _ensure_font(page, fontfile)
    page.insert_text(pos, s, fontsize=size, color=_col(color), fontname=fn)

def wrap(words, maxw):
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= maxw:
            cur = (cur + " " + w).strip()
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines

def para(page, x, y, s, size=9, maxw=88, color=INK, leading=12.5, bold=False):
    for ln in wrap(s.split(), maxw):
        text(page, (x, y), ln, size=size, color=color, bold=bold)
        y += leading
    return y

def place_img(page, rect, png, fallback_color):
    """Fit an image into rect, centered, keeping aspect. Draws a tinted
    panel behind if png missing."""
    if png and os.path.exists(png) and os.path.getsize(png) > 0:
        try:
            page.insert_image(fitz.Rect(*rect), filename=png, keep_proportion=True)
            return True
        except Exception:
            pass
    rect and page.draw_rect(fitz.Rect(*rect), color=(0.6,0.6,0.6), fill=fallback_color, width=1)
    return False

# ---------------------------------------------------------------------------
# page builders
# ---------------------------------------------------------------------------
def p_cover(doc, theme, date, evs, issue_no, colonel):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    W, H = 595, 842
    # full-bleed top accent band
    rect(doc, pg, 0, 0, W, 26, accent, fill=accent, width=0)
    # hero clip (themed) upper-right
    clips = v1.clip_for(theme, 1, seed=f"{date.isoformat()}cv")
    hero = v1.raster(clips[0], 300) if clips else None
    # tinted panel behind hero for bleed (drawn first, image on top)
    rect(doc, pg, 330, 60, 560, 470, accent, fill=(0.97,0.96,0.93), width=0)
    place_img(pg, (330, 60, 560, 360), hero, accent)
    # lower hero band: big issue numeral + theme mark
    rect(doc, pg, 330, 360, 560, 470, accent, fill=accent, width=0)
    text(pg, (345, 430), f"#{issue_no:04d}", size=54, color=(1,1,1), fontfile="dmserif")
    text(pg, (345, 460), f"THEME: {theme.upper()}", size=11, color=(1,1,1), bold=True)
    # title block
    text(pg, (40, 70), "SEYMOUR WINS", size=42, color=INK, fontfile="dmserif")
    text(pg, (40, 112), "DAILY MAGAZINE", size=18, color=accent, bold=True)
    text(pg, (40, 142), date.strftime("%A %B %d, %Y").upper(), size=13, color=INK)
    text(pg, (40, 164), f"ISSUE #{issue_no:04d}   -   THEME: {theme.upper()}", size=10, color=(0.4,0.4,0.4))
    # "through the years" teaser strip
    y = 330
    rect(doc, pg, 40, y-18, W-40, y-14, accent, fill=accent, width=0)
    text(pg, (44, y-22), "ON THIS DAY - THROUGH THE YEARS", size=12, color=(1,1,1), bold=True, fontfile="dmserif")
    y += 6
    shown = sorted(evs, key=lambda e: int(e[0]) if str(e[0]).isdigit() else 0)[:6]
    for e in shown:
        yr = str(e[0])
        body = re.split(r"[:—-]", e[1])[0].strip()
        body = body if len(body) <= 52 else body[:52] + "..."
        text(pg, (44, y), yr, size=11, color=accent, bold=True, fontfile="dmserif")
        y = para(pg, 92, y, body, size=9.5, maxw=26, color=INK)
        y += 4
    # "IN THIS ISSUE" section band -- fills lower half
    by = 470
    rect(doc, pg, 40, by-18, W-40, by-14, accent, fill=accent, width=0)
    text(pg, (44, by-22), "IN THIS ISSUE", size=12, color=(1,1,1), bold=True)
    sections = [
        "Factoid of the Day -- history event x stream lens",
        "Editorial -- the verified anchor + Colonel codec",
        "Through The Years -- this date, every year on record",
        "Public-Domain Dispatch -- Wikipedia PD image of the subject",
        f"Clip Spreads -- {CONFIG['clips_per_day']} themed CC0 plates",
        f"Personae -- {CONFIG['personas_per_day']} AI personalities fork the day",
    ]
    yy = by + 8
    for s in sections:
        yy = para(pg, 50, yy, "- " + s, size=10, maxw=38, color=INK)
        yy += 8
    # thematic statement block -- fills the lower band
    rect(doc, pg, 40, 620, W-40, 760, (0.94,0.93,0.90), fill=(0.96,0.95,0.92), width=1)
    stmt = v1.THEME_LINES.get(theme, "Winds riding information: the thread continues.")
    text(pg, (60, 648), "THE THREAD", size=10, color=accent, bold=True)
    para(pg, 60, 668, stmt, size=12, maxw=78, color=INK)
    text(pg, (60, 740), f"Seymour Wins - {date.year}. One issue a day, every day, through the years.", size=9, color=(0.45,0.45,0.45))
    # colonel footer
    text(pg, (40, H-50), colonel, size=11, color=INK, bold=True)
    text(pg, (40, H-34), "Create context, not control content.", size=9, color=(0.45,0.45,0.45))
    return pg

def p_factoid(doc, theme, factoid, ev, colonel):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    rect(doc, pg, 0, 0, 595, 16, accent, fill=accent, width=0)
    text(pg, (40, 50), "FACTOID OF THE DAY", size=16, color=accent, bold=True)
    line(pg, 40, 60, 555, 60, accent, width=1.5)
    # two columns: left factoid text, right clip accent
    if factoid:
        y = 84
        for ln in factoid.splitlines()[:20]:
            if not ln.strip():
                y += 8; continue
            for chunk in [ln[i:i+62] for i in range(0, len(ln), 62)]:
                text(pg, (40, y), chunk, size=10, color=INK); y += 14
                if y > 740: break
    else:
        para(pg, 40, 90, (ev[1] if ev else "No anchor pooled for this day."), size=11, maxw=60)
    # right accent clip
    clips = v1.clip_for(theme, 1, seed=f"{theme}fa")
    acc = v1.raster(clips[0], 280) if clips else None
    rect(doc, pg, 360, 460, 555, 700, accent, fill=(0.96,0.95,0.92), width=1)
    place_img(pg, (380, 480, 535, 680), acc, accent)
    line(pg, 360, 705, 555, 705, accent, width=0.5)
    _cap = v1.THEME_LINES.get(theme, "")
    para(pg, 364, 712, _cap, size=8, maxw=24, color=(0.4,0.4,0.4))
    text(pg, (40, 800), f"The Colonel: {colonel}", size=9, color=(0.45,0.45,0.45))
    return pg

def p_editorial(doc, theme, issue_text, colonel):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    rect(doc, pg, 0, 0, 595, 16, accent, fill=accent, width=0)
    text(pg, (40, 50), "EDITORIAL", size=16, color=accent, bold=True, fontfile="dmserif")
    line(pg, 40, 60, 555, 60, accent, width=1.5)
    if not issue_text:
        para(pg, 40, 90, "No editorial seeded for this day. The thread continues in the archive.", size=11)
        return pg
    lines = [l for l in issue_text.splitlines() if l.strip()][:40]
    y = 90
    # drop-style first non-empty line
    first = True
    for ln in lines:
        if y > 770: break
        if first and len(ln) > 12:
            text(pg, (40, y), ln[:1], size=34, color=accent, fontfile="specialelite")
            text(pg, (78, y), ln[1:89], size=10.5, color=INK)
            y += 16
            first = False
            continue
        for chunk in [ln[i:i+92] for i in range(0, len(ln), 92)]:
            text(pg, (40, y), chunk, size=9.5, color=INK); y += 13
    # colonel pull-quote box
    rect(doc, pg, 40, 780, 555, 812, accent, fill=(0.96,0.95,0.92), width=1)
    text(pg, (50, 794), f'"{colonel}"', size=10, color=accent, bold=True)
    return pg

def p_through_years(doc, theme, evs, date):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    rect(doc, pg, 0, 0, 595, 16, accent, fill=accent, width=0)
    text(pg, (40, 50), "THROUGH THE YEARS", size=16, color=accent, bold=True, fontfile="dmserif")
    text(pg, (40, 70), f"{date.strftime('%B %d')} -- every year on record. The Seymour spine.", size=9.5, color=(0.4,0.4,0.4))
    line(pg, 40, 80, 555, 80, accent, width=1.5)
    # sort by year
    def yr(e):
        try: return int(e[0])
        except: return 0
    evs = sorted(evs, key=yr, reverse=True)[:34]
    y = 100
    for e in evs:
        yr_s = str(e[0])
        body = e[1]
        body = re.split(r"[:—-]", body)[0].strip()
        body = body if len(body) <= 96 else body[:96] + "..."
        text(pg, (44, y), yr_s, size=11, color=accent, bold=True)
        text(pg, (104, y), body, size=9, color=INK)
        y += 19
        if y > 800: break
    return pg

def p_dispatch(doc, theme, ev, q):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    rect(doc, pg, 0, 0, 595, 16, accent, fill=accent, width=0)
    text(pg, (40, 50), "PUBLIC-DOMAIN DISPATCH", size=15, color=accent, bold=True)
    img = v1.wiki_pd_image(q, f"{q}dp") if q else None
    caption = ""
    if img:
        # pull source from provenance
        prov = v1._load_wiki_prov()
        ck = re.sub(r"\W+", "_", (q or "").lower())[:50]
        prov = prov.get(ck, {})
        caption = prov.get("article", q or "")
        src = prov.get("license", "public domain / CC")
    else:
        clips = v1.clip_for(theme, 1, seed=f"{theme}dp")
        img = v1.raster(clips[0], 460) if clips else None
        caption = f"{theme} (CC0 clipart)"
        src = "CC0 / public domain"
    place_img(pg, (60, 90, 535, 560), img, accent)
    text(pg, (60, 580), f"Subject: {q or theme}", size=10, color=INK, bold=True)
    text(pg, (60, 600), caption[:120], size=9, color=(0.35,0.35,0.35))
    text(pg, (60, 620), f"Source: Wikipedia ({src})", size=8.5, color=(0.45,0.45,0.45))
    return pg

def p_clip_spread(doc, theme, clips, seed_base, content_line):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    # 2-up grid
    cells = [(40,80,290,330), (305,80,555,330)]
    for i, svg in enumerate(clips[:2]):
        x0,y0,x1,y1 = cells[i]
        rect(doc, pg, x0-6, y0-26, x1+6, y1+30, (0.9,0.9,0.88), fill=(0.96,0.95,0.92), width=0.5)
        rect(doc, pg, x0-6, y0-26, x1+6, y0-22, accent, fill=accent, width=0)
        png = v1.raster(svg, 300)
        place_img(pg, (x0, y0, x1, y1), png, accent)
        label = v1.PROV.get(os.path.basename(svg), {}).get("label", "CC0 clipart")
        text(pg, (x0, y1+8), f"CLIP {seed_base+ i+1}", size=9, color=accent, bold=True)
        text(pg, (x0, y1+22), label[:54], size=8, color=(0.4,0.4,0.4))
    # caption block from real content
    if content_line:
        text(pg, (40, 380), "FROM THE DAY'S THREAD", size=10, color=accent, bold=True)
        para(pg, 40, 400, content_line, size=10, maxw=92, color=INK)
    return pg

def p_persona(doc, theme, uf, colonel):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    persona = os.path.basename(uf)[2:-3]
    body = open(uf, errors="ignore").read()
    # parse grounding fact + universe
    m_u = re.search(r"\*\*UNIVERSE:\*\*\s*(.+)", body)
    m_g = re.search(r"\*\*GROUNDING FACT:\*\*\s*(.+)", body)
    universe = m_u.group(1).strip() if m_u else persona
    ground = m_g.group(1).strip() if m_g else ""
    rect(doc, pg, 0, 0, 595, 16, accent, fill=accent, width=0)
    text(pg, (40, 50), f"AU PERSONA - {persona}", size=15, color=accent, bold=True, fontfile="dmserif")
    text(pg, (40, 70), f"Universe: {universe}", size=9.5, color=(0.4,0.4,0.4), fontfile="specialelite")
    # grounding pull-quote
    rect(doc, pg, 40, 84, 555, 150, accent, fill=(0.96,0.95,0.92), width=1)
    text(pg, (50, 98), "GROUNDING FACT (verified anchor)", size=8.5, color=accent, bold=True)
    para(pg, 50, 114, ground[:300], size=9.5, maxw=72, color=INK)
    # clip
    clips = v1.clip_for(persona if persona in v1.THEME_DIRS else theme, 1, seed=persona)
    acc = v1.raster(clips[0], 260) if clips else None
    place_img(pg, (380, 170, 535, 360), acc, accent)
    # speculative excerpt
    clean = re.sub(r"\*\*", "", body)
    ex = clean.split("SPECULATIVE FICTION", 1)[-1][:600] if "SPECULATIVE" in clean else clean[:600]
    text(pg, (40, 380), "SPECULATIVE FICTION (forked from a verified anchor)", size=9, color=accent, bold=True)
    para(pg, 40, 398, ex.strip(), size=9, maxw=92, color=INK)
    text(pg, (40, 800), f'"{colonel}"', size=9, color=(0.45,0.45,0.45))
    return pg

def p_divider(doc, theme, label, sub):
    accent = THEME_COLOR.get(theme, (0.3,0.3,0.3))
    pg = doc.new_page()
    W, H = 595, 842
    rect(doc, pg, 0, 0, W, 26, accent, fill=accent, width=0)
    rect(doc, pg, 0, H-26, W, H, accent, fill=accent, width=0)
    # big centered label
    text(pg, (40, 400), label, size=46, color=INK, fontfile="dmserif")
    line(pg, 40, 430, 555, 430, accent, width=2)
    text(pg, (40, 460), sub, size=14, color=accent, bold=True)
    text(pg, (40, 790), "SEYMOUR WINS - DAILY MAGAZINE", size=9, color=(0.5,0.5,0.5))
    return pg

# ---------------------------------------------------------------------------
# orchestrator
# ---------------------------------------------------------------------------
def make_magazine(year, month, day, cfg=None):
    import fitz
    cfg = cfg or CONFIG
    rnd = random.Random(f"{year}{month:02d}{day:02d}")
    date = datetime.date(year, month, day)
    key = f"{month:02d}-{day:02d}"
    evs = v1.POOL.get(key, [])
    ev = rnd.choice(evs) if evs else None
    theme = cfg["locked_theme"] or rnd.choice(v1.THEME_DIRS)
    factoid = v1._factoid_text(year, month, day)
    colonel = rnd.choice(COLONEL)
    issue_no = date.timetuple().tm_yday

    doc = fitz.open()
    p_cover(doc, theme, date, evs, issue_no, colonel)
    p_factoid(doc, theme, factoid, ev, colonel)
    # editorial
    iss = os.path.join(v1.CAL, str(year), f"{month:02d}", f"{day:02d}.md")
    issue_text = open(iss, errors="ignore").read()[:1800] if os.path.exists(iss) else ""
    p_editorial(doc, theme, issue_text, colonel)
    # through the years (THE SPINE)
    p_through_years(doc, theme, evs, date)
    # dispatch
    subj = None
    if ev:
        subj = re.split(r"[:—-]", ev[1])[0].strip()
        q = " ".join(subj.split()[:6])
    else:
        q = None
    p_dispatch(doc, theme, ev, q)

    # clip spreads (2 per page)
    clips = v1.clip_for(theme, cfg["clips_per_day"], seed=f"{year}{month}{day}")
    content_line = ""
    if issue_text:
        for ln in issue_text.splitlines():
            if ln.strip().startswith("**FACT:**") or len(ln.strip()) > 40:
                content_line = ln.strip().lstrip("*").strip()
                if content_line: break
    ci = 0
    while ci < len(clips):
        p_clip_spread(doc, theme, clips[ci:ci+2], ci, content_line)
        ci += 2

    # section divider before personas
    p_divider(doc, theme, "PERSONAE",
                 f"{cfg['personas_per_day']} AI voices fork the day")

    # persona pages
    au_dir = os.path.join(v1.CAL, str(year), f"{month:02d}", f"{day:02d}_au")
    personas = []
    if os.path.isdir(au_dir):
        allu = sorted(glob.glob(os.path.join(au_dir, "u_*.md")))
        rnd.shuffle(allu)
        personas = allu[:cfg["personas_per_day"]]
    for uf in personas:
        p_persona(doc, theme, uf, colonel)

    out_dir = os.path.join(OUT, str(year)); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{year}-{month:02d}-{day:02d}.pdf")
    doc.save(out)
    return out, len(doc)

def main():
    ap = argparse.ArgumentParser(description="Seymour Wins magazine engine v2")
    ap.add_argument("years", nargs="*")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if a.dry:
        print("DRY v2: target front=5, clips=8, personas=18")
        return
    if len(a.years) == 3:
        out, n = make_magazine(int(a.years[0]), int(a.years[1]), int(a.years[2]))
        print(f"built {out} ({n} pages)")
        return
    years = [int(y) for y in a.years] if a.years else list(range(2020, 2027))
    for y in years:
        n = 0
        for mm in range(1, 13):
            for dd in range(1, 32):
                try: datetime.date(y, mm, dd)
                except ValueError: continue
                try:
                    make_magazine(y, mm, dd); n += 1
                except Exception as e:
                    print(f"  SKIP {y}-{mm:02d}-{dd:02d}: {e}")
        print(f"  {y}: {n} issues")

if __name__ == "__main__":
    main()
