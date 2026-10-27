#!/usr/bin/env python3
"""
seymour_presynth.py — Multi-perspective pre-ingestion synthesizer.

Runs after topic tagging is complete. For each topic cluster, generates
summaries at multiple temperatures with different personality lenses,
then amalgamates into Wikipedia-style entries for the Ponderables Wiki.

Usage:
  python3 seymour_presynth.py                          # Full pipeline
  python3 seymour_presynth.py --dry-run                # Show clusters, no LLM calls
  python3 seymour_presynth.py --cluster "Marvel"       # Single cluster only
  python3 seymour_presynth.py --resume                 # Resume from saved progress
"""

import json
import sys
import time
import argparse
import requests
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# ── Paths ──────────────────────────────────────────────────────────────
INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
OUTPUT_DIR = Path("/home/wubu/seymour-project/pre_seymour/presynth")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = OUTPUT_DIR / "progress.json"
AMALGAM_OUTPUT = OUTPUT_DIR / "wikipedia_style_catalog.md"

# ── LLM Config ─────────────────────────────────────────────────────────
LLAMA_URL = "http://localhost:18802/v1/chat/completions"
MODEL = "Qwen3.6-27B-UD-IQ2_M.gguf"
MAX_TOKENS_PER_CALL = 600
REQUEST_TIMEOUT = 180

# Min videos to form their own cluster (smaller clusters merge into "Other")
MIN_CLUSTER_SIZE = 3

# ── Temperatures ───────────────────────────────────────────────────────
# Lower = more factual/deterministic. Higher = more creative/divergent.
TEMPERATURES = [0.3, 0.7, 1.0]

# ── Personality Lenses ─────────────────────────────────────────────────
# Each personality brings a different viewpoint to the same content.
PERSONALITIES = {
    "archivist": {
        "label": "Archivist (factual)",
        "system": (
            "You are Seymour, a meticulous archivist cataloging WuBu Streams content. "
            "Be direct, factual, and precise. List specific video titles, dates, and topics. "
            "Focus on what was recorded, when, and what happened. "
            "Avoid editorializing. 3-5 sentences. English only."
        ),
    },
    "critic": {
        "label": "Critic (skeptical)",
        "system": (
            "You are a skeptical media critic reviewing WuBu Streams content. "
            "Question the quality, originality, and significance. "
            "Point out patterns — what works, what's repetitive, what's surprising. "
            "Be honest but not cruel. 3-5 sentences. English only."
        ),
    },
    "fan": {
        "label": "Fan (enthusiastic)",
        "system": (
            "You are a passionate fan who loves WuBu Streams content. "
            "Highlight the best moments, funniest bits, and most impressive gameplay. "
            "Use a warm, engaged tone. Celebrate what makes this content special. "
            "3-5 sentences. English only."
        ),
    },
    "wikipedian": {
        "label": "Wikipedia Editor (neutral)",
        "system": (
            "You are a Wikipedia editor writing a neutral, encyclopedic summary. "
            "Use a formal, third-person tone. Structure information objectively. "
            "Include relevant dates, game titles, and content categories. "
            "No opinions, no emotional language. 3-5 sentences. English only."
        ),
    },
}

# ── Amalgamation Templates ─────────────────────────────────────────────

WIKIPEDIA_TEMPLATE = """# {cluster_name}

**Overview:** {overview}

## Scope

{scope}

## Timeline and Content

{timeline}

## Themes and Recurring Elements

{themes}

## Reception and Significance

{reception}

## Related Content

{related}

---
*Pre-ingestion entry generated {date} from {video_count} videos across {source_years}.*
"""


# ══════════════════════════════════════════════════════════════════════
#  DATA LAYER
# ══════════════════════════════════════════════════════════════════════

def load_index() -> dict:
    """Load the tagged video index."""
    with open(INDEX_FILE) as f:
        return json.load(f)


def cluster_by_keyword(index: dict, tag_blacklist: set = None) -> dict[str, list]:
    """
    Group videos into topic clusters based on shared tag keywords.

    A video can appear in multiple clusters if its tags span topics.
    Returns {cluster_name: [video_dict, ...]}.
    """
    if tag_blacklist is None:
        tag_blacklist = {
            "Gaming", "Video Games", "Entertainment", "Content Creation",
            "Gaming (General category)", "Video Games (General category)",
            "Let's Play", "Let's Play (Content type)", "Gaming Walkthrough",
            "Gaming Walkthrough (Content type)", "Gameplay",
            "Pop Culture", "Internet Culture", "Humor",
            "Alternative set:", "Topic 1", "Topic 2", "Topic 3",
            "Topic 4", "Topic 5",
        }

    # Collect all meaningful tags with frequency
    tag_videos = defaultdict(list)
    for vid, entry in index.items():
        topics = entry.get("topics", [])
        if not topics:
            continue
        for topic in topics:
            clean = topic.strip()
            # Skip generic/placeholder tags
            if any(bl in clean for bl in tag_blacklist):
                continue
            # Normalize: strip parenthetical qualifiers for grouping
            norm = clean.split(" (The ")[0].split(" (Content")[0].split(" (General")[0].split(" (Specific")[0].split(" (Implied")[0]
            norm = norm.split(" — ")[0].split(" – ")[0]
            norm = norm.strip()
            if len(norm) < 3:
                continue
            tag_videos[norm].append({
                "video_id": vid,
                "title": entry.get("title", ""),
                "date": entry.get("upload_date", "unknown"),
                "word_count": entry.get("word_count", 0),
                "topics": topics,
            })

    # Merge small clusters into "Other Topics"
    merged = {}
    other = []
    for tag, videos in sorted(tag_videos.items(), key=lambda x: -len(x[1])):
        if len(videos) >= MIN_CLUSTER_SIZE:
            merged[tag] = videos
        else:
            other.extend(videos)

    if other:
        merged["Other Topics"] = other

    return merged


def get_era(date_str: str) -> str:
    """Map upload date to era label."""
    if not date_str or date_str == "unknown":
        return "unknown"
    year = date_str[:4]
    if year <= "2023":
        return "Foundations (pre-2024)"
    elif year == "2024":
        return "Deep Dives (2024)"
    elif year == "2025":
        return "Hiatus & Prep (2025)"
    else:
        return "Absorption Era (2026)"


# ══════════════════════════════════════════════════════════════════════
#  LLM LAYER
# ══════════════════════════════════════════════════════════════════════

def llm_summarize(system_prompt: str, content: str, temperature: float) -> str:
    """Call local llama-server and return the response text."""
    prompt = (
        f"Summarize the following video content cluster. "
        f"Be concise (3-5 sentences).\n\n"
        f"CLUSTER CONTENT:\n{content}"
    )

    try:
        resp = requests.post(
            LLAMA_URL,
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": MAX_TOKENS_PER_CALL,
            },
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 200:
            result = resp.json()
            return result["choices"][0]["message"].get("content", "").strip()
        else:
            return f"[ERROR {resp.status_code}]"
    except Exception as e:
        return f"[EXCEPTION: {e}]"


def amalgamate_wikipedia(
    cluster_name: str,
    videos: list,
    all_summaries: dict,
    overview: str,
) -> str:
    """
    Amalgamate all personality+temp summaries into a Wikipedia-style entry.

    all_summaries = {
        personality_key: {temperature: [per-video-summaries...], "amalgamated": str},
        ...
    }
    """
    video_count = len(videos)
    dates = [v["date"] for v in videos if v["date"] != "unknown"]
    source_years = ", ".join(sorted(set(d[:4] for d in dates))) if dates else "unknown"

    # Build timeline from date-sorted videos
    sorted_vids = sorted(videos, key=lambda v: v["date"] if v["date"] != "unknown" else "9999")
    timeline_bullets = []
    for v in sorted_vids[:8]:  # Top 8 by date
        title_short = v["title"][:60]
        timeline_bullets.append(f"- **{v['date']}** — [{v['video_id']}](https://youtu.be/{v['video_id']}) {title_short}")
    if len(sorted_vids) > 8:
        timeline_bullets.append(f"- *...and {len(sorted_vids) - 8} more videos*")
    timeline = "\n".join(timeline_bullets)

    # Scope: what games, what format
    games = Counter()
    formats = Counter()
    # Include the cluster name itself as a game match
    cluster_lower = cluster_name.lower()
    for v in videos:
        for t in v.get("topics", []):
            tl = t.lower()
            if any(g in tl for g in ["game", "gaming", "walkthrough", "let's play",
                                     "playthrough", "stream", "vod"]):
                formats[t] += 1
            else:
                games[t] += 1
    # Add cluster name as primary game if not already counted
    if cluster_name not in games:
        games[cluster_name] = len(videos)

    top_games = ", ".join(g for g, _ in games.most_common(5)) if games else "various"
    scope = (
        f"This cluster covers {video_count} videos from {source_years}. "
        f"Primary games and topics: {top_games}. "
        f"Content formats include: {', '.join(f for f, _ in formats.most_common(3)) if formats else 'VODs and streams'}."
    )

    # Themes: extract from summaries
    themes_parts = []
    for pers_key, temp_dict in all_summaries.items():
        for temp, summary in temp_dict.items():
            if summary and not summary.startswith("[") and pers_key != "wikipedian":
                themes_parts.append(f"*{PERSONALITIES[pers_key]['label']} ({temp}):* {summary}")
    themes = "\n\n".join(themes_parts) if themes_parts else "Content spans multiple gaming genres and playstyles."

    # Reception: use wikipedian + amalgamated
    reception_parts = []
    if "wikipedian" in all_summaries:
        for temp, summary in all_summaries["wikipedian"].items():
            if summary and not summary.startswith("["):
                reception_parts.append(f"*Wikipedia Editor ({temp}):* {summary}")
    if "critic" in all_summaries:
        for temp, summary in all_summaries["critic"].items():
            if summary and not summary.startswith("["):
                reception_parts.append(f"*Critic ({temp}):* {summary}")
    reception = "\n\n".join(reception_parts[:4]) if reception_parts else "Content was produced as part of the WuBu Streams channel."

    # Related: other clusters or tags that overlap
    related = ""
    all_tags = Counter()
    for v in videos:
        for t in v.get("topics", []):
            all_tags[t] += 1
    top_tags = [t for t, _ in all_tags.most_common(8) if t not in tag_blacklist()]
    if top_tags:
        related = "Tags: " + ", ".join(top_tags[:8])
    else:
        related = "No related tags recorded."

    return WIKIPEDIA_TEMPLATE.format(
        cluster_name=cluster_name,
        overview=overview or "A collection of WuBu Streams videos covering related content.",
        scope=scope,
        timeline=timeline,
        themes=themes,
        reception=reception,
        related=related,
        date=datetime.now().strftime("%Y-%m-%d"),
        video_count=video_count,
        source_years=source_years,
    )


def tag_blacklist():
    return {
        "Gaming", "Video Games", "Entertainment", "Content Creation",
        "Gaming (General category)", "Video Games (General category)",
        "Let's Play", "Let's Play (Content type)", "Gaming Walkthrough",
        "Gaming Walkthrough (Content type)", "Gameplay",
        "Pop Culture", "Internet Culture", "Humor",
        "Alternative set:", "Topic 1", "Topic 2", "Topic 3",
        "Topic 4", "Topic 5",
    }


# ══════════════════════════════════════════════════════════════════════
#  PIPELINE
# ══════════════════════════════════════════════════════════════════════

def format_cluster_for_llm(videos: list) -> str:
    """Format a cluster's videos into a text block for the LLM."""
    parts = []
    for v in videos:
        topics_str = ", ".join(v.get("topics", [])[:3])
        parts.append(
            f"[{v['video_id']}] {v['date']} | {v['title'][:70]}\n"
            f"  Topics: {topics_str} | {v['word_count']} words"
        )
    return "\n".join(parts[:20])  # First 20 videos is enough context


def load_progress() -> dict:
    """Load saved progress if resuming."""
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text())
    return {"completed_clusters": [], "amalgamations": {}, "all_summaries": {}}


def save_progress(progress: dict):
    """Save progress for resume."""
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Multi-perspective pre-ingestion synthesizer")
    parser.add_argument("--dry-run", action="store_true", help="Show clusters, no LLM calls")
    parser.add_argument("--cluster", type=str, help="Process only clusters matching this name")
    parser.add_argument("--resume", action="store_true", help="Resume from saved progress")
    parser.add_argument("--force", action="store_true", help="Skip untagged warning prompt")
    args = parser.parse_args()

    # ── Load data ──
    print("Loading index...")
    index = load_index()

    tagged = sum(1 for v in index.values() if v.get("topics"))
    untagged = sum(1 for v in index.values() if not v.get("topics"))
    print(f"  Total: {len(index)} | Tagged: {tagged} | Untagged: {untagged}")

    if untagged > 0 and not args.dry_run and not args.force:
        print(f"  ⚠  {untagged} videos still untagged. Use --force to proceed.")
        return

    # ── Cluster ──
    print("Clustering by topic keyword...")
    clusters = cluster_by_keyword(index)
    print(f"  Found {len(clusters)} clusters:")
    for name, vids in sorted(clusters.items(), key=lambda x: -len(x[1])):
        print(f"    {name:40s} {len(vids):3d} videos")

    if args.dry_run:
        return

    # ── Progress ──
    progress = load_progress() if args.resume else {
        "completed_clusters": [],
        "all_summaries": {},
        "amalgamations": {},
    }

    # ── Process each cluster ──
    for cluster_name, videos in sorted(clusters.items(), key=lambda x: -len(x[1])):
        if args.cluster and args.cluster.lower() not in cluster_name.lower():
            continue
        if cluster_name in progress["completed_clusters"]:
            print(f"\n[{cluster_name}] Already completed, skipping.")
            continue

        print(f"\n{'='*70}")
        print(f"[{cluster_name}] {len(videos)} videos")
        print(f"{'='*70}")

        cluster_content = format_cluster_for_llm(videos)

        # For each personality × temperature combination
        cluster_summaries = {}
        for pers_key, pers_data in PERSONALITIES.items():
            cluster_summaries[pers_key] = {}
            for temp in TEMPERATURES:
                key = f"{pers_key}_{temp}"
                print(f"  [{key}] Generating...", end=" ", flush=True)

                # Check if we already have this from a previous partial run
                saved = progress.get("all_summaries", {}).get(cluster_name, {}).get(key)
                if saved:
                    print(f"cached.")
                    cluster_summaries[pers_key][temp] = saved
                    continue

                summary = llm_summarize(pers_data["system"], cluster_content, temp)
                cluster_summaries[pers_key][temp] = summary
                print(f"done ({len(summary)} chars)")

                # Save progress after each call
                if cluster_name not in progress["all_summaries"]:
                    progress["all_summaries"][cluster_name] = {}
                progress["all_summaries"][cluster_name][key] = summary
                save_progress(progress)

                # Brief pause between calls to not hammer the LLM
                time.sleep(2)

        # ── Amalgamate into Wikipedia entry ──
        print(f"  [amalgamating] Wikipedia-style entry...", end=" ", flush=True)

        # Generate overview using default temp
        overview_prompt = f"Write one sentence describing this collection of {len(videos)} videos about {cluster_name}."
        overview = llm_summarize(
            "You are a Wikipedia editor. Write one neutral, encyclopedic sentence.",
            f"Cluster: {cluster_name}\n{videos[0]['title'][:100] if videos else ''}...",
            0.5,
        )

        amalgam = amalgamate_wikipedia(cluster_name, videos, cluster_summaries, overview)

        # Save per-cluster output
        cluster_file = OUTPUT_DIR / f"cluster_{cluster_name.lower().replace(' ', '_').replace('(', '').replace(')', '')[:40]}.md"
        cluster_file.write_text(amalgam)
        print(f"saved to {cluster_file.name}")

        progress["completed_clusters"].append(cluster_name)
        progress["amalgamations"][cluster_name] = {
            "file": str(cluster_file),
            "video_count": len(videos),
            "overview": overview,
        }
        save_progress(progress)

    # ── Build master catalog ──
    print(f"\n{'='*70}")
    print("Building master Wikipedia-style catalog...")

    catalog_parts = [
        f"# WuBu Streams — Content Catalog",
        f"",
        f"*Pre-ingestion catalog generated {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        f"*Source: {len(index)} videos, {tagged} tagged, {len(clusters)} topic clusters*",
        f"",
        f"---",
        f"",
    ]

    for cluster_name in sorted(progress["amalgamations"].keys(), key=lambda c: -progress["amalgamations"][c]["video_count"]):
        info = progress["amalgamations"][cluster_name]
        cluster_file = Path(info["file"])
        if cluster_file.exists():
            content = cluster_file.read_text()
            catalog_parts.append(content)
            catalog_parts.append("")

    AMALGAM_OUTPUT.write_text("\n".join(catalog_parts))
    print(f"  Written to: {AMALGAM_OUTPUT}")
    print(f"  {len(progress['amalgamations'])} cluster entries")

    # ── Summary ──
    print(f"\n{'='*70}")
    print(f"DONE")
    print(f"  Clusters processed: {len(progress['completed_clusters'])}/{len(clusters)}")
    print(f"  LLM calls made: {len(progress['completed_clusters']) * len(PERSONALITIES) * len(TEMPERATURES)}")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"  Catalog: {AMALGAM_OUTPUT}")


if __name__ == "__main__":
    main()