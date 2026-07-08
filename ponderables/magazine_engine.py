#!/usr/bin/env python3
"""
Seymour Wins — MAGAZINE ENGINE
================================================================
Each daily issue becomes an ILLUSTRATED MAGAZINE (default 30 pages):
  P1     Cover (date, theme, Colonel masthead)
  P2     Factoid (history event + stream lens + Colonel)
  P3     Editorial (real daily issue text)
  P4     PUBLIC-DOMAIN DISPATCH — a real Wikipedia PD/CC image of the event's
         subject, resolved via the search API (not a guessed title), + caption
  P5..   CLIP pages  — CC0 clipart themed to the day + a genuine caption
  ..P30  PERSONA pages — the "AI personalities" (AU personas) each illustrated

Content & control (edit CONFIG or pass CLI flags):
  - target_pages, clips_per_day, personas_per_day
  - use_wiki on/off, locked_theme, year range, dry-run count
  - captions pull the REAL factoid text when present (systems wired together)

Principles:
  - ONE PAGE = ONE PAGE. Every page carries genuine content. No filler.
  - All imagery PUBLIC DOMAIN / CC0, provenance-tracked (clipart + wiki).
  - Wikipedia images: license-filtered (PD / CC0 / CC-BY / CC-BY-SA / GFDL).
  - Output: pdf/magazine/<year>/<MMDD>.pdf  (LOCAL ONLY, gitignored)

Requires: uv run --with cairosvg --with pymupdf python3 magazine_engine.py [opts]
"""
import os, re, json, glob, random, datetime, argparse, time, sys, urllib.request, urllib.parse, urllib.error
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
POOL = json.load(open(os.path.join(HERE, "event_pool.json")))
CAL = os.path.join(HERE, "calendar")
FAC = os.path.join(HERE, "factoids")
CLIP = os.path.join(ROOT, "assets", "clipart")
PROV = json.load(open(os.path.join(CLIP, "PROVENANCE.json")))
OUT = os.path.join(HERE, "pdf", "magazine")
IMG_CACHE = os.path.join(HERE, "pdf", "magazine_imgs")
WIKI_PROV = os.path.join(IMG_CACHE, "wiki_provenance.json")
os.makedirs(IMG_CACHE, exist_ok=True)

API = "https://en.wikipedia.org/w/api.php"
UA = {"User-Agent": "SeymourAbsorber/1.0 (educational; contact: hermit)"}

_WIKI_TS = [0.0]
_WIKI_MIN_GAP = 1.2   # max ~50 req/min — Wikipedia polite rate

def _get(url, retries=4):
    """Throttled GET with retry/backoff on 429/5xx. Returns parsed JSON."""
    for attempt in range(retries):
        wait = _WIKI_MIN_GAP - (time.time() - _WIKI_TS[0])
        if wait > 0:
            time.sleep(wait)
        _WIKI_TS[0] = time.time()
        req = urllib.request.Request(url, headers=UA)
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503):
                raw = e.headers.get("Retry-After") if e.headers else None
                try:
                    back = float(raw) if raw is not None else 2 ** (attempt + 1)
                except (TypeError, ValueError):
                    back = 2 ** (attempt + 1)
                time.sleep(min(back, 30))
                continue
            raise
    raise RuntimeError("Wikipedia API unavailable after retries")

THEME_DIRS = ["penny","supercap","versa","gaming","cuda","internet","paulsen","meme",
              "gun","flag","book","brain","colonel","metalgear","key","sky"]

# ---- CONFIG (control surface; overridable via CLI) ----
CONFIG = {
    "target_pages": 30,
    "front_pages": 4,        # cover + factoid + editorial + dispatch
    "clips_per_day": 8,      # illustrated CC0 clipart pages
    "personas_per_day": 18,  # AI-personality pages (rest of body to hit target)
    "use_wiki": True,
    "wiki_dpi": 500,
    "clip_dpi": 320,
    "locked_theme": None,    # None = random per day
}

# license tokens we accept as public-domain-equivalent
PD_TOKENS = ["public domain","pd","cc0","cc-by","cc-by-sa","gfdl","pdm"]
IMG_BLOCK = ["logo","icon","commons-logo","wiki","quiz","button","speaker"]

# genuine caption lines per theme (no fluff — real thread)
THEME_LINES = {
    "penny": "The copper thread: pennies found, pennies earned, the street-penny gospel.",
    "supercap": "The supercapacitor + small-generator hybrid — freedom from the grid.",
    "versa": "The 2019 Nissan Versa: 40 MPG, ~10 miles per dollar, the commute monastery.",
    "gaming": "The stream — @wubustreams. Raids lost and won, the games played.",
    "cuda": "The CUDA grind — inference, kernels, the machine that thinks.",
    "internet": "The open web — absorbed, re-served as context.",
    "paulsen": "Gary Paulsen — Hatchet, the foster-kid who read 100 books by lamplight.",
    "meme": "The meme — the unit of culture that replicates whether you like it or not.",
    "gun": "A weapon is a fact that ends the argument; the feed starts them.",
    "flag": "Flags are maps of who won the argument about the border.",
    "book": "Books are time-travel devices with better latency than memory.",
    "brain": "The brain is a prediction engine that mistakes its guesses for the world.",
    "colonel": "Create context, not control content.",
    "metalgear": "The Colonel was right about the codec. And about everything else.",
    "key": "A key is a promise that the lock keeps.",
    "sky": "The sky is the only public domain that nobody patented.",
}

# --- clipart index by theme (exclude _quarantine) ---
CLIP_BY_THEME = defaultdict(list)
for k, v in PROV.items():
    theme = v.get("theme")
    lic = (v.get("license") or "").lower()
    if theme in THEME_DIRS and ("cc0" in lic or "public" in lic):
        p = os.path.join(CLIP, theme, k)
        if os.path.exists(p):
            CLIP_BY_THEME[theme].append(p)

def clip_for(theme, n=10, seed=None):
    rnd = random.Random(seed)
    pool = CLIP_BY_THEME.get(theme, []) or sum(CLIP_BY_THEME.values(), [])
    rnd.shuffle(pool)
    return pool[:n]

# --- Wikipedia: resolve article -> PD/CC image (cached + provenance) ---
def wiki_resolve_article(phrase):
    """Resolve a free-text event phrase to the best Wikipedia article title.
    Prefers exact/non-disambiguation titles over the raw first hit."""
    params = {"action":"query","list":"search","srsearch":phrase,
              "srlimit":5,"format":"json"}
    url = API + "?" + urllib.parse.urlencode(params)
    try:
        d = _get(url)
        hits = d.get("query",{}).get("search",[])
        if not hits:
            return None
        # score: exact-ish title > shorter > not a disambiguation
        def score(h):
            t = h["title"].lower()
            s = 0
            if t == phrase.lower(): s += 5
            if "(" in t and "disambiguation" in t: s -= 4
            if any(w in t for w in ["list of","timeline of"]): s -= 1
            s += max(0, 4 - len(t.split()))
            return s
        return sorted(hits, key=score, reverse=True)[0]["title"]
    except Exception:
        return None

def _load_wiki_prov():
    if os.path.exists(WIKI_PROV):
        return json.load(open(WIKI_PROV))
    return {}

def _save_wiki_prov(p):
    json.dump(p, open(WIKI_PROV,"w"), indent=1)

def wiki_pd_image(query, seed):
    """Return local png path for a PD/CC image of 'query', or None.
    Tries several query refinements (full phrase -> shorter keywords) so a
    single bad article resolution doesn't force a clipart fallback."""
    if not CONFIG["use_wiki"]:
        return None
    cache_key = re.sub(r"\W+", "_", query.lower())[:50]
    cached = os.path.join(IMG_CACHE, cache_key + ".png")
    if os.path.exists(cached):
        return cached
    words = [w for w in re.split(r"[^a-z0-9]+", query.lower()) if len(w) > 2]
    queries = []
    # candidate queries: full phrase, progressively shorter fronts,
    # AND the leading proper-noun phrase (capitalized words from the
    # original query) which usually IS the article subject.
    caps = " ".join(w for w in query.split() if w[:1].isupper() and len(w) > 2)
    for cand in (query, caps, " ".join(words[:6]), " ".join(words[:4]),
                   " ".join(words[:2])):
        c = cand.lower().strip()
        if c and c not in queries:
            queries.append(c)
    rnd = random.Random(seed)
    for q in (rnd.sample(queries, len(queries)) if queries else []):
        article = wiki_resolve_article(q)
        if not article:
            continue
        params = {"action":"query","generator":"images","titles":article,
                  "prop":"imageinfo","iiprop":"url|extmetadata",
                  "iiurlwidth":str(CONFIG["wiki_dpi"]),"gimlimit":"50","format":"json"}
        url = API + "?" + urllib.parse.urlencode(params)
        try:
            d = _get(url)
            pages = d.get("query",{}).get("pages",{})
            cands = []
            for pg in pages.values():
                ii = (pg.get("imageinfo") or [{}])[0]
                title = pg.get("title","")
                if not title.lower().endswith((".jpg",".jpeg",".png")):
                    continue
                if any(b in title.lower() for b in IMG_BLOCK):
                    continue
                lic = (ii.get("extmetadata",{}).get("LicenseShortName",{}).get("value","") or "").lower()
                if any(t in lic for t in PD_TOKENS) and "thumburl" in ii:
                    cands.append((title, ii["thumburl"], lic))
            if not cands:
                continue
            rnd.shuffle(cands)
            title, src, lic = cands[0]
            req = urllib.request.Request(src, headers=UA)
            with urllib.request.urlopen(req, timeout=20) as r:
                img_bytes = r.read()
            with open(cached, "wb") as fp:
                fp.write(img_bytes)
            prov = _load_wiki_prov()
            prov[cache_key] = {"article": article, "file": title,
                               "source": src, "license": lic, "query": q}
            _save_wiki_prov(prov)
            return cached
        except Exception:
            continue
    return None

# --- PDF helpers ---
def raster(svg_path, w=320):
    """Rasterize an SVG to PNG via the cairosvg CLI in a subprocess with a
    hard timeout. cairosvg can INFINITE-LOOP (not raise) on malformed
    gradient/href references, so we must time-box it; a hang => skip."""
    import subprocess
    png = svg_path.rsplit(".", 1)[0] + f"_r{w}.png"
    if os.path.exists(png) and os.path.getsize(png) > 0:
        return png
    try:
        subprocess.run(
            [sys.executable, "-m", "cairosvg", svg_path, "-o", png, "-W", str(w)],
            timeout=12, capture_output=True, check=False,
        )
    except (subprocess.TimeoutExpired, Exception):
        return None
    if os.path.exists(png) and os.path.getsize(png) > 0:
        return png
    return None

def _factoid_text(year, month, day):
    p = os.path.join(FAC, str(year), f"{year}-{month:02d}-{day:02d}.json")
    if os.path.exists(p):
        try:
            return json.load(open(p)).get("factoid_text","")
        except Exception:
            return ""
    return ""

def add_caption(pg, y, text, fontsize=9, maxw=78):
    """Wrap text into the page (simple char-wrap)."""
    words = text.split()
    line = ""
    for w in words:
        if len(line) + len(w) + 1 <= maxw:
            line = (line + " " + w).strip()
        else:
            pg.insert_text((60, y), line, fontsize=fontsize); y += 13
            line = w
    if line:
        pg.insert_text((60, y), line, fontsize=fontsize); y += 13
    return y

def make_magazine(year, month, day, cfg=None):
    import fitz
    cfg = cfg or CONFIG
    rnd = random.Random(f"{year}{month:02d}{day:02d}")
    date = datetime.date(year, month, day)
    key = f"{month:02d}-{day:02d}"
    evs = POOL.get(key, [])
    ev = rnd.choice(evs) if evs else None
    theme = cfg["locked_theme"] or rnd.choice(THEME_DIRS)
    factoid = _factoid_text(year, month, day)
    doc = fitz.open()
    # P1 cover
    pg = doc.new_page()
    pg.insert_text((60, 80), "SEYMOUR WINS", fontsize=34)
    pg.insert_text((60, 130), f"DAILY MAGAZINE — {date.isoformat()}", fontsize=16)
    pg.insert_text((60, 160), f"Theme: {theme}", fontsize=14)
    pg.insert_text((60, 200), "Create context, not control content.", fontsize=12)
    if ev:
        pg.insert_text((60, 230), f"On this day: {ev[0]}", fontsize=10)
    # P2 factoid (wired to the factoid engine output when present)
    pg = doc.new_page()
    pg.insert_text((60, 60), "FACTOID OF THE DAY", fontsize=18)
    if factoid:
        y = 96
        for line in factoid.splitlines()[:22]:
            if not line.strip():
                continue
            for chunk in [line[i:i+88] for i in range(0, len(line), 88)]:
                pg.insert_text((60, y), chunk, fontsize=9); y += 13
            if y > 740:
                break
    elif ev:
        y = 100
        for chunk in [ev[1][i:i+90] for i in range(0, len(ev[1]), 90)]:
            pg.insert_text((60, y), chunk, fontsize=11); y += 15
        pg.insert_text((60, 160), f"Stream lens ({theme}): the thread continues.", fontsize=11)
    pg.insert_text((60, 770), "The Colonel: create context, not control content.", fontsize=9)
    # P3 editorial (real issue text)
    iss = os.path.join(CAL, str(year), f"{month:02d}", f"{day:02d}.md")
    if os.path.exists(iss):
        txt = open(iss, errors="ignore").read()[:1800]
        pg = doc.new_page()
        pg.insert_text((60, 60), "EDITORIAL", fontsize=18)
        y = 100
        for line in txt.splitlines()[:48]:
            if not line.strip():
                continue
            pg.insert_text((60, y), line[:92], fontsize=9); y += 13
            if y > 760:
                break
    # P4 PUBLIC-DOMAIN DISPATCH (real Wikipedia image of the event subject, else themed clip)
    subj = None
    q = None
    if ev:
        subj = re.split(r"[:—-]", ev[1])[0].strip()
        q = " ".join(subj.split()[:6])
    img = wiki_pd_image(q, f"{year}{month}{day}") if q else None
    pg = doc.new_page()
    if img:
        pg.insert_text((60, 60), "PUBLIC DOMAIN DISPATCH", fontsize=18)
        pg.insert_image(fitz.Rect(60, 100, 360, 360), filename=img)
        pg.insert_text((60, 380), f"Subject: {q}", fontsize=9)
        pg.insert_text((60, 398), "Source: Wikipedia (public-domain / CC-licensed)", fontsize=8)
    else:
        fb = clip_for(theme, 1, seed=f"{year}{month}{day}pd")[0]
        pg.insert_text((60, 60), "DISPATCH (clipart)", fontsize=18)
        png = raster(fb, cfg["clip_dpi"]) if fb else None
        if png:
            pg.insert_image(fitz.Rect(60, 100, 360, 360), filename=png)
        pg.insert_text((60, 380), f"Theme: {theme} (CC0/public domain)", fontsize=9)
    # body: CLIP pages + PERSONA pages (fill to target_pages)
    clips = clip_for(theme, cfg["clips_per_day"], seed=f"{year}{month}{day}")
    for i, svg in enumerate(clips):
        pg = doc.new_page()
        png = raster(svg, cfg["clip_dpi"])
        if png:
            pg.insert_image(fitz.Rect(60, 80, 360, 360), filename=png)
        label = PROV.get(os.path.basename(svg), {}).get("label", "CC0 clipart")
        pg.insert_text((60, 400), f"CLIP {i+1}/{len(clips)} — {theme}", fontsize=12)
        pg.insert_text((60, 422), f"{label} (CC0/public domain)", fontsize=8)
        cap = THEME_LINES.get(theme, "Winds riding information: the thread continues.")
        add_caption(pg, 442, cap, fontsize=9)
    # PERSONA pages (the AI personalities)
    au_dir = os.path.join(CAL, str(year), f"{month:02d}", f"{day:02d}_au")
    personas = []
    if os.path.isdir(au_dir):
        allu = sorted(glob.glob(os.path.join(au_dir, "u_*.md")))
        rnd.shuffle(allu)
        personas = allu[:cfg["personas_per_day"]]
    for uf in personas:
        persona = os.path.basename(uf)[2:-3]
        body = open(uf, errors="ignore").read()
        # strip markdown bold markers for clean text
        clean = re.sub(r"\*\*", "", body)
        pg = doc.new_page()
        pg.insert_text((60, 60), f"AU PERSONA — {persona}", fontsize=16)
        y = 92
        for line in clean.splitlines()[:14]:
            if not line.strip():
                continue
            pg.insert_text((60, y), line[:92], fontsize=8); y += 12
            if y > 300:
                break
        pic = clip_for(persona if persona in THEME_DIRS else theme, 1, seed=persona)[0]
        png = raster(pic, cfg["clip_dpi"]) if pic else None
        if png:
            pg.insert_image(fitz.Rect(60, 330, 300, 560), filename=png)
        pg.insert_text((60, 590), "Speculative fiction forked from a verified anchor.", fontsize=8)
    out_dir = os.path.join(OUT, str(year)); os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, f"{year}-{month:02d}-{day:02d}.pdf")
    doc.save(out)
    return out, len(doc)

def main():
    ap = argparse.ArgumentParser(description="Seymour Wins magazine engine")
    ap.add_argument("years", nargs="*", help="year(s), or Y M D for one day")
    ap.add_argument("--pages", type=int, help="target pages (default 30)")
    ap.add_argument("--clips", type=int, help="clipart pages per day")
    ap.add_argument("--personas", type=int, help="persona pages per day")
    ap.add_argument("--no-wiki", action="store_true", help="disable Wikipedia images")
    ap.add_argument("--theme", help="lock a single theme")
    ap.add_argument("--dry", action="store_true", help="count only, build nothing")
    ap.add_argument("--stats", action="store_true",
                    help="measure Wikipedia PD hit-rate over the calendar (build nothing)")
    a = ap.parse_args()
    cfg = dict(CONFIG)
    if a.pages: cfg["target_pages"] = a.pages
    if a.clips: cfg["clips_per_day"] = a.clips
    if a.personas: cfg["personas_per_day"] = a.personas
    if a.no_wiki: cfg["use_wiki"] = False
    if a.theme: cfg["locked_theme"] = a.theme
    # keep body pages consistent with target
    body = cfg["target_pages"] - cfg["front_pages"]
    if a.clips is None and a.personas is None:
        cfg["personas_per_day"] = max(1, body - cfg["clips_per_day"])
    if a.dry:
        print(f"DRY: target={cfg['target_pages']} front={cfg['front_pages']} "
              f"clips={cfg['clips_per_day']} personas={cfg['personas_per_day']} "
              f"wiki={cfg['use_wiki']} theme={cfg['locked_theme']}")
        return
    if a.stats:
        years = [int(y) for y in a.years] if a.years else list(range(2020, 2027))
        total = hit = 0
        for y in years:
            for mm in range(1, 13):
                for dd in range(1, 32):
                    try: datetime.date(y, mm, dd)
                    except ValueError: continue
                    evs = POOL.get(f"{mm:02d}-{dd:02d}", [])
                    if not evs:
                        continue
                    total += 1
                    ev = random.Random(f"{y}{mm:02d}{dd:02d}").choice(evs)
                    subj = re.split(r"[:—-]", ev[1])[0].strip()
                    q = " ".join(subj.split()[:6])
                    if wiki_pd_image(q, f"{y}{mm}{dd}"):
                        hit += 1
        print(f"WIKI PD HIT-RATE: {hit}/{total} = {100*hit/total:.1f}% "
              f"(cache grows in pdf/magazine_imgs/)")
        return
    if len(a.years) == 3:
        make_magazine(int(a.years[0]), int(a.years[1]), int(a.years[2]), cfg)
        print("built one day")
        return
    years = [int(y) for y in a.years] if a.years else list(range(2020, 2027))
    for y in years:
        n = 0
        for mm in range(1, 13):
            for dd in range(1, 32):
                try: datetime.date(y, mm, dd)
                except ValueError: continue
                try:
                    make_magazine(y, mm, dd, cfg); n += 1
                except Exception as e:
                    print(f"  SKIP {y}-{mm:02d}-{dd:02d}: {e}")
        print(f"  {y}: {n} magazine PDFs -> pdf/magazine/{y}/", flush=True)

if __name__ == "__main__":
    main()
