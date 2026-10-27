#!/usr/bin/env python3
"""
YouTube Engagement Panel Transcript Absorber
Uses browser automation to check every video for the "In this video" transcript feature.
Saves extracted transcripts to captions/ directory.

This runs as a persistent browser session — navigates to each video, extracts, saves.
"""

import os
import sys
import json
import time
import subprocess
import re
from pathlib import Path

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")

def main():
    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Engagement Panel Transcript Absorber")
    print(f"=" * 60)
    print(f"Videos to check: {len(urls)}")
    print(f"")
    
    # Load progress
    progress_file = OUTPUT_DIR / "engagement_progress.json"
    if progress_file.exists():
        with open(progress_file) as f:
            progress = json.load(f)
        done_ids = set(progress.get("done", []))
    else:
        progress = {"done": [], "has_transcript": [], "no_transcript": []}
        done_ids = set()
    
    # This script provides instructions for the browser automation
    # It outputs commands that can be executed via Hermes browser tools
    
    print(f"Already processed: {len(done_ids)}")
    print(f"Remaining: {len(urls) - len(done_ids)}")
    print(f"")
    
    # Find next video to process
    for i, url in enumerate(urls):
        vid_match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
        if not vid_match:
            continue
        vid = vid_match.group(1)
        
        if vid in done_ids:
            continue
        
        print(f"[{i+1}/{len(urls)}] NEXT: {vid}")
        print(f"URL: {url}")
        return  # Process one at a time via browser tools
    
    print(f"All videos processed!")
    print(f"Has transcript: {len(progress.get('has_transcript', []))}")
    print(f"No transcript: {len(progress.get('no_transcript', []))}")

if __name__ == "__main__":
    main()
