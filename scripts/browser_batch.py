#!/usr/bin/env python3
"""
Batch YouTube Engagement Panel Transcript Extractor
===================================================
Reads video URLs from all_videos.txt, navigates each one in the browser,
extracts the "In this video" engagement panel transcript, and saves to file.

This script is designed to be called by the agent after each video is processed.
It tracks progress and outputs the next video to process.

Usage:
    python3 browser_batch.py status     — Show current progress
    python3 browser_batch.py next       — Get next video to process
    python3 browser_batch.py mark_done <video_id> <title> <words>  — Mark video as done
    python3 browser_batch.py mark_no_panel <video_id>            — Mark as no panel
    python3 browser_batch.py mark_failed <video_id> <error>       — Mark as failed
"""

import json
import sys
import re
import os
from pathlib import Path

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")
PROGRESS_FILE = OUTPUT_DIR / "browser_extract_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": [], "no_panel": [], "failed": [], "last_index": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_video_id(url):
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def get_progress():
    """Return counts and remaining videos"""
    progress = load_progress()
    done_ids = {p.get("video_id") for p in progress.get("done", [])}
    no_panel_ids = {p.get("video_id") for p in progress.get("no_panel", [])}
    failed_ids = {p.get("video_id") for p in progress.get("failed", [])}
    
    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    remaining = []
    for i, url in enumerate(urls):
        vid = get_video_id(url)
        if vid and vid not in done_ids and vid not in no_panel_ids and vid not in failed_ids:
            remaining.append({"index": i, "url": url, "video_id": vid})
    
    return {
        "total": len(urls),
        "done": len(progress.get("done", [])),
        "no_panel": len(progress.get("no_panel", [])),
        "failed": len(progress.get("failed", [])),
        "remaining": len(remaining),
        "next": remaining[0] if remaining else None
    }

def mark_done(video_id, title, words, source="engagement_panel"):
    progress = load_progress()
    progress["done"].append({
        "video_id": video_id,
        "title": title,
        "words": words,
        "source": source
    })
    save_progress(progress)
    print(f"✅ Marked done: {video_id} ({words} words)")

def mark_no_panel(video_id):
    progress = load_progress()
    progress["no_panel"].append({"video_id": video_id})
    save_progress(progress)
    print(f"⚠️ Marked no panel: {video_id}")

def mark_failed(video_id, error):
    progress = load_progress()
    progress["failed"].append({"video_id": video_id, "error": error})
    save_progress(progress)
    print(f"❌ Marked failed: {video_id} ({error})")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 browser_batch.py [status|next|mark_done|mark_no_panel|mark_failed]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        info = get_progress()
        print(f"Progress: {info['done']} done, {info['no_panel']} no panel, {info['failed']} failed")
        print(f"Remaining: {info['remaining']} / {info['total']}")
        if info['next']:
            print(f"Next: {info['next']['video_id']} — {info['next']['url']}")
    
    elif cmd == "next":
        info = get_progress()
        if info['next']:
            print(json.dumps(info['next']))
        else:
            print("ALL_DONE")
    
    elif cmd == "mark_done":
        if len(sys.argv) < 5:
            print("Usage: python3 browser_batch.py mark_done <video_id> <title> <words>")
            sys.exit(1)
        mark_done(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    
    elif cmd == "mark_no_panel":
        if len(sys.argv) < 3:
            print("Usage: python3 browser_batch.py mark_no_panel <video_id>")
            sys.exit(1)
        mark_no_panel(sys.argv[2])
    
    elif cmd == "mark_failed":
        if len(sys.argv) < 4:
            print("Usage: python3 browser_batch.py mark_failed <video_id> <error>")
            sys.exit(1)
        mark_failed(sys.argv[2], sys.argv[3])
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
