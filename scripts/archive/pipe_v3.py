#!/usr/bin/env python3
"""
Seymour Pipe v3 — Hybrid Transcription Pipeline
=================================================
Strategy:
1. Check if YouTube has auto-captions (fast, free, no storage)
2. If not, use cloud Whisper API (fast, no local CPU)
3. For both: save transcript + SRT

This is the right approach. The old approach (local whisper) was wrong because:
- 468 videos × 30min CPU time = 60+ days
- 468 videos × ~450MB OGG = 220GB storage

The right approach:
- Captioned videos: <30 seconds per video via browser
- Uncaptioned videos: ~2-5 minutes per video via cloud API
- Total: ~8-15 hours for all 468 videos
- Storage: just text files, <100MB total
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")
PROGRESS_FILE = OUTPUT_DIR / "pipeline_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": [], "failed": [], "no_captions": [], "has_captions": []}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_video_id(url):
    """Extract video ID from YouTube URL."""
    import re
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def download_audio_ogg(url, video_id, output_dir):
    """Download audio as OGG Vorbis (small file, fast)."""
    safe = video_id[:10]
    ogg_path = output_dir / f"{safe}_{video_id}.ogg"
    
    if ogg_path.exists():
        return ogg_path
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'vorbis',
            'preferredquality': '3',
        }],
        'outtmpl': str(ogg_path).replace('.ogg', '.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    import yt_dlp
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    if not ogg_path.exists():
        for f in output_dir.glob(f"*{video_id}*"):
            f.rename(ogg_path)
            break
    
    return ogg_path

def check_youtube_captions(video_id):
    """Check if YouTube has auto-captions for this video."""
    import urllib.request
    url = f'https://www.youtube.com/api/timedtext?lang=en&v={video_id}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('utf-8')
        if 'text' in data and len(data) > 100:
            return True
    except:
        pass
    return False

def extract_youtube_captions(video_id):
    """Extract existing YouTube captions via API."""
    import urllib.request
    import xml.etree.ElementTree as ET
    
    url = f'https://www.youtube.com/api/timedtext?lang=en&v={video_id}'
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req, timeout=10)
    data = resp.read().decode('utf-8')
    
    root = ET.fromstring(data)
    entries = []
    for text in root.findall('text'):
        start = float(text.get('start', 0))
        dur = float(text.get('dur', 0))
        text_content = text.text or ''
        text_content = text_content.replace('&#39;', "'").replace('&quot;', '"').replace('&amp;', '&')
        entries.append({
            'start': round(start, 2),
            'end': round(start + dur, 2),
            'text': text_content.strip()
        })
    
    return entries

def format_transcript(entries, title, video_id):
    """Format entries as human-readable transcript."""
    lines = [f"# {title}", f"# {video_id}", "# Extracted transcript", ""]
    for e in entries:
        mins = int(e['start'] // 60)
        secs = int(e['start'] % 60)
        lines.append(f"[{mins:02d}:{secs:02d}] {e['text']}")
    return '\n'.join(lines)

def format_srt(entries):
    """Format entries as SRT."""
    srt = []
    for i, e in enumerate(entries):
        start = e['start']
        end = e['end']
        
        sh = int(start // 3600)
        sm = int((start % 3600) // 60)
        ss = int(start % 60)
        sms = int((start % 1) * 1000)
        
        eh = int(end // 3600)
        em = int((end % 3600) // 60)
        es = int(end % 60)
        ems = int((end % 1) * 1000)
        
        srt.append(f"{i+1}")
        srt.append(f"{sh:02d}:{sm:02d}:{ss:02d},{sms:03d} --> {eh:02d}:{em:02d}:{es:02d},{ems:03d}")
        srt.append(e['text'])
        srt.append("")
    
    return '\n'.join(srt)

def transcribe_with_cloud_whisper(ogg_path, hf_token=None):
    """Use HuggingFace Inference API to transcribe audio."""
    api_url = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
    
    if not hf_token:
        return None
    
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    with open(ogg_path, 'rb') as f:
        data = f.read()
    
    response = requests.post(api_url, headers=headers, data=data, timeout=120)
    
    if response.status_code == 200:
        result = response.json()
        if 'text' in result:
            return result['text']
    
    return None

def main():
    if len(sys.argv) < 2:
        print("Seymour Pipe v3 — Hybrid Transcription Pipeline")
        print("")
        print("Usage:")
        print("  python3 pipe_v3.py check        — Check which videos have captions")
        print("  python3 pipe_v3.py extract      — Extract captions via browser")
        print("  python3 pipe_v3.py count        — Count caption availability")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "count":
        # Quick check: how many of our 468 videos have YouTube captions?
        with open(URL_FILE) as f:
            urls = [l.strip() for l in f if l.strip()]
        
        print(f"Checking {len(urls)} videos for caption availability...")
        
        has_caps = 0
        no_caps = 0
        
        for url in urls[:20]:  # Check first 20
            vid = get_video_id(url)
            has = check_youtube_captions(vid)
            if has:
                has_caps += 1
                print(f"  ✅ {vid}: HAS captions")
            else:
                no_caps += 1
                print(f"  ❌ {vid}: NO captions")
            time.sleep(0.5)  # Rate limit
        
        print(f"\nSample (first 20):")
        print(f"  Has captions: {has_caps}")
        print(f"  No captions: {no_caps}")
        print(f"  Estimated total with captions: {int(has_caps/20 * len(urls))} / {len(urls)}")
    
    elif cmd == "check":
        # Full check of all videos
        with open(URL_FILE) as f:
            urls = [l.strip() for l in f if l.strip()]
        
        print(f"Checking all {len(urls)} videos...")
        progress = {"has_captions": [], "no_captions": []}
        
        for i, url in enumerate(urls):
            vid = get_video_id(url)
            has = check_youtube_captions(vid)
            if has:
                progress["has_captions"].append(vid)
            else:
                progress["no_captions"].append(vid)
            
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(urls)} (has: {len(progress['has_captions'])}, no: {len(progress['no_captions'])})")
                save_progress(progress)
        
        save_progress(progress)
        print(f"\nFinal:")
        print(f"  Has captions: {len(progress['has_captions'])}")
        print(f"  No captions: {len(progress['no_captions'])}")

if __name__ == "__main__":
    main()
