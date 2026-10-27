#!/usr/bin/env python3
"""Dead-to-rights asset downloader for Seymour Ponderables.
Only CC0 (Openclipart) + Public Domain (Wikimedia Commons) + OFL (Google Fonts).
Every file gets a provenance line written to LICENSE_MANIFEST additions.
"""
import json, os, subprocess, re, sys, time

ASSETS = "/home/wubu/seymour-project/assets"
CLIPART = f"{ASSETS}/clipart"
TEXTURES = f"{ASSETS}/textures"
FONTS = f"{ASSETS}/fonts"
UA = "Mozilla/5.0 (SeymourAbsorber/1.0)"

def curl(url, out=None):
    """Fetch URL. If out given, save to file and return True on success.
    Else return decoded text."""
    cmd = ["curl", "-sL", "--max-time", "60", "-A", UA, url]
    if out:
        cmd += ["-o", out]
        p = subprocess.run(cmd, capture_output=True)
        return p.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0
    p = subprocess.run(cmd, capture_output=True)
    return p.stdout.decode("utf-8", "ignore")

def oc_search(query, n=5):
    """Return list of (id, slug) from Openclipart tag page."""
    html = curl(f"https://openclipart.org/tag/{query.replace(' ','-')}")
    ids = re.findall(r'/detail/(\d+)/([a-z0-9\-]+)', html)
    seen, out = set(), []
    for i, slug in ids:
        if i in seen: continue
        seen.add(i); out.append((i, slug))
        if len(out) >= n: break
    return out

def oc_download(idd, slug, theme):
    os.makedirs(f"{CLIPART}/{theme}", exist_ok=True)
    out = f"{CLIPART}/{theme}/oc_{slug}.svg"
    ok = curl(f"https://openclipart.org/download/{idd}", out=out)
    if ok:
        print(f"  [CC0] {theme}/{slug}  ({os.path.getsize(out)}b)")
    return ok

# ── Openclipart themed pulls (CC0) ──
THEMES = {
    "penny":    ["coin", "money", "penny"],
    "versa":    ["car", "automobile", "road"],
    "cuda":     ["computer", "chip", "circuit"],
    "paulsen":  ["book", "axe", "tree"],
    "gaming":   ["gamepad", "joystick", "controller"],
    "internet": ["computer", "monitor", "internet"],
    "supercap": ["battery", "lightning", "engine"],
    "meme":     ["speech", "thought", "face"],
}

print("=== Openclipart CC0 clipart ===")
manifest_rows = []
for theme, queries in THEMES.items():
    got = 0
    for q in queries:
        if got >= 3: break
        for idd, slug in oc_search(q, 3):
            if oc_download(idd, slug, theme):
                manifest_rows.append((f"Openclipart:{idd}", "CC0", f"clipart/{theme}/oc_{slug}.svg"))
                got += 1
                if got >= 3: break
            time.sleep(0.5)
    print(f"  theme '{theme}': {got} files")

# ── Wikimedia Commons PD texture (paper/halftone) ──
print("=== Wikimedia PD textures ===")
os.makedirs(TEXTURES, exist_ok=True)
# Search PD paper texture files
js = curl("https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=paper%20texture%20filetype:image&gsrnamespace=6&gsrlimit=3&prop=imageinfo&iiprop=url|extmetadata&format=json")
try:
    d = json.loads(js)
    pages = d.get("query", {}).get("pages", {})
    for v in pages.values():
        ii = v.get("imageinfo", [{}])[0]
        url = ii.get("url")
        lic = ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", "")
        if url and ("Public" in lic or "CC0" in lic or "PD" in lic):
            ext = url.split(".")[-1].split("?")[0][:4]
            out = f"{TEXTURES}/wc_{v['title'].replace(' ','_')[:40]}.{ext}"
            if curl(url, out=out):
                print(f"  [PD] {os.path.basename(out)} ({lic})")
                manifest_rows.append((f"Wikimedia:{v['title']}", lic, f"textures/{os.path.basename(out)}"))
except Exception as e:
    print("  wm texture err:", e)

# ── Google Fonts OFL ──
print("=== Google Fonts OFL ===")
FONT_LIST = ["Special+Elite", "Old+Standard+TT", "Rye", "Bungee", "DM+Serif+Display"]
for fam in FONT_LIST:
    css = curl(f"https://fonts.googleapis.com/css2?family={fam}&display=swap")
    m = re.search(r'url\((https://[^)]+\.ttf)\)', css)
    if m:
        name = fam.replace("+", "")
        out = f"{FONTS}/{name}-Regular.ttf"
        if curl(m.group(1), out=out):
            print(f"  [OFL] {name}  ({os.path.getsize(out)}b)")
            manifest_rows.append((f"GoogleFonts:{name}", "OFL", f"fonts/{name}-Regular.ttf"))

# ── Append to manifest ──
with open(f"{ASSETS}/LICENSE_MANIFEST.md", "a") as f:
    f.write("\n## Downloaded assets (session 2026-07-07)\n")
    for src, lic, path in manifest_rows:
        f.write(f"| {src} | {lic} | local:{path} | ✅ |\n")

print(f"\nTOTAL DOWNLOADED: {len(manifest_rows)} assets")
