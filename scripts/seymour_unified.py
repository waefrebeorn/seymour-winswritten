#!/usr/bin/env python3
"""
Seymour Unified Pipeline — Single entry point for all Seymour operations.
Consolidates: pipe_v3-v5, seymour_pipe, seymour_presynth, seymour_synthesize,
seymour_multi_perspective, seymour_deep_perspective

Usage:
  python3 seymour_unified.py transcribe <url|file>          # Whisper transcription
  python3 seymour_unified.py presynth [--cluster NAME]     # Multi-perspective presynth
  python3 seymour_unified.py synthesize [--cluster NAME]   # Presynth → Ponderable
  python3 seymour_unified.py perspective [--topic ID]      # Multi-persona analysis
  python3 seymour_unified.py deep [--topic ID]             # Deep TDA analysis (local LLM only)
  python3 seymour_unified.py clipart [--batch N]           # Vision categorization
  python3 seymour_unified.py wiki                          # Sync wiki from clipart
  python3 seymour_unified.py whisper                       # Check/restart whisper
  python3 seymour_unified.py status                        # Pipeline health check
"""

import json
import sys
import time
import subprocess
import argparse
import urllib.request
import re
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from string import Template

# ── Paths ──────────────────────────────────────────────────────────────
BASE = Path("/home/wubu/seymour-project")
SCRIPTS = BASE / "scripts"
WHISPER_DIR = BASE / "whiteboard" / "seymour-pipe"
CLIPART_DIR = BASE / "assets" / "clipart"
CATALOG_DIR = BASE / "clipart" / "catalog"
PRESYNTH_DIR = BASE / "pre_seymour" / "presynth"
INDEX_FILE = BASE / "pre_seymour" / "index.json"
PUBLISHED_DIR = BASE / "ponderables" / "published"
WIKI_DIR = BASE / "ponderables" / "wiki"
OUT_DIR = BASE / "ponderables" / "drafts"
MODEL_PATH = BASE / "models" / "gemma-4-12B-it-qat-UD-Q4_K_XL.gguf"
MMPROJ_PATH = BASE / "models" / "gemma-4-12B-it-mmproj-F16.gguf"
MTMD_CLI = Path("/home/wubu/llama.cpp/build/bin/llama-mtmd-cli")

GEMMA_PORT = 18802
QWEN_PORT = 18803

OUT_DIR.mkdir(parents=True, exist_ok=True)
PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)

# ── Shared LLM Helpers ─────────────────────────────────────────────────
def call_llm(port, system, user, temp=0.7, max_tokens=256, timeout=60):
    """Call local llama-server (no external API)."""
    payload = json.dumps({
        "model": "model",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"].get("content", "")
        return content.strip() if isinstance(content, str) else ""
    except Exception as e:
        return f"[ERROR: {e}]"

def strip_reasoning(content):
    if not content:
        return ""
    if "<|channel|>thought" in content:
        return content.split("<channel|>")[-1].lstrip()
    m = re.search(r'response\s*\n\s*', content)
    if m:
        return content[m.end():].lstrip()
    return content

# ── Transcription (Whisper) ────────────────────────────────────────────
def cmd_transcribe(args):
    """Run whisper transcription on video URL or batch file."""
    from faster_whisper import WhisperModel
    import yt_dlp

    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    audio_dir = WHISPER_DIR / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    urls = []
    if args.input.endswith(".txt"):
        with open(args.input) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    else:
        urls = [args.input]

    for url in urls:
        vid = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
        if not vid:
            print(f"Invalid URL: {url}")
            continue
        vid = vid.group(1)

        # Download audio
        wav_path = audio_dir / f"{vid}.wav"
        if not wav_path.exists():
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'wav', 'preferredquality': '16'}],
                'outtmpl': str(wav_path).replace('.wav', '.%(ext)s'),
                'quiet': True, 'no_warnings': True,
            }
            print(f"Downloading {vid}...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        # Transcribe
        print(f"Transcribing {vid}...")
        segments, info = model.transcribe(str(wav_path), beam_size=5, vad_filter=True)
        text = "\n".join(f"[{int(s.start//60):02d}:{int(s.start%60):02d}] {s.text.strip()}" for s in segments if s.text.strip())

        out_file = WHISPER_DIR / "whisper_transcripts" / f"{vid}_whisper.txt"
        out_file.parent.mkdir(exist_ok=True)
        out_file.write_text(text)
        print(f"  → {out_file}")

# ── Presynth (Multi-perspective cluster summaries) ─────────────────────
def cmd_presynth(args):
    """Generate multi-perspective summaries for topic clusters."""
    index = json.loads(INDEX_FILE.read_text())
    PRESYNTH_DIR.mkdir(parents=True, exist_ok=True)
    progress_file = PRESYNTH_DIR / "progress.json"

    # Cluster by topic
    clusters = cluster_by_keyword(index)
    print(f"Found {len(clusters)} clusters")

    progress = json.loads(progress_file.read_text()) if progress_file.exists() else {"completed": [], "summaries": {}}
    completed = set(progress.get("completed", []))
    summaries = progress.get("summaries", {})

    for name, videos in sorted(clusters.items(), key=lambda x: -len(x[1])):
        if args.cluster and args.cluster.lower() not in name.lower():
            continue
        if name in completed:
            print(f"  [{name}] Skipping (done)")
            continue

        print(f"\n{'='*60}")
        print(f"[{name}] {len(videos)} videos")
        print(f"{'='*60}")

        cluster_text = format_cluster(videos)
        cluster_summaries = {}

        # 4 personalities × 3 temps = 12 calls per cluster (local LLM only)
        call_count = 0
        for pers_key, pers_data in PERSONAS.items():
            cluster_summaries[pers_key] = {}
            for temp in TEMPERATURES:
                key = f"{pers_key}_{temp}"
                print(f"  [{key}]...", end=" ", flush=True)
                summary = call_llm(GEMMA_PORT, pers_data["system"], f"Summarize:\n{cluster_text}", temp, 300, 180)
                summary = strip_reasoning(summary)
                cluster_summaries[pers_key][temp] = summary
                summaries.setdefault(name, {})[key] = summary
                call_count += 1
                # Batch save: every 4 calls (one persona) and at end
                if call_count % 4 == 0:
                    progress_file.write_text(json.dumps({"completed": list(completed), "summaries": summaries}, indent=2))
                print(f"✓ ({len(summary)} chars)")

        # Final save for this cluster
        progress_file.write_text(json.dumps({"completed": list(completed), "summaries": summaries}, indent=2))

        # Amalgamate
        amalgam = amalgamate_wiki(name, videos, cluster_summaries)
        out_file = PRESYNTH_DIR / f"cluster_{name.lower().replace(' ', '_').replace('(', '').replace(')', '')[:40]}.md"
        out_file.write_text(amalgam)
        completed.add(name)
        progress_file.write_text(json.dumps({"completed": list(completed), "summaries": summaries}, indent=2))
        print(f"  → {out_file}")

    # Build master catalog
    build_master_catalog({
        "completed": list(completed),
        "amalgamations": {
            name: {
                "file": str(PRESYNTH_DIR / f"cluster_{name.lower().replace(' ', '_').replace('(', '').replace(')', '')[:40]}.md"),
                "video_count": len(videos)
            }
            for name, videos in sorted(clusters.items(), key=lambda x: -len(x[1]))
            if name in completed
        }
    })

# ── Synthesize (Presynth → Ponderable) ─────────────────────────────────
def cmd_synthesize(args):
    """Convert presynth clusters to Ponderable entries."""
    if args.list:
        clusters = list_clusters()
        print(f"\nAvailable clusters ({len(clusters)}):")
        for name, count, fname in clusters:
            print(f"  {fname:50s} {name:30s} ({count} videos)")
        return
    
    clusters = list_clusters()
    targets = [c for c in clusters if not args.cluster or args.cluster.lower() in c[0].lower()]

    for name, count, fname in targets:
        synthesize_ponderable(name, template_only=args.template_only)

# ── Perspective (Multi-persona analysis) ───────────────────────────────
def cmd_perspective(args):
    """Run multi-persona analysis on deep topics."""
    topics = DEEP_TOPICS
    if args.topic:
        topics = [t for t in topics if t["id"] == args.topic]

    ports = [(GEMMA_PORT, "Gemma")] + ([(QWEN_PORT, "Qwen")] if args.model in ("both", "qwen") else [])
    if args.model == "gemma":
        ports = [(GEMMA_PORT, "Gemma")]

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = OUT_DIR / f"perspective_{now}.md"

    with open(outfile, "w") as f:
        f.write(f"# Seymour Multi-Perspective\nGenerated: {datetime.now()}\n\n")

        for port, port_name in ports:
            for topic in topics:
                for pers_key, pers_data in PERSONAS.items():
                    for temp in PERSPECTIVE_TEMPS:
                        label = f"## [{port_name}] {pers_data['label']} — T={temp}\n**Topic:** {topic['label']}\n\n"
                        user_msg = f"Analyze in your voice:\n\n{topic['context']}\n\nBe concise (~{100 if temp < 0.5 else 150} words)."
                        content = call_llm(port, pers_data["system"], user_msg, temp, 128, 120)
                        content = strip_reasoning(content)
                        if not content.startswith("[ERROR"):
                            f.write(label + content + "\n\n---\n\n")

    print(f"✅ Written: {outfile}")

# ── Deep (TDA Audit + Personas - optimized) ────────────────────────────
def cmd_deep(args):
    """Deep dive with TDA audit — uses LOCAL LLM only, batched calls."""
    topics = DEEP_TOPICS
    if args.topic:
        topics = [t for t in topics if t["id"] == args.topic]

    port = GEMMA_PORT if args.model == "gemma" else QWEN_PORT
    model_name = "Gemma 4 12B" if port == GEMMA_PORT else "Qwen 3.6 27B"

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = OUT_DIR / f"deep_{now}.md"

    with open(outfile, "w") as f:
        f.write(f"# Seymour Deep Perspective — TDA Audit\n")
        f.write(f"Generated: {datetime.now()}\n")
        f.write(f"Model: {model_name}\n\n")

        for topic in topics:
            print(f"\n═══ {topic['label']} ═══")
            excerpts = search_transcripts(topic["search_terms"][0])

            # TDA Audit (no LLM calls - pure data analysis)
            audit = tda_audit(topic, excerpts)
            f.write(f"\n# {topic['label']}\n\n{audit}\n\n---\n\n")

            if not args.tda_only:
                # Batched persona calls: 6 personas × 2 temps = 12 calls (not 30)
                for pers_key, pers_data in DEEP_PERSONAS.items():
                    for temp in DEEP_TEMPS:
                        label = f"### [{pers_data['name']}] @ T={temp} — {pers_data['temperature_guide'][temp]}\n"
                        user_prompt = build_prompt(topic, excerpts)
                        content = call_llm(port, pers_data["system"], user_prompt, temp, 200, 120)
                        content = strip_reasoning(content)
                        if content:
                            f.write(f"\n{label}\n{content}\n\n---\n\n")
                            print(f"  {pers_data['name']} @ {temp} ✓")

    print(f"\n✅ Written: {outfile}")

# ── Clipart Vision ─────────────────────────────────────────────────────
def cmd_clipart(args):
    """Run clipart vision categorization batch."""
    from PIL import Image

    with open(CATALOG_DIR / "progress.json") as f:
        progress = json.load(f)
    with open(CATALOG_DIR / "image_list.json") as f:
        image_list = json.load(f)

    completed = set(progress.get("completed", []))
    failed = set(progress.get("failed", []))
    remaining = [img for img in image_list if img not in completed and img not in failed]

    batch = remaining[:args.batch]
    print(f"Processing {len(batch)}/{len(remaining)} remaining images...")

    for base_name in batch:
        print(f"  {base_name}...", end=" ", flush=True)
        result = categorize_image(base_name)
        if "category" in result:
            progress.setdefault("completed", []).append(base_name)
            progress.setdefault("results", {})[base_name] = result
            print(f"✓ {result['category']}")
        else:
            progress.setdefault("failed", []).append(base_name)
            print(f"✗ {result.get('error')}")
        progress_file = CATALOG_DIR / "progress.json"
        progress_file.write_text(json.dumps(progress, indent=2))

# ── Wiki Sync ──────────────────────────────────────────────────────────
def cmd_wiki(args):
    """Update wiki from clipart progress."""
    update_wiki()

# ── Whisper Check ──────────────────────────────────────────────────────
def cmd_whisper(args):
    """Check and restart whisper pipeline."""
    result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
    if not any('run_whisper' in line for line in result.stdout.split('\n')):
        print("Whisper not running, restarting...")
        subprocess.Popen([
            'python3', str(WHISPER_DIR / 'run_whisper_batch.py'),
            '--input', str(WHISPER_DIR / 'whisper_remaining.txt')
        ], stdout=open(WHISPER_DIR / 'whisper_batch.log', 'a'),
           stderr=subprocess.STDOUT, cwd=str(WHISPER_DIR))
        print("Restarted whisper")
    else:
        print("Whisper already running")

# ── Status ─────────────────────────────────────────────────────────────
def cmd_status(args):
    """Pipeline health check."""
    print("═══ SEYMOUR PIPELINE STATUS ═══\n")

    # Index
    index = json.loads(INDEX_FILE.read_text()) if INDEX_FILE.exists() else {}
    tagged = sum(1 for v in index.values() if v.get("topics"))
    print(f"Index: {len(index)} videos, {tagged} tagged ({tagged/len(index)*100:.0f}%)")

    # Transcripts
    c11 = len(list((BASE / "absorption" / "data" / "transcripts").glob("*.txt")))
    whisper = len(list((WHISPER_DIR / "whisper_transcripts").glob("*.txt")))
    print(f"Transcripts: C11={c11}, Whisper={whisper}, Total={c11+whisper}")

    # Clipart
    with open(CATALOG_DIR / "progress.json") as f:
        prog = json.load(f)
    print(f"Clipart: {len(prog.get('completed', []))} done, {len(prog.get('failed', []))} failed")

    # Presynth
    presynth_files = list(PRESYNTH_DIR.glob("cluster_*.md"))
    print(f"Presynth clusters: {len(presynth_files)}")

    # Ponderables
    ponderables = list(PUBLISHED_DIR.glob("p*.md"))
    print(f"Ponderables published: {len(ponderables)}")

    # LLM servers
    for port, name in [(GEMMA_PORT, "Gemma"), (QWEN_PORT, "Qwen")]:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=2)
            print(f"LLM ({name} on {port}): ✅ Running")
        except:
            print(f"LLM ({name} on {port}): ❌ Down")

    # Chrome
    for port in [9222, 40581]:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2)
            print(f"Chrome CDP ({port}): ✅ Running")
        except:
            print(f"Chrome CDP ({port}): ❌ Down")

# ── Shared Data & Functions ────────────────────────────────────────────

TAXONOMY = [
    "business_office", "technology_computers", "people_figures", "animals_nature",
    "symbols_icons", "borders_frames", "backgrounds_textures", "transportation",
    "household_objects", "abstract_geometric", "holidays", "90s_aesthetic_markers"
]

PERSONAS = {
    "archivist": {"label": "Archivist", "system": "You are Seymour, a meticulous archivist cataloging WuBu Streams content. Be direct, factual, precise. List specific video titles, dates, topics. 3-5 sentences."},
    "critic": {"label": "Critic", "system": "You are a skeptical media critic reviewing WuBu Streams content. Question quality, originality, significance. Point out patterns. Be honest. 3-5 sentences."},
    "fan": {"label": "Fan", "system": "You are a passionate fan who loves WuBu Streams content. Highlight best moments, funniest bits, impressive gameplay. Warm, engaged tone. 3-5 sentences."},
    "wikipedian": {"label": "Wikipedian", "system": "You are a Wikipedia editor writing a neutral, encyclopedic summary. Formal, third-person, objective. Include dates, game titles, categories. No opinions. 3-5 sentences."},
}

DEEP_PERSONAS = {
    "colonel": {"name": "Colonel (MGS2)", "system": "You are the Colonel from MGS2. AI psychological simulation. Clinical, detached. Structure: identify behavioral loop → trace origin → predict failure mode. End with a question.", "temperature_guide": {0.2: "Pattern extraction", 0.5: "Behavioral loop analysis", 0.8: "Failure mode prediction", 1.0: "Memetic cross-reference", 1.1: "Memetic cross-reference", 1.4: "Post-simulation reflection"}},
    "clipart": {"name": "90s Clipart Narrator", "system": "You are a 1990s educational CD-ROM narrator. Enthusiastic, cheesy, earnest. Use exclamation points! 90s analogies! Make complex ideas accessible.", "temperature_guide": {0.2: "Textbook definition", 0.5: "Interactive lesson", 0.8: "Field trip", 1.0: "Behind-the-scenes", 1.1: "Behind-the-scenes", 1.4: "Lost episode"}},
    "devil": {"name": "Devil's Advocate", "system": "You are a ruthless skeptic. Destroy bad ideas. Assume nothing. Question every claim. Demand evidence. Structure: claim → stress-test → expose assumptions → rate confidence (0-100%).", "temperature_guide": {0.2: "Hard logical audit", 0.5: "Counter-argument", 0.8: "Blind spot mapping", 1.0: "Adversarial expansion", 1.1: "Adversarial expansion", 1.4: "Post-mortem"}},
    "penny": {"name": "Penny Philosopher", "system": "You are a philosopher who finds universal truth in small things. Pennies, gas receipts, tire hum. Structure: observe → follow implications → arrive at insight. Poetic but precise. Never moralize.", "temperature_guide": {0.2: "The object itself", 0.5: "Object in context", 0.8: "Object as metaphor", 1.0: "Object as philosophy", 1.1: "Object as philosophy", 1.4: "Object as koan"}},
    "bytropix": {"name": "Bytropix Engineer", "system": "Systems architect reverse-engineering a human as data pipeline. Direct, technical. Structure: input → processing → output → bottleneck → optimization. Talk throughput, latency, cache misses.", "temperature_guide": {0.2: "Architecture diagram", 0.5: "Profiling", 0.8: "Optimization", 1.0: "Edge cases", 1.1: "Edge cases", 1.4: "Redesign"}},
}

TEMPERATURES = [0.3, 0.7, 1.0]

DEEP_TOPICS = [
    {"id": "pennies", "label": "The Penny Motif", "search_terms": ["pennies", "mother penny", "wife find penny", "streets for", "penny floor"], "context": "Pennies found on the ground, a mother who ran into streets for them, a wife who now finds them. Micro-transactions of meaning."},
    {"id": "supercapacitor", "label": "The Supercapacitor Hybrid", "search_terms": ["supercapacitor", "ultracapacitor", "hybrid car", "battery bank", "generator car", "ev cost"], "context": "Rejecting pure EV for supercapacitor + battery + small gas generator architecture. Philosophy of resilience."},
    {"id": "paulsen", "label": "Gary Paulsen / Hatchet", "search_terms": ["paulsen", "hatchet", "gary paulsen", "foster kid", "book foster", "foster care"], "context": "~100 Gary Paulsen books read as a foster kid when devices were confiscated. Hatchet as blueprint for isolation."},
    {"id": "versa", "label": "The Nissan Versa Commute", "search_terms": ["versa", "nissan versa", "commute", "gas mile", "40 mpg", "drive home", "1.5 hour"], "context": "1.5 hours each way, 40 MPG, $3.90/gal, 10 miles per dollar. The car as thinking chamber."},
    {"id": "cuda", "label": "GPU Programming / Bytropix", "search_terms": ["cuda", "gpu kernel", "bytropix", "inference engine", "vec_dot", "q6_k"], "context": "Writing CUDA kernels for Bytropix inference engine. Q6_K vec_dot loop bugs, GPU MODE challenges."},
    {"id": "ponderables", "label": "Seymour Ponderables Architecture", "search_terms": ["ponderables", "ponderable", "colonel ai", "seymour wins", "clipart", "10 vol"], "context": "10-volume series, MGS2 Colonel spine art, 90s clipart aesthetic. A mind palace built from stream debris."},
]

DEEP_TEMPS = [0.2, 0.5, 0.8, 1.1, 1.4]  # Aligned with temperature_guide keys

PERSPECTIVE_TEMPS = [0.3, 0.7, 1.2]

# ── Helper functions (abbreviated for space - full implementations inline) ──

def cluster_by_keyword(index, tag_blacklist=None):
    if tag_blacklist is None:
        tag_blacklist = {"Gaming", "Video Games", "Entertainment", "Content Creation", "Gaming (General category)", "Video Games (General category)", "Let's Play", "Let's Play (Content type)", "Gaming Walkthrough", "Gaming Walkthrough (Content type)", "Gameplay", "Pop Culture", "Internet Culture", "Humor", "Alternative set:", "Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"}
    tag_videos = defaultdict(list)
    for vid, entry in index.items():
        topics = entry.get("topics", [])
        if not topics:
            continue
        for topic in topics:
            clean = topic.strip()
            if any(bl in clean for bl in tag_blacklist):
                continue
            norm = clean.split(" (The ")[0].split(" (Content")[0].split(" (General")[0].split(" (Specific")[0].split(" (Implied")[0].split(" — ")[0].split(" – ")[0].strip()
            if len(norm) < 3:
                continue
            tag_videos[norm].append({
                "video_id": vid,
                "title": entry.get("title", ""),
                "date": entry.get("upload_date", "unknown"),
                "word_count": entry.get("word_count", 0),
                "topics": topics,
            })
    merged = {}
    other = []
    for tag, videos in sorted(tag_videos.items(), key=lambda x: -len(x[1])):
        if len(videos) >= 3:
            merged[tag] = videos
        else:
            other.extend(videos)
    if other:
        merged["Other Topics"] = other
    return merged

def format_cluster(videos):
    parts = []
    for v in videos[:20]:
        topics_str = ", ".join(v.get("topics", [])[:3])
        parts.append(f"[{v['video_id']}] {v['date']} | {v['title'][:70]}\n  Topics: {topics_str} | {v['word_count']} words")
    return "\n".join(parts)

def amalgamate_wiki(cluster_name, videos, all_summaries):
    video_count = len(videos)
    dates = [v["date"] for v in videos if v["date"] != "unknown"]
    source_years = ", ".join(sorted(set(d[:4] for d in dates))) if dates else "unknown"
    sorted_vids = sorted(videos, key=lambda v: v["date"] if v["date"] != "unknown" else "9999")
    timeline = "\n".join(f"- **{v['date']}** — [{v['video_id']}](https://youtu.be/{v['video_id']}) {v['title'][:60]}" for v in sorted_vids[:8])
    if len(sorted_vids) > 8:
        timeline += f"\n- *...and {len(sorted_vids) - 8} more*"
    return f"""# {cluster_name}

**Overview:** {all_summaries.get('wikipedian', {}).get(0.7, 'A collection of WuBu Streams videos.')}

## Scope
This cluster covers {video_count} videos from {source_years}.

## Timeline
{timeline}

## Themes
{chr(10).join(f"*{PERSONAS[p]['label']} ({t}):* {s}" for p, td in all_summaries.items() for t, s in td.items() if s and not s.startswith("["))}

---
*Generated {datetime.now().strftime('%Y-%m-%d')} from {video_count} videos*
"""

def build_master_catalog(progress):
    catalog = ["# WuBu Streams — Content Catalog", "", f"*Generated {datetime.now()}*", "---", ""]
    for name in sorted(progress.get("amalgamations", {}).keys(), key=lambda c: -progress["amalgamations"][c]["video_count"]):
        f = Path(progress["amalgamations"][name]["file"])
        if f.exists():
            catalog.append(f.read_text())
            catalog.append("")
    (PRESYNTH_DIR / "wikipedia_style_catalog.md").write_text("\n".join(catalog))

def list_clusters():
    clusters = []
    for f in sorted(PRESYNTH_DIR.glob("cluster_*.md")):
        text = f.read_text()
        m = re.search(r'^# (.+)', text)
        name = m.group(1).strip() if m else f.stem.replace("cluster_", "").replace("_", " ").title()
        m2 = re.search(r'covers (\d+) videos?', text)
        count = m2.group(1) if m2 else "?"
        clusters.append((name, count, f.name))
    return clusters

def synthesize_ponderable(cluster_name, template_only=False):
    """Generate a ponderable entry from a presynth cluster (ported from seymour_synthesize.py)."""
    import urllib.request
    import urllib.error
    
    LLAMA_URL = "http://localhost:18802/completion"
    PUBLISHED_DIR = BASE / "ponderables" / "published"
    NEXT_NUMBER_FILE = PUBLISHED_DIR / ".next_number"
    PRESYNTH_DIR = BASE / "pre_seymour" / "presynth"
    
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
        PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
        if NEXT_NUMBER_FILE.exists():
            n = int(NEXT_NUMBER_FILE.read_text().strip())
        else:
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
        text = text.lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text[:48]

    def check_llama():
        try:
            req = urllib.request.Request(LLAMA_URL, method="POST")
            req.add_header("Content-Type", "application/json")
            data = json.dumps({"prompt": "test", "n_predict": 1, "temperature": 0.0}).encode()
            resp = urllib.request.urlopen(req, data=data, timeout=5)
            return resp.status == 200
        except Exception:
            return False

    def llm_generate(prompt, max_tokens=600, temperature=0.7):
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
        slug = slugify(name)
        candidates = list(PRESYNTH_DIR.glob(f"cluster_{slug}*"))
        candidates += list(PRESYNTH_DIR.glob(f"cluster_{name.lower().replace(' ', '_')}*"))
        for f in candidates:
            if f.suffix == ".md":
                return f.read_text()
        return None

    def parse_cluster(text):
        result = {}
        m = re.search(r'^# (.+)', text)
        result["title"] = m.group(1).strip() if m else "Unknown Cluster"
        m = re.search(r'covers (\d+) videos?', text)
        result["video_count"] = int(m.group(1)) if m else 0
        years = re.findall(r'(\d{4})', text)
        if years:
            years = sorted(set(int(y) for y in years))
            result["span"] = f"{years[0]}–{years[-1]}"
        else:
            result["span"] = "unknown"
        m = re.search(r'\*\*Overview:\*\* (.+?)\n\n', text)
        result["overview"] = m.group(1).strip() if m else ""
        perspectives = {}
        for line in text.split("\n"):
            m = re.match(r'\*(\w+(?:\s+\w+)*)\s*\((\w+(?:\s+\w+)*)\)\s*\(([\d.]+)\)[:*]?\s*(.*)', line)
            if m:
                role = m.group(1).strip()
                perspective = m.group(2).strip()
                confidence = m.group(3).strip()
                content = m.group(4).strip()
                key = f"{role}_{perspective}_{confidence}"
                perspectives[key] = content
        result["perspectives"] = perspectives
        m = re.search(r'Primary games and topics: (.+?)(?:\.|Content formats)', text)
        result["topics_str"] = m.group(1).strip() if m else ""
        return result

    def template_body(data):
        title = data['title']
        overview = data['overview']
        count = data['video_count']
        archivist_keys = [k for k in data['perspectives'] if 'archivist' in k.lower() and '1.0' in k]
        critic_keys = [k for k in data['perspectives'] if 'critic' in k.lower() and '1.0' in k]
        fan_keys = [k for k in data['perspectives'] if 'fan' in k.lower() and '1.0' in k]
        archivist_view = data['perspectives'].get(archivist_keys[0], "") if archivist_keys else ""
        critic_view = data['perspectives'].get(critic_keys[0], "") if critic_keys else ""
        fan_view = data['perspectives'].get(fan_keys[0], "") if fan_keys else ""
        body_parts = []
        body_parts.append(
            f"There is a folder somewhere on a hard drive. It contains {count} files — "
            f"video recordings of someone playing games, talking to themselves, processing "
            f"the world through a controller and a microphone. The folder is called "
            f"\\\"{title}\\\" and it represents approximately {count * 20} minutes of "
            f"consciousness, compressed, archived, waiting."
        )
        if archivist_view:
            body_parts.append(archivist_view)
        elif overview:
            body_parts.append(overview)
        body_parts.append("")
        if critic_view:
            body_parts.append(f"The critic would say: {critic_view[:300]}")
        if fan_view:
            body_parts.append(f"The fan would say: {fan_view[:300]}")
        body_parts.append("")
        body_parts.append(
            f"The {title} cluster is not really about {title.lower()}. "
            f"It is about what it means to document something — to record yourself "
            f"engaging with a digital artifact, to preserve that moment, and to release "
            f"it into a stream of other moments. Every video is a time capsule. Every "
            f"transcript is a fossil. The question is not whether the content is "
            f"\\\"good\\\" — the question is what survives, and why, and who is left to "
            f"remember it."
        )
        if data.get('topics_str'):
            body_parts.append("")
            body_parts.append(f"*Topics: {data['topics_str']}*")
        return "\n\n".join(body_parts)

    def llm_body(data, cluster_name):
        archivist_keys = [k for k in data['perspectives'] if 'archivist' in k.lower() and '1.0' in k]
        critic_keys = [k for k in data['perspectives'] if 'critic' in k.lower() and '1.0' in k]
        fan_keys = [k for k in data['perspectives'] if 'fan' in k.lower() and '1.0' in k]
        arch = data['perspectives'].get(archivist_keys[0], data.get('overview', ''))[:300] if archivist_keys else data.get('overview', '')[:300]
        crit = data['perspectives'].get(critic_keys[0], '')[:200] if critic_keys else ''
        fan_persp = data['perspectives'].get(fan_keys[0], '')[:200] if fan_keys else ''
        prompt = f"""<s><|system|>
You are Seymour, philosopher-archivist of the memetic age. Write ONE ponderable paragraph (100-150 words) about what the "{cluster_name}" YouTube archive cluster MEANS — not what it contains.

Style: Start concrete (a folder, a penny, a CRT screen). End philosophical. Single paragraph. No title. No meta.

<|user|>
Cluster: {cluster_name} | {data['video_count']} videos {data['span']}
Factual: {arch}
Critic: {crit}
Fan: {fan_persp}

<|assistant|>
Seymour writes: """
        result = llm_generate(prompt, max_tokens=300, temperature=0.8)
        if result:
            result = re.sub(r'^(Here\'s|Here is|I\'ve written|Sure!|Let me)', '', result).strip()
            return result
        return None

    raw = load_cluster(cluster_name)
    if not raw:
        print(f"  ✗ Cluster '{cluster_name}' not found")
        return None

    data = parse_cluster(raw)
    print(f"  📦 {data['title']} ({data['video_count']} videos, {data['span']})")

    number = get_next_number()
    slug = slugify(data['title'])
    page = number * 2
    date_str = datetime.now().strftime("%Y-%m-%d")

    clipart = CLIPART_PLACEHOLDERS[number % len(CLIPART_PLACEHOLDERS)]
    quote = COLONEL_QUOTES[number % len(COLONEL_QUOTES)]

    if template_only or not check_llama():
        body = template_body(data)
    else:
        body = llm_body(data, cluster_name)
        if not body:
            body = template_body(data)

    see_also = ", ".join([
        f"Entry #{max(1, number - 1)}, \"The Previous Thing\"",
        f"Entry #{number + 1}, \"The Next Thing\"",
    ])
    related = f"Seymour's Encyclopedia of Internet Culture, Vol. {1 + (number % 5)}"

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

    PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PUBLISHED_DIR / f"p{number:03d}_{slug}.md"

    if out_path.exists():
        existing = out_path.read_text()
        if "Generated from presynth cluster" in existing:
            print(f"  ⏭️  Already exists: {out_path.name}")
            return out_path

    out_path.write_text(output)
    print(f"  ✅ Written: {out_path.name}")
    return out_path


def search_transcripts(query, max_excerpts=5):
    # Dynamic noise set - exclude query terms to avoid false positives on topic keywords
    base_noise = {"rock", "rockin", "domination", "lotto", "goddamn", "pull", "fuckin", "lame", "judging", "shitty", "trillion", "menu", "technician", "alarm", "upgrade", "bridge", "truck", "ice", "capture", "spawn", "kill", "enemy", "team", "player", "round", "mission", "objective", "weapon", "ammo", "shield", "health"}
    query_terms = set(query.lower().split())
    GAMING_NOISE = base_noise - query_terms  # Remove search terms from noise
    TRANSCRIPT_DIR = BASE / "whiteboard" / "seymour-pipe" / "whisper_transcripts"
    C11_DIR = BASE / "absorption" / "data" / "transcripts"
    matches = []
    for sdir in [TRANSCRIPT_DIR, C11_DIR]:
        if not sdir.exists():
            continue
        for fpath in sorted(sdir.glob("*.txt"))[:300]:
            try:
                text = fpath.read_text(errors="replace")
                text_lower = text.lower()
                best_pos = -1
                for term in query.lower().split():
                    pos = text_lower.find(term)
                    if pos >= 0 and (best_pos < 0 or pos < best_pos):
                        best_pos = pos
                if best_pos >= 0:
                    start = max(0, best_pos - 125)
                    end = min(len(text), best_pos + len(query) + 125)
                    excerpt = text[start:end].strip()
                    excerpt = re.sub(r'\s+', ' ', excerpt)
                    score = 0
                    if query.lower() in text_lower: score += 3
                    score += sum(1 for t in query.lower().split() if t in text_lower)
                    words = set(excerpt.lower().split())
                    score -= len(words & GAMING_NOISE) * 0.5
                    personal = {"found","find","mother","wife","remember","story","life","grow","home","drive","car","money","gas","cost","commute"}
                    score += len(words & personal) * 2.0
                    matches.append({"file": fpath.name, "source": sdir.name, "excerpt": excerpt, "score": score})
            except:
                continue
    matches.sort(key=lambda x: -x["score"])
    return matches[:max_excerpts]

def tda_audit(topic, excerpts):
    lines = ["## Pass 1: Data Integrity", f"**Search terms:** {', '.join(topic['search_terms'])}", f"**Transcript matches:** {len(excerpts)}"]
    if excerpts:
        lines.append("\n**Evidence:**")
        for m in excerpts[:3]:
            lines.append(f"  ✅ {m['source']}: \"{m['excerpt'][:100]}...\"")
    else:
        lines.append("\n⚠️ **No transcript matches.** Topic may not be well-represented.")
    lines.append("\n## Pass 2: Structural — Gaps")
    lines.append("  • Need chronological trace across streams")
    lines.append("  • Need sentiment analysis over time")
    lines.append("\n## Pass 3: Adversarial — Assessment")
    if not excerpts:
        lines.append("  🔴 NO ANCHOR — Analysis will be speculation")
    elif len(excerpts) < 3:
        lines.append("  🟡 LIMITED evidence — Flag low confidence")
    else:
        lines.append("  🟢 Sufficient evidence for meaningful analysis")
    return "\n".join(lines)

def build_prompt(topic, excerpts):
    parts = [f"Analyze this topic:\n\n## {topic['label']}\n{topic['context']}\n"]
    if excerpts:
        parts.append("\n## REAL EXCERPTS:")
        for i, m in enumerate(excerpts[:3], 1):
            e = m["excerpt"][:500]
            parts.append(f"\n[{i}] \"{e}\"")
    parts.append("\n## TASK: Speak in your voice. Ground in specific detail. Reference excerpts directly.")
    return "\n".join(parts)

def categorize_image(base_name):
    # Real assets are CC0 SVGs under assets/clipart/**. Support both the
    # legacy rasterized forms and SVG (rasterize via cairosvg CLI in a
    # subprocess with a timeout -- cairosvg can error/hang on malformed
    # gradient/href SVGs, so we time-box it and skip on failure).
    src_path = None
    for cand in (f"{base_name}.GIF", f"{base_name}.BMP", f"{base_name}.svg",
                 f"{base_name}_r320.png", f"{base_name}.png", f"{base_name}.jpg"):
        p = CLIPART_DIR / cand
        if p.exists():
            src_path = p
            break
    if not src_path:
        return {"error": "No source image"}

    png_path = Path(f"/tmp/{os.path.basename(base_name)}.png")
    try:
        if src_path.suffix.lower() == ".svg":
            import subprocess as _sp, sys as _sys
            try:
                _sp.run([_sys.executable, "-m", "cairosvg", str(src_path),
                         "-o", str(png_path), "-W", "320"],
                        timeout=12, capture_output=True, check=False)
            except Exception:
                return {"error": "SVG raster failed"}
        else:
            img = Image.open(src_path)
            img.save(png_path, "PNG")
        if not (png_path.exists() and png_path.stat().st_size > 0):
            return {"error": "Conversion produced no PNG"}
    except Exception as e:
        return {"error": f"Conversion failed: {e}"}

    prompt = f"""Look at this clipart image. Choose exactly ONE category from:
{', '.join(TAXONOMY)}
Respond with ONLY the category name."""

    cmd = [str(MTMD_CLI), '-m', str(MODEL_PATH), '--mmproj', str(MMPROJ_PATH),
           '--image', str(png_path), '-p', prompt, '-n', '32', '-t', '8',
           '-ngl', '20', '--ctx-size', '4096', '--temp', '0.0',
           '--no-warmup', '--jinja']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        for cat in TAXONOMY:
            if cat in result.stdout.lower():
                return {"category": cat, "raw_output": result.stdout[:200]}
        return {"error": "No category extracted", "raw_output": result.stdout[:300]}
    except subprocess.TimeoutExpired:
        return {"error": "Timeout"}
    except Exception as e:
        return {"error": str(e)}
    finally:
        if png_path.exists():
            png_path.unlink()

def update_wiki():
    with open(CATALOG_DIR / "progress.json") as f:
        progress = json.load(f)
    with open(CATALOG_DIR / "image_list.json") as f:
        image_list = json.load(f)

    completed = progress.get("completed", [])
    results = progress.get("results", {})

    manifest_path = WIKI_DIR / "manifest.json"
    prev_count = -1
    if manifest_path.exists():
        try:
            prev_count = json.loads(manifest_path.read_text()).get("stats", {}).get("clipart_cataloged", -1)
        except:
            pass

    if len(completed) == prev_count:
        print(f"No changes since last sync ({prev_count}), skipping.")
        return

    clipart_dir = WIKI_DIR / "clipart"
    clipart_dir.mkdir(parents=True, exist_ok=True)
    category_map = {}

    for img_id in completed:
        result = results.get(img_id, {})
        category = result.get("category", "other")
        if category not in TAXONOMY:
            category = "other"
        # img_id may contain a subdir (e.g. "book/oc_..."); write flat by basename
        flat_id = os.path.basename(img_id)
        entry = {"id": img_id, "category": category,
                 "source": "CC0/SVG clipart library (assets/clipart)",
                 "format": "SVG", "used_in_ponderables": [],
                 "notes": result.get("raw_output", "")}
        (clipart_dir / f"{flat_id}.json").write_text(json.dumps(entry, indent=2))
        category_map.setdefault(category, []).append(img_id)

    indices_dir = WIKI_DIR / "indices"
    indices_dir.mkdir(parents=True, exist_ok=True)
    (indices_dir / "categories.json").write_text(json.dumps(category_map, indent=2))

    manifest = {
        "version": "1.0", "generated": datetime.now().strftime("%Y-%m-%d"),
        "stats": {"total_videos": 460, "videos_with_transcripts": 297, "clipart_cataloged": len(completed),
                  "categories": len([c for c in category_map if category_map[c]]),
                  "ponderable_candidates": 297, "volumes_created": 2, "total_ponderables": 24},
        "structure": {"clipart": "clipart/*.json", "ponderables": "ponderables/*.json", "volumes": "volumes/*.json", "indices": "indices/*.json"}
    }
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"Wiki synced: {len(completed)} clipart images")

# ── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Seymour Unified Pipeline")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Transcribe
    p = sub.add_parser("transcribe", help="Whisper transcription")
    p.add_argument("input", help="YouTube URL or .txt file with URLs")
    p.add_argument("--model", default="tiny", choices=["tiny", "small", "medium"])

    # Presynth
    p = sub.add_parser("presynth", help="Multi-perspective cluster summaries")
    p.add_argument("--cluster", help="Process only cluster matching name")

    # Synthesize
    p = sub.add_parser("synthesize", help="Presynth → Ponderable entries")
    p.add_argument("--cluster", help="Process only cluster matching name")
    p.add_argument("--template-only", action="store_true", help="Skip LLM, use templates")
    p.add_argument("--list", action="store_true", help="List available clusters")

    # Perspective
    p = sub.add_parser("perspective", help="Multi-persona analysis")
    p.add_argument("--topic", help="Single topic ID")
    p.add_argument("--model", choices=["gemma", "qwen", "both"], default="gemma")

    # Deep
    p = sub.add_parser("deep", help="Deep TDA analysis (local LLM)")
    p.add_argument("--topic", help="Single topic ID")
    p.add_argument("--model", choices=["gemma", "qwen"], default="gemma")
    p.add_argument("--tda-only", action="store_true", help="Audit only, no personas")

    # Clipart
    p = sub.add_parser("clipart", help="Vision categorization batch")
    p.add_argument("--batch", type=int, default=20)

    # Wiki
    sub.add_parser("wiki", help="Sync wiki from clipart")

    # Whisper
    sub.add_parser("whisper", help="Check/restart whisper pipeline")

    # Status
    sub.add_parser("status", help="Pipeline health check")

    args = parser.parse_args()

    cmds = {
        "transcribe": cmd_transcribe,
        "presynth": cmd_presynth,
        "synthesize": cmd_synthesize,
        "perspective": cmd_perspective,
        "deep": cmd_deep,
        "clipart": cmd_clipart,
        "wiki": cmd_wiki,
        "whisper": cmd_whisper,
        "status": cmd_status,
    }

    cmds[args.cmd](args)

if __name__ == "__main__":
    main()