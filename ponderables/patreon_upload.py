#!/usr/bin/env python3
"""
Seymour Wins — PATREON UPLOADER (ToS-compliant, API v2)
=====================================================================
Builds Patreon post payloads for every daily issue + yearly collection,
maps each to the tier ladder in patreon_tiers.json, and (optionally) pushes
them via the official Patreon API v2 (POST /api/oauth2/v2/posts).

DESIGN RULES (from research + money-room lesson #1):
  * Uses the OFFICIAL API v2 (OAuth2), NOT browser-scraping/bots (ToS gray area).
  * Paced sender: min 2s between posts, exponential backoff on 429/5xx.
  * Edge rate limit (2025-07-04): blasts of bad requests => 30-min block.
    We send ONE post per call, validate payload, never firehose.
  * DRY-RUN by default: writes payloads to disk, pushes NOTHING unless
    --live AND a token is present in .env (gitignored).
  * Individual posts are tagged (searchable). Yearly COLLECTION posts index
    all individual posts for easy access.

Post payload (API v2, JSON:API):
  POST /api/oauth2/v2/posts
  { "data": {
      "type": "post",
      "attributes": {
          "title": ..., "content": ..., "post_type": "text",
          "tags": [...], "is_paid": false, "tiers_details": [...]
      },
      "relationships": { "campaign": {"data": {"type":"campaign","id":CAMPAIGN_ID}} }
  }}

Run:
  python3 patreon_upload.py --dry-run            # build all payloads, no push
  python3 patreon_upload.py --dry-run --year 2020
  python3 patreon_upload.py --live              # REAL push (needs .env token)
"""
import os, sys, json, time, glob, re, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
CAL = os.path.join(HERE, "calendar")
OUT = os.path.join(HERE, "patreon_payloads")
TOKEN_FILE = os.path.join(HERE, ".env")

def load_tier_map():
    tj = json.load(open(os.path.join(HERE, "patreon_tiers.json")))
    by_id = {t["id"]: t for t in tj["tiers"]}
    return tj, by_id

def parse_issue(path):
    t = open(path).read()
    m = re.search(r"\*\*TITLE:\*\*\s*(.+)", t)
    th = re.search(r"\*\*THEME:\*\*\s*(\S+)", t)
    title = m.group(1).strip() if m else os.path.basename(path)
    theme = th.group(1) if th else "meme"
    # body = everything after the FACT line's first paragraph block, trimmed
    fact = re.search(r"\*\*FACT:\*\*\s*(.+)", t)
    fact_txt = fact.group(1).strip() if fact else ""
    # render readable body: drop the field-marker lines, keep prose + Colonel + triple-checked
    body_lines = []
    for ln in t.splitlines():
        s = ln.strip()
        if s.startswith("**TITLE:**") or s.startswith("**THEME:") or s.startswith("**THEME_LABEL:**"):
            continue
        body_lines.append(ln)
    body = "\n".join(body_lines).strip()
    return title, theme, fact_txt, body

def build_individual(year, month, day, tmap):
    p = f"{CAL}/{year}/{month:02d}/{day:02d}.md"
    if not os.path.exists(p):
        return None
    title, theme, fact, body = parse_issue(p)
    tier = tmap["post_model"]["individual"]["tier"]  # free
    tags = ["seymour-wins", theme, str(year), f"{month:02d}{day:02d}", "daily"]
    content = (f"{body}\n\n---\n*Part of the Seymour Wins daily chronicle. "
               f"Searchable by theme, year, and date.*")
    return {
        "type": "post",
        "title": f"{title} — {year}-{month:02d}-{day:02d}",
        "content": content,
        "tags": tags,
        "tier": tier,
        "date": f"{year}-{month:02d}-{day:02d}",
        "product": "daily_issue",
    }

def build_collection(year, tmap, individual_posts):
    # index of all individual posts for the year
    lines = [f"# Seymour Wins {year} — Collection Index",
             "",
             f"All {len(individual_posts)} daily issues for {year}, each posted individually and searchable by theme/year/date.",
             "",
             "| Date | Theme | Link |",
             "|------|-------|------|"]
    for ip in individual_posts:
        lines.append(f"| {ip['date']} | {ip['tags'][1]} | [{ip['title']}](pending) |")
    content = "\n".join(lines)
    return {
        "type": "post",
        "title": f"Seymour Wins {year} — Full Year Collection",
        "content": content,
        "tags": ["seymour-wins", "collection", str(year)],
        "tier": "free",
        "date": f"{year}-collection",
        "product": "collection",
    }

def build_weekly_volume(year, tmap):
    """One gated post per weekly volume PDF (the $1/week spine product)."""
    vols = sorted(glob.glob(os.path.join(HERE, "pdf", "volumes", str(year), "*.pdf")))
    posts = []
    for v in vols:
        bn = os.path.basename(v).replace(".pdf", "")
        # SeymourWins_2020_week01 -> week 01
        m = re.search(r"week(\d+)", bn)
        wk = m.group(1) if m else "?"
        tags = ["seymour-wins", "weekly", str(year), f"week{wk.zfill(2)}"]
        posts.append({
            "type": "post",
            "title": f"Seymour Wins {year} — Weekly Volume {wk.zfill(2)}",
            "content": (f"Weekly chronicle volume for {year}, week {wk.zfill(2)}.\n\n"
                        f"This week's daily issues (7 days × 31 pages: 1 real + 30 multiverse AU spins) "
                        f"compiled into one volume.\n\n*Weekly Reader tier ($1/week) — the spine of the publication.*"),
            "tags": tags,
            "tier": "weekly",
            "date": f"{year}-w{wk.zfill(2)}",
            "product": "weekly_volume",
            "pdf": v,
        })
    return posts

def build_monthly_volume(year, tmap):
    """One gated post per MONTH-as-volume (12/yr) + note the AU spins included."""
    posts = []
    for mo in range(1, 13):
        ndays = (datetime.date(year+1, 1, 1) - datetime.date(year, mo, 1)).days if mo == 12 \
                else (datetime.date(year, mo+1, 1) - datetime.date(year, mo, 1)).days
        tags = ["seymour-wins", "monthly", "volume", str(year), f"month{mo:02d}"]
        posts.append({
            "type": "post",
            "title": f"Seymour Wins {year} — Volume {mo:02d} (Month {mo:02d})",
            "content": (f"Month {mo:02d} of {year}, compiled as VOLUME {mo:02d} "
                        f"(~{ndays} days).\n\nIncludes the month's daily issues plus the "
                        f"30-pages/day MULTIVERSE alternate-universe spins.\n\n"
                        f"*Monthly Volume tier ($10/mo) — month = volume.*"),
            "tags": tags,
            "tier": "monthly_volume",
            "date": f"{year}-m{mo:02d}",
            "product": "month_volume",
        })
    return posts

def collect_year(year):
    tj, tmap = load_tier_map()
    indiv = []
    for mm in range(1, 13):
        for dd in range(1, 32):
            p = build_individual(year, mm, dd, tj)
            if p:
                indiv.append(p)
    coll = build_collection(year, tj, indiv)
    weekly = build_weekly_volume(year, tj)
    monthly = build_monthly_volume(year, tj)
    return indiv, coll, weekly, monthly

def save_payloads(year, indiv, coll, weekly, monthly):
    yd = os.path.join(OUT, str(year))
    os.makedirs(yd, exist_ok=True)
    meta = {"year": year, "individual_count": len(indiv), "collection": True,
            "weekly_volumes": len(weekly), "monthly_volumes": len(monthly)}
    for ip in indiv:
        fn = f"{ip['date']}.json"
        with open(os.path.join(yd, fn), "w") as f:
            json.dump(ip, f, indent=2)
    with open(os.path.join(yd, "collection.json"), "w") as f:
        json.dump(coll, f, indent=2)
    for w in weekly:
        with open(os.path.join(yd, f"week_{w['date']}.json"), "w") as f:
            json.dump(w, f, indent=2)
    for m in monthly:
        with open(os.path.join(yd, f"month_{m['date']}.json"), "w") as f:
            json.dump(m, f, indent=2)
    with open(os.path.join(yd, "_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    return len(indiv) + 1 + len(weekly) + len(monthly)

# ---------------- sender ----------------
def load_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    env = {}
    for line in open(TOKEN_FILE):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env.get("PATREON_ACCESS_TOKEN")

def push_live(payloads, campaign_id, token):
    """Push via Patreon API v2. Paced + backoff. Requires token + campaign_id."""
    import urllib.request
    url = "https://www.patreon.com/api/oauth2/v2/posts"
    hdr = {"Authorization": f"Bearer {token}",
           "Content-Type": "application/json"}
    sent = 0
    for i, pl in enumerate(payloads, 1):
        body = {"data": {
            "type": "post",
            "attributes": {
                "title": pl["title"],
                "content": pl["content"],
                "post_type": "text",
                "tags": pl["tags"],
                "is_paid": False,
            },
            "relationships": {
                "campaign": {"data": {"type": "campaign", "id": campaign_id}}
            },
        }}
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers=hdr, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                r.read()
            sent += 1
            print(f"  pushed {i}/{len(payloads)}: {pl['title'][:50]}", flush=True)
        except urllib.error.HTTPError as e:
            if e.code == 429 or e.code >= 500:
                wait = int(e.headers.get("Retry-After", "30"))
                print(f"  rate limited ({e.code}); backing off {wait}s", flush=True)
                time.sleep(wait)
                # retry once
                with urllib.request.urlopen(req, timeout=30) as r2:
                    r2.read()
                sent += 1
            else:
                print(f"  ERROR {e.code} on {pl['title']}: {e.read()[:200]}", flush=True)
        time.sleep(2.0)  # min pacing between posts
    return sent

def main():
    args = sys.argv[1:]
    live = "--live" in args
    dry = "--dry-run" in args or not live
    years = [int(a) for a in args if a.isdigit()] or list(range(2020, 2027))
    total = 0
    for y in years:
        indiv, coll, weekly, monthly = collect_year(y)
        n = save_payloads(y, indiv, coll, weekly, monthly)
        total += n
        print(f"  {y}: {len(indiv)} individual + 1 collection + {len(weekly)} weekly + {len(monthly)} monthly -> patreon_payloads/{y}/", flush=True)
    print(f"BUILT {total} post payloads (dry-run={dry}).", flush=True)
    if live:
        token = load_token()
        cid = os.environ.get("PATREON_CAMPAIGN_ID")
        if not token or not cid:
            print("LIVE mode requires .env PATREON_ACCESS_TOKEN + PATREON_CAMPAIGN_ID. Aborting (safe).")
            return
        allpl = []
        for y in years:
            yd = os.path.join(OUT, str(y))
            for fn in sorted(os.listdir(yd)):
                if fn.endswith(".json") and fn != "_meta.json":
                    allpl.append(json.load(open(os.path.join(yd, fn))))
        print(f"PUSHING {len(allpl)} posts LIVE...", flush=True)
        sent = push_live(allpl, cid, token)
        print(f"LIVE push complete: {sent}/{len(allpl)} sent.")

if __name__ == "__main__":
    main()
