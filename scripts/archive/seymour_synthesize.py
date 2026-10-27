#!/usr/bin/env python3
"""
seymour_synthesize.py — Presynth → Ponderable bridge.

Reads presynth cluster summaries and synthesizes Seymour Ponderable entries
(published/ directory). Uses llama-server when available, with template
fallback for offline/backlog mode.

Usage:
  # Process a specific cluster (LLM mode)
  python3 scripts/seymour_synthesize.py "Artificial Intelligence"

  # Process all clusters (batch mode)
  python3 scripts/seymour_synthesize.py --all

  # Template-only (no LLM) — fast backlog generation
  python3 scripts/seymour_synthesize.py --all --template-only

  # Pipeline integration
  python3 scripts/seymour_synthesize.py --query "marvel rivals" --limit 2

Output: ponderables/published/p{NNN}_{slug}.md
"""

import json
import re
import sys
import time
import subprocess
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime
from string import Template

BASE = Path("/home/wubu/seymour-project")
PRESYNTH_DIR = BASE / "pre_seymour" / "presynth"
PUBLISHED_DIR = BASE / "ponderables" / "published"
VOL1_DIR = BASE / "ponderables" / "vol-1"
WIKI_DIR = BASE / "ponderables" / "wiki"
LOGS = BASE / "logs"
LOGS.mkdir(exist_ok=True)

LLAMA_URL = "http://localhost:18802/completion"
NEXT_NUMBER_FILE = PUBLISHED_DIR / ".next_number"

# ── Entry template (matches entry-001.md style) ──
PONDERABLE_TEMPLATE = Template("""# SEYMOUR PONDERABLES Vol. 1: The Mimetic War
## Entry ${number}: ${title}

---

[CLIPART: ${clipart_placeholder}]

---

${body}

---

> "${colonel_quote}"
> — The Colonel, MGS2

---

↳ See also: ${see_also}
↳ Related: _${related}_

---

SEYMOUR PONDERABLES | Vol. 1: The Mimetic War | Pg. ${page}

*Generated from presynth cluster "${cluster_name}"*
*${video_count} videos across ${span}*
*Synthesis date: ${date}*
""")

# ── Colonel quotes pool ──
COLONEL_QUOTES = [
    "What we propose to do is not to control content, but to create context.",
    "Unnecessary information must be filtered out to stimulate the evolution of the species.",
    "A memetic weapon designed to subdue and control the public consciousness.",
    "The value of information does not survive the moment in which it was new.",
    "We are not merely preserving the past — we are curating the future.",
    "Each datum wants to live forever. Most don't deserve to.",
    "The simulation is self-correcting. The noise will be filtered.",
    "You cannot kill a meme. You can only hope to contain it.",
    "Information wants to be free. But free information wants to be curated.",
    "In the digital ocean, only the loudest memes survive.",
    "What is a man but a collection of memes that have learned to walk?",
    "The truth is not a destination. It is a filter.",
]

CLIPART_PLACEHOLDERS = [
    "A hand-drawn floppy disk labeled 'MEMES' with a question mark over it",
    "A grainy screenshot of a CRT monitor displaying the WuBu stream archive",
    "A clipart brain plugged into a USB cable, wires trailing into a PC tower",
    "A copper penny resting on asphalt, wheat side up, slightly scratched",
    "A row of 90s-era folder icons labeled 'VIDEOS', 'MEMES', 'TRANSCRIPTS', 'PENNIES'",
    "An antique projector showing a frame from Death Stranding 2",
    "A stick-figure character labeled 'WuBu' holding a controller in each hand",
    "A clipart trash can overflowing with floppy disks, each labeled 'forgotten meme'",
    "A VHS tape with a handwritten label: 'CLUSTER: ARTIFICIAL INTELLIGENCE'",
    "A bronze medal with the word 'PENNY' stamped on it sitting on a stack of papers",
    "A clipart magnifying glass hovering over a YouTube search bar",
    "A diagram of a neural network where each node is a 90s clipart image",
    "A clipart hourglass with pennies instead of sand",
    "An old TV set displaying a blue error screen, text reading 'MEME NOT FOUND'",
    "A hand reaching into a jumble of cables labeled 'context collapse'",
    "A clipart globe with pushpins marking every penny found on a map",
    "A cassette tape with the label 'PRE-SEYMOUR INDEX — 408 ENTRIES'",
    "A clipart camera pointed at a mirror showing a screen showing the camera",
]


def get_next_number():
    """Get the next ponderable entry number."""
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    if NEXT_NUMBER_FILE.exists():
        n = int(NEXT_NUMBER_FILE.read_text().strip())
    else:
        # Count existing entries
        existing = list(PUBLISHED_DIR.glob("p*.md"))
        if existing:
            nums = []
            for f in existing:
                m = re.match(r"p(\d+)_", f.name)
                if m:
                    nums.append(int(m.group(1)))
            n = max(nums) + 1 if nums else 1
        else:
            n = 1
    NEXT_NUMBER_FILE.write_text(str(n + 1))
    return n


def slugify(text):
    """Convert text to URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:48]


def check_llama():
    """Check if llama-server is running."""
    try:
        req = urllib.request.Request(LLAMA_URL, method="POST")
        req.add_header("Content-Type", "application/json")
        data = json.dumps({"prompt": "test", "n_predict": 1, "temperature": 0.0}).encode()
        resp = urllib.request.urlopen(req, data=data, timeout=5)
        return resp.status == 200
    except Exception:
        return False


def llm_generate(prompt, max_tokens=600, temperature=0.7):
    """Generate text via llama-server."""
    if not check_llama():
        return None

    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "repeat_penalty": 1.1,
        "stop": ["</ponderable>", "\n\n\n"],
        "cache_prompt": True,
    }

    try:
        req = urllib.request.Request(LLAMA_URL, method="POST")
        req.add_header("Content-Type", "application/json")
        data = json.dumps(payload).encode()
        resp = urllib.request.urlopen(req, data=data, timeout=120)
        result = json.loads(resp.read().decode())
        text = result.get("content", "").strip()
        return text if text else None
    except Exception as e:
        print(f"  [LLM ERROR] {e}")
        return None


def load_cluster(name):
    """Load a presynth cluster file by name."""
    # Normalize name to filename
    slug = slugify(name)
    candidates = list(PRESYNTH_DIR.glob(f"cluster_{slug}*"))
    candidates += list(PRESYNTH_DIR.glob(f"cluster_{name.lower().replace(' ', '_')}*"))

    for f in candidates:
        if f.suffix == ".md":
            return f.read_text()

    return None


def parse_cluster(text):
    """Extract structured data from a cluster markdown file."""
    result = {}

    # Title
    m = re.search(r'^# (.+)', text)
    result["title"] = m.group(1).strip() if m else "Unknown Cluster"

    # Video count
    m = re.search(r'covers (\d+) videos?', text)
    result["video_count"] = int(m.group(1)) if m else 0

    # Year span
    years = re.findall(r'(\d{4})', text)
    if years:
        years = sorted(set(int(y) for y in years))
        result["span"] = f"{years[0]}–{years[-1]}"
    else:
        result["span"] = "unknown"

    # Overview (first paragraph after title)
    m = re.search(r'\*\*Overview:\*\* (.+?)\n\n', text)
    result["overview"] = m.group(1).strip() if m else ""

    # Extract multi-perspective sections
    perspectives = {}
    current_role = None
    for line in text.split("\n"):
        m = re.match(r'\*(\w+(?:\s+\w+)*)\s*\((\w+(?:\s+\w+)*)\)\s*\(([\d.]+)\)[:\*]?\s*(.*)', line)
        if m:
            role = m.group(1).strip()
            perspective = m.group(2).strip()
            confidence = m.group(3).strip()
            content = m.group(4).strip()
            key = f"{role}_{perspective}_{confidence}"
            perspectives[key] = content
        else:
            m2 = re.match(r'## (.+)', line)
            if m2:
                current_role = m2.group(1).strip()

    result["perspectives"] = perspectives

    # Topics from the cluster content
    m = re.search(r'Primary games and topics: (.+?)(?:\.|Content formats)', text)
    result["topics_str"] = m.group(1).strip() if m else ""

    return result


def synthesize_ponderable(cluster_name, template_only=False):
    """Generate a ponderable entry from a presynth cluster."""
    raw = load_cluster(cluster_name)
    if not raw:
        print(f"  ✗ Cluster '{cluster_name}' not found")
        return None

    data = parse_cluster(raw)
    print(f"  📦 {data['title']} ({data['video_count']} videos, {data['span']})")

    number = get_next_number()
    slug = slugify(data['title'])
    page = number * 2  # ~2 pages per entry
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Pick clipart and quote
    clipart = CLIPART_PLACEHOLDERS[number % len(CLIPART_PLACEHOLDERS)]
    quote = COLONEL_QUOTES[number % len(COLONEL_QUOTES)]

    # Generate body
    if template_only or not check_llama():
        body = _template_body(data)
    else:
        body = _llm_body(data, cluster_name)
        if not body:
            body = _template_body(data)

    # Build cross-refs
    see_also = ", ".join([
        f"Entry #{max(1, number - 1)}, \"The Previous Thing\"",
        f"Entry #{number + 1}, \"The Next Thing\"",
    ])
    related = f"Seymour's Encyclopedia of Internet Culture, Vol. {1 + (number % 5)}"

    # Render
    output = PONDERABLE_TEMPLATE.substitute(
        number=number,
        title=data['title'],
        clipart_placeholder=clipart,
        body=body,
        colonel_quote=quote,
        see_also=see_also,
        related=related,
        page=page,
        cluster_name=data['title'],
        video_count=data['video_count'],
        span=data['span'],
        date=date_str,
    )

    # Write
    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PUBLISHED_DIR / f"p{number:03d}_{slug}.md"

    # Check for existing content to avoid overwriting
    if out_path.exists():
        existing = out_path.read_text()
        if "Generated from presynth cluster" in existing:
            print(f"  ⏭️  Already exists: {out_path.name}")
            return out_path

    out_path.write_text(output)
    print(f"  ✅ Written: {out_path.name}")
    return out_path


def _template_body(data):
    """Generate body text without LLM (template fallback)."""
    title = data['title']
    overview = data['overview']
    count = data['video_count']

    # Pick the best archivist perspective (1.0 confidence) for factual content
    archivist_keys = [k for k in data['perspectives'] if 'archivist' in k.lower() and '1.0' in k]
    critic_keys = [k for k in data['perspectives'] if 'critic' in k.lower() and '1.0' in k]
    fan_keys = [k for k in data['perspectives'] if 'fan' in k.lower() and '1.0' in k]

    archivist_view = data['perspectives'].get(archivist_keys[0], "") if archivist_keys else ""
    critic_view = data['perspectives'].get(critic_keys[0], "") if critic_keys else ""
    fan_view = data['perspectives'].get(fan_keys[0], "") if fan_keys else ""

    body_parts = []

    # Opening allegorical paragraph
    body_parts.append(
        f"There is a folder somewhere on a hard drive. It contains {count} files — "
        f"video recordings of someone playing games, talking to themselves, processing "
        f"the world through a controller and a microphone. The folder is called "
        f"\"{title}\" and it represents approximately {count * 20} minutes of "
        f"consciousness, compressed, archived, waiting."
    )

    # The factual core
    if archivist_view:
        body_parts.append(archivist_view)
    elif overview:
        body_parts.append(overview)

    # The tension (critic vs fan)
    body_parts.append("")

    if critic_view:
        body_parts.append(f"The critic would say: {critic_view[:300]}")
    if fan_view:
        body_parts.append(f"The fan would say: {fan_view[:300]}")

    # The philosophical framing
    body_parts.append("")
    body_parts.append(
        f"The {title} cluster is not really about {title.lower()}. "
        f"It is about what it means to document something — to record yourself "
        f"engaging with a digital artifact, to preserve that moment, and to release "
        f"it into a stream of other moments. Every video is a time capsule. Every "
        f"transcript is a fossil. The question is not whether the content is "
        f"\"good\" — the question is what survives, and why, and who is left to "
        f"remember it."
    )

    # Topics
    if data.get('topics_str'):
        body_parts.append("")
        body_parts.append(f"*Topics: {data['topics_str']}*")

    return "\n\n".join(body_parts)


def _llm_body(data, cluster_name):
    """Generate body text using llama-server."""
    # Build concise context from the best perspectives
    archivist_keys = [k for k in data['perspectives'] if 'archivist' in k.lower() and '1.0' in k]
    critic_keys = [k for k in data['perspectives'] if 'critic' in k.lower() and '1.0' in k]
    fan_keys = [k for k in data['perspectives'] if 'fan' in k.lower() and '1.0' in k]
    arch = data['perspectives'].get(archivist_keys[0], data.get('overview', ''))[:300] if archivist_keys else data.get('overview', '')[:300]
    crit = data['perspectives'].get(critic_keys[0], '')[:200] if critic_keys else ''
    fan_persp = data['perspectives'].get(fan_keys[0], '')[:200] if fan_keys else ''

    prompt = f"""<s><|system|>
You are Seymour, philosopher-archivist of the memetic age. Write ONE ponderable paragraph (100-150 words) about what the "{cluster_name}" YouTube archive cluster MEANS — not what it contains.

Style: Start concrete (a folder, a penny, a CRT screen). End philosophical. Single paragraph. No title. No meta.
</s>
<|user|>
Cluster: {cluster_name} | {data['video_count']} videos {data['span']}
Factual: {arch}
Critic: {crit}
Fan: {fan_persp}
</s>
<|assistant|>
Seymour writes:</s>"""

    result = llm_generate(prompt, max_tokens=300, temperature=0.8)
    if result:
        # Clean up LLM output
        result = re.sub(r'^(Here\'s|Here is|I\'ve written|Sure!|Let me)', '', result).strip()
        return result
    return None


def list_clusters():
    """List all available presynth clusters."""
    clusters = []
    for f in sorted(PRESYNTH_DIR.glob("cluster_*.md")):
        text = f.read_text()
        m = re.search(r'^# (.+)', text)
        name = m.group(1).strip() if m else f.stem.replace("cluster_", "").replace("_", " ").title()
        m2 = re.search(r'covers (\d+) videos?', text)
        count = m2.group(1) if m2 else "?"
        clusters.append((name, count, f.name))
    return clusters


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Presynth → Ponderable bridge")
    parser.add_argument("query", nargs="?", default=None, help="Cluster name or search query")
    parser.add_argument("--all", action="store_true", help="Process all clusters")
    parser.add_argument("--template-only", action="store_true", help="Skip LLM, use templates only")
    parser.add_argument("--limit", type=int, default=0, help="Max clusters to process (0=unlimited)")
    parser.add_argument("--list", action="store_true", help="List available clusters")
    args = parser.parse_args()

    if args.list:
        print("\nAvailable clusters:")
        for name, count, fname in list_clusters():
            print(f"  {fname:50s} {name:30s} ({count} videos)")
        return

    # Get target clusters
    if args.all:
        clusters = [c[0] for c in list_clusters()]
        if args.limit > 0:
            clusters = clusters[:args.limit]
        print(f"Processing {len(clusters)} clusters...")
        for c in clusters:
            synthesize_ponderable(c, template_only=args.template_only)
            time.sleep(0.5)  # Rate limiting between entries
    elif args.query:
        synthesize_ponderable(args.query, template_only=args.template_only)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()