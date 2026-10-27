#!/usr/bin/env python3
"""
topic_gap_filler.py — Fill missing topic tags using local LLM.
Targets: 39 videos with no topics, plus videos missing timestamps.
Uses llama-server with Qwen3.6-27B-IQ2_M for fast topic generation.
"""

import json
import requests
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Config
INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
UNIFIED_TS_FILE = Path("/home/wubu/seymour-project/unified_timestamps.json")
LLAMA_URL = "http://localhost:18802/v1/chat/completions"
MODEL = "Qwen3.6-27B-UD-IQ2_M.gguf"
OUTPUT_INDEX = Path("/home/wubu/seymour-project/pre_seymour/index_with_topics.json")

# Topic categories from Seymour project
EXISTING_TOPICS = [
    "Gaming", "Marvel Rivals", "Death Stranding", "RoboCop Rogue City",
    "Schedule I", "Poppy Playtime", "Five Nights at Freddy's", "TF2",
    "Bully Scholarship Edition", "Alan Wake 2", "Red Dead Redemption 2",
    "Minecraft", "Fortnite", "Horror Games", "Retro Gaming",
    "AI Content", "Music Videos", "News/Commentary", "IRL/Streaming",
    "Technology", "Programming", "Art/Creativity", "Food/Cooking",
    "Conspiracy/Paranormal", "Internet Culture", "Memes", "Penny/Superstition",
    "StrongBad", "Homestar Runner", "Nintendo", "PlayStation", "PC Gaming",
    "Speedrunning", "Let's Play", "Walkthrough", "Blind Playthrough",
    "Multiplayer", "Co-op", "Ranked/Competitive", "Modding",
    "Game Development", "AI/ML", "Supercapacitor/Hybrid EV"
]

SYSTEM_PROMPT = f"""You are Seymour, a topic tagger for WuBu Streams video content.
Analyze the video title and transcript excerpt, then assign 3-5 relevant topics.
Use ONLY topics from this predefined list (case-sensitive):
{', '.join(EXISTING_TOPICS)}

You may also add 1-2 new specific topics if needed (e.g., specific game names, character names).
Output format: JSON array of strings only. No explanation."""

def load_index():
    with open(INDEX_FILE) as f:
        return json.load(f)

def load_unified_ts():
    if UNIFIED_TS_FILE.exists():
        with open(UNIFIED_TS_FILE) as f:
            return json.load(f).get("videos", {})
    return {}

def get_transcript_excerpt(video_id, max_chars=500):
    """Get transcript excerpt for context."""
    index = load_index()
    if video_id not in index:
        return ""
    
    transcript_path = index[video_id].get("transcript_path", "")
    if not transcript_path:
        return ""
    
    try:
        with open(transcript_path) as f:
            content = f.read(max_chars)
        return content[:max_chars]
    except:
        return ""

print_lock = threading.Lock()
def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def generate_topics(video_id, title, transcript_excerpt):
    """Generate topics using local LLM."""
    
    user_prompt = f"""Video ID: {video_id}
Title: {title}
Transcript excerpt: {transcript_excerpt[:500]}

Assign 3-5 topics from the allowed list. Output JSON array only."""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 200,
        "stream": False
    }
    
    try:
        response = requests.post(LLAMA_URL, json=payload, timeout=300)  # Increased to 5 minutes
        if response.status_code == 200:
            result = response.json()
            content = result["choices"][0]["message"]["content"].strip()
            
            # Try to parse JSON
            try:
                topics = json.loads(content)
                if isinstance(topics, list):
                    return topics
            except:
                # Try to extract from text
                import re
                matches = re.findall(r'"([^"]+)"', content)
                if matches:
                    return matches
                # Fallback: split by comma/newline
                return [t.strip().strip('"') for t in content.replace('\n', ',').split(',') if t.strip()]
    except Exception as e:
        safe_print(f"Error generating topics for {video_id}: {e}")
    
    return []

def process_videos_needing_topics(limit=None, workers=4):
    """Process all videos missing topics."""
    index = load_index()
    unified_ts = load_unified_ts()
    
    # Find videos needing topics
    candidates = []
    for vid, info in index.items():
        topics = info.get("topics", [])
        if not topics or (isinstance(topics, list) and len(topics) == 0):
            # Priority: videos with transcripts and timestamps
            has_ts = vid in unified_ts and unified_ts[vid].get("has_timestamps", False)
            has_transcript = info.get("has_transcript", False)
            priority = (has_ts + has_transcript * 2)  # Higher = more priority
            
            candidates.append({
                "video_id": vid,
                "title": info.get("title", ""),
                "priority": priority,
                "has_ts": has_ts,
                "has_transcript": has_transcript
            })
    
    # Sort by priority (highest first)
    candidates.sort(key=lambda x: x["priority"], reverse=True)
    
    if limit:
        candidates = candidates[:limit]
    
    safe_print(f"Found {len(candidates)} videos needing topics")
    
    results = {}
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_vid = {}
        for c in candidates:
            excerpt = get_transcript_excerpt(c["video_id"])
            future = executor.submit(generate_topics, c["video_id"], c["title"], excerpt)
            future_to_vid[future] = c
        
        for future in as_completed(future_to_vid):
            c = future_to_vid[future]
            topics = future.result()
            
            if topics:
                results[c["video_id"]] = topics
                safe_print(f"✓ {c['video_id']}: {topics}")
            else:
                safe_print(f"✗ {c['video_id']}: Failed to generate topics")
    
    return results

def update_index_with_topics(new_topics):
    """Update the main index with new topics."""
    with open(INDEX_FILE) as f:
        index = json.load(f)
    
    updated = 0
    for vid, topics in new_topics.items():
        if vid in index:
            index[vid]["topics"] = topics
            updated += 1
    
    # Save updated index
    with open(OUTPUT_INDEX, "w") as f:
        json.dump(index, f, indent=2)
    
    # Also backup and replace original
    import shutil
    shutil.copy2(INDEX_FILE, INDEX_FILE.with_suffix(".json.bak"))
    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)
    
    safe_print(f"Updated {updated} videos in index")
    safe_print(f"Backup: {INDEX_FILE.with_suffix('.json.bak')}")
    safe_print(f"New index: {OUTPUT_INDEX}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fill missing topic tags using LLM")
    parser.add_argument("--limit", type=int, help="Max videos to process")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    parser.add_argument("--dry-run", action="store_true", help="Don't update index")
    parser.add_argument("--single", help="Process single video ID")
    args = parser.parse_args()
    
    if args.single:
        index = load_index()
        if args.single not in index:
            print(f"Video {args.single} not found")
            return
        info = index[args.single]
        excerpt = get_transcript_excerpt(args.single)
        topics = generate_topics(args.single, info["title"], excerpt)
        print(f"Generated topics: {topics}")
        return
    
    print("Starting topic gap filling...")
    new_topics = process_videos_needing_topics(limit=args.limit, workers=args.workers)
    
    if new_topics and not args.dry_run:
        update_index_with_topics(new_topics)
    elif args.dry_run:
        print(f"\nDry run - would update {len(new_topics)} videos:")
        for vid, topics in new_topics.items():
            print(f"  {vid}: {topics}")

if __name__ == "__main__":
    main()