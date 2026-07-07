#!/usr/bin/env python3
"""
Seymour Wins — CC0 CLIPART ACQUIRER v4 (OpenGameArt CC0 manifest + freesvg CC0)

Sources (ALL dead-to-rights CC0 / public domain):
  1. OpenGameArt CC0 HuggingFace dataset: 29 manifests (2D_Art_00..28.jsonl.zst),
     each record carries a `licenses: ['CC0']` flag. We take CC0 records, pull
     direct .svg file URLs, AND download .zip records and extract embedded .svg.
  2. freesvg.org: explicit CC0 (license page links creativecommons.org/publicdomain/zero).
     We scrape tag pages for item URLs, then each item page for its download.

Every saved file recorded in assets/clipart/PROVENANCE.json with source + license.

Usage:
  python3 acquire_clipart.py                 # all themes
  python3 acquire_clipart.py penny           # one theme
  python3 acquire_clipart.py --quarantine    # move unprovenanced files out
"""
import os, re, json, sys, subprocess, glob, io

ROOT = "/home/wubu/seymour-project"
CLIP = f"{ROOT}/assets/clipart"
PROV = f"{CLIP}/PROVENANCE.json"
QUAR = f"{CLIP}/_quarantine"
MANI = "/tmp/oga_manifests"

# theme -> keyword substrings (lowercased) matched against title+tags+filename
THEME_KW = {
    "penny":    ["coin", "penny", "money", "cent", "currency", "cash", "gold", "bank", "dollar", "euro", "piggy", "treasure", "gem", "diamond"],
    "supercap": ["battery", "energy", "power", "capacitor", "solar", "engine", "lightning", "electric", "fuel", "charge", "bolt", "reactor", "generator"],
    "versa":    ["car", "truck", "vehicle", "bus", "automobile", "road", "wheel", "bike", "bicycle", "motorcycle", "train", "plane", "ship", "boat", "helicopter", "tire", "traffic"],
    "gaming":   ["game", "controller", "joystick", "arcade", "console", "pixel", "rpg", "character", "sprite", "avatar", "enemy", "monster", "hero", "player", "wizard", "sword", "shield"],
    "cuda":     ["computer", "cpu", "chip", "server", "robot", "monitor", "keyboard", "mouse", "circuit", "processor", "tech", "screen", "terminal", "code", "ai", "drone"],
    "internet": ["internet", "web", "wifi", "network", "social", "browser", "cloud", "signal", "antenna", "globe", "link", "share", "mail", "phone", "chat"],
    "paulsen":  ["book", "tree", "forest", "mountain", "nature", "leaf", "plant", "river", "lake", "camp", "tent", "compass", "map", "animal", "bird", "fish", "wolf", "bear", "wilderness"],
    "meme":     ["smiley", "emoji", "face", "laugh", "symbol", "sign", "star", "heart", "speech", "bubble", "meme", "icon", "badge", "banner", "explosion", "spark", "crown", "skull"],
    "metalgear": ["snake", "codec", "cyborg", "soldier", "stealth", "ninja", "exoskeleton", "helmet", "tactical", "radar", "cardboard", "bandana"],
    "gun":      ["gun", "weapon", "rifle", "pistol", "sword", "shield", "crossbow", "cannon", "missile", "bomb", "armor", "war"],
    "colonel":  ["eye", "camera", "surveillance", "broadcast", "antenna", "microphone", "radio", "screen", "television", "satellite", "control"],
    "brain":    ["brain", "mind", "thought", "idea", "neural", "head", "intelligence", "consciousness"],
    "flag":     ["flag", "banner", "emblem", "seal", "crest", "shield"],
    "sky":      ["moon", "sun", "star", "cloud", "storm", "lightning", "rain", "snow", "weather", "planet", "space", "comet"],
    "book":     ["book", "scroll", "manuscript", "library", "page", "quill", "letter", "document", "newspaper", "press"],
    "key":      ["key", "lock", "door", "treasure", "chest", "safe", "vault"],
}
PER_THEME_TARGET = 125
UA = "Mozilla/5.0 (SeymourWins CC0 clipart acquirer; toilet-book) curl/8"

provenance = {}
if os.path.exists(PROV):
    try:
        provenance = json.load(open(PROV))
    except Exception:
        provenance = {}


def slugify(s):
    s = s.lower().replace("file:", "").replace(" ", "-")
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s[:45] or "art"


def cur_count(theme):
    d = f"{CLIP}/{theme}"
    return len([f for f in os.listdir(d) if f.endswith('.svg')]) if os.path.isdir(d) else 0


def save_bytes(theme, data, label, source, lic="CC0/PublicDomain"):
    d = f"{CLIP}/{theme}"
    os.makedirs(d, exist_ok=True)
    n = cur_count(theme)
    fn = f"oc_{slugify(label)}_{n:03d}.svg"
    path = f"{d}/{fn}"
    if os.path.exists(path):
        return False
    try:
        open(path, "wb").write(data)
        if b"<svg" not in data[:500] and b"<?xml" not in data[:500]:
            os.remove(path); return False
        if len(data) < 200:
            os.remove(path); return False
        provenance[fn] = {"theme": theme, "source": source, "license": lic, "label": label}
        json.dump(provenance, open(PROV, "w"), indent=2)
        return True
    except Exception:
        if os.path.exists(path):
            os.remove(path)
        return False


def theme_of(text):
    t = text.lower()
    hits = [th for th, kws in THEME_KW.items() if any(k in t for k in kws)]
    return hits  # may be multiple; caller distributes


def process_manifests():
    """Yield (title, theme_list, file_entries) for CC0 records."""
    import zstandard
    for mf in sorted(glob.glob(f"{MANI}/*.jsonl.zst")):
        try:
            raw = open(mf, "rb").read()
            dctx = zstandard.ZstdDecompressor()
            text = dctx.stream_reader(io.BytesIO(raw)).read().decode("utf-8", "replace")
        except Exception:
            continue
        for ln in text.strip().split("\n"):
            if not ln.strip():
                continue
            try:
                r = json.loads(ln)
            except Exception:
                continue
            if "CC0" not in r.get("licenses", []):
                continue
            blob = (r.get("title", "") + " " + " ".join(r.get("tags", [])) + " "
                    + " ".join(f.get("name", "") for f in r.get("files", [])))
            ths = theme_of(blob)
            if not ths:
                continue
            yield r.get("title", "oga"), ths, r.get("files", []), r.get("url", "")


def acquire_from_oga():
    """Download DIRECT .svg files from CC0 records, then extract SVGs from a
    bounded number of CC0 .zip records to top each theme toward PER_THEME_TARGET."""
    print("--- OpenGameArt CC0 manifest scan (direct SVGs + bounded zip extraction) ---")
    added = 0
    seen_urls = set()
    # PASS 1: direct svg files
    for title, ths, files, page in process_manifests():
        if cur_count_reached():
            break
        for f in files:
            name = f.get("name", "")
            url = f.get("url", "")
            if not url or not name.lower().endswith(".svg"):
                continue
            if url in seen_urls:
                continue
            seen_urls.add(url)
            if cur_count_reached():
                break
            for th in ths:
                if cur_count(th) >= PER_THEME_TARGET:
                    continue
                r = subprocess.run(["curl", "-sL", "--max-time", "20", "-A", UA, url],
                                   capture_output=True)
                if save_bytes(th, r.stdout, title, url):
                    added += 1
    # PASS 2: bounded zip extraction (max ZIP_BUDGET zips per theme still under target)
    ZIP_BUDGET = 400
    zip_tried = {t: 0 for t in THEME_KW}
    for title, ths, files, page in process_manifests():
        if cur_count_reached():
            break
        for f in files:
            name = f.get("name", "")
            url = f.get("url", "")
            if not url or not name.lower().endswith(".zip"):
                continue
            # only extract for themes still under target and within budget
            ths_under = [t for t in ths if cur_count(t) < PER_THEME_TARGET]
            if not ths_under:
                continue
            if all(zip_tried[t] >= ZIP_BUDGET for t in ths_under):
                continue
            for t in ths_under:
                zip_tried[t] += 1
            r = subprocess.run(["curl", "-sL", "--max-time", "30", "-A", UA, url],
                               capture_output=True)
            try:
                z = zipfile.ZipFile(io.BytesIO(r.stdout))
                for zn in z.namelist():
                    if not zn.lower().endswith(".svg"):
                        continue
                    for th in ths_under:
                        if cur_count(th) >= PER_THEME_TARGET:
                            continue
                        data = z.read(zn)
                        if save_bytes(th, data, title + "-" + zn.split("/")[-1][:18], url):
                            added += 1
                    if cur_count_reached():
                        break
            except Exception:
                pass
    return added


def cur_count_reached():
    return all(cur_count(t) >= PER_THEME_TARGET for t in THEME_KW)


# ---- freesvg CC0 fallback ----
FREESVG_TAGS = {
    "penny":    ["money", "coin", "gold", "bank"],
    "supercap": ["energy", "battery", "lightning", "power"],
    "versa":    ["car", "truck", "bus", "vehicle", "road", "bicycle"],
    "gaming":   ["game", "joystick", "controller", "arcade"],
    "cuda":     ["computer", "robot", "technology", "monitor"],
    "internet": ["internet", "wifi", "social", "web", "phone"],
    "paulsen":  ["tree", "forest", "mountain", "book", "nature", "animal"],
    "meme":     ["smiley", "emoji", "symbol", "star", "heart", "face"],
}


def freesvg_item_svg(item_url):
    """Return raw svg bytes from a freesvg item page if directly available."""
    try:
        r = subprocess.run(["curl", "-s", "--max-time", "20", "-A", UA, item_url],
                           capture_output=True, text=True)
        m = re.search(r'href="([^"]+\.svg)"', r.stdout)
        if m:
            u = m.group(1)
            if u.startswith("/"):
                u = "https://freesvg.org" + u
            rr = subprocess.run(["curl", "-sL", "--max-time", "20", "-A", UA, u],
                                capture_output=True)
            if b"<svg" in rr.stdout[:500]:
                return rr.stdout, u
    except Exception:
        pass
    return None, None


def acquire_from_freesvg():
    print("--- freesvg.org CC0 scan ---")
    added = 0
    for th, tags in FREESVG_TAGS.items():
        if cur_count(th) >= PER_THEME_TARGET:
            continue
        for tag in tags:
            if cur_count(th) >= PER_THEME_TARGET:
                break
            try:
                r = subprocess.run(["curl", "-s", "--max-time", "20", "-A", UA,
                                    f"https://freesvg.org/tag/{tag}"], capture_output=True, text=True)
                items = re.findall(r'href="(https://freesvg\.org/[^"]+)"', r.stdout)
                items = [i for i in items if not i.endswith(("/tag/" + tag))]
            except Exception:
                items = []
            for it in items:
                if cur_count(th) >= PER_THEME_TARGET:
                    break
                data, src = freesvg_item_svg(it)
                if data:
                    if save_bytes(th, data, it.split("/")[-1], src, lic="CC0/freesvg"):
                        added += 1
    return added


def quarantine_unprovenanced():
    os.makedirs(QUAR, exist_ok=True)
    moved = 0
    for t in list(THEME_KW.keys()):
        d = f"{CLIP}/{t}"
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if f.endswith(".svg") and f not in provenance:
                try:
                    os.rename(f"{d}/{f}", f"{QUAR}/{t}__{f}")
                    moved += 1
                except Exception:
                    pass
    print(f"quarantined {moved} unprovenanced files -> {QUAR}")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--quarantine":
        quarantine_unprovenanced()
        return
    a = acquire_from_oga()
    print(f"OGA added: {a}")
    b = acquire_from_freesvg()
    print(f"freesvg added: {b}")
    print("\n=== SUMMARY ===")
    total = 0
    for t in THEME_KW:
        c = cur_count(t); total += c
        print(f"  {t}: {c}")
    print(f"  TOTAL CC0/PD: {total} SVGs | provenance entries: {len(provenance)}")


if __name__ == "__main__":
    main()
