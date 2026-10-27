#!/usr/bin/env python3
"""
Seymour Pipe v4 — Smart Pipeline
=================================
For each video:
1. Check if engagement panel transcript exists (browser)
2. If yes → extract it (instant)
3. If no → download OGG audio → upload to HF Whisper API → get transcript
4. Save as .txt + .srt

This is FAST because:
- No local whisper (GPU-powered)
- OGG is ~10x smaller than WAV
- ~2-3 min per video average

Storage: just text files (~50MB total for all 468 videos)
"""

import os
import sys
import json
import time
import subprocess
import requests
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
import re
import yt_dlp

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
AUDIO_DIR = OUTPUT_DIR / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")

def get_video_id(url):
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def check_timedtext_captions(video_id):
    """Check if YouTube timedtext API has captions."""
    url = f'https://www.youtube.com/api/timedtext?lang=en&v={video_id}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode('utf-8')
        return 'text' in data and len(data) > 100
    except:
        return False

def download_audio_ogg(url, video_id):
    """Download audio as OGG Vorbis."""
    ogg_path = AUDIO_DIR / f"{video_id}.ogg"
    
    if ogg_path.exists() and ogg_path.stat().st_size > 100000:
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
    
    print(f"  Downloading OGG...")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    if not ogg_path.exists():
        for f in AUDIO_DIR.glob(f"{video_id}*"):
            f.rename(ogg_path)
            break
    
    size_mb = ogg_path.stat().st_size / 1024 / 1024
    print(f"  Audio: {size_mb:.1f} MB")
    return ogg_path

def transcribe_with_hf(ogg_path, hf_token):
    """Transcribe using HuggingFace Inference API (GPU-powered)."""
    if not hf_token:
        return None
    
    api_url = "https://api-inference.huggingface.co/models/openai/whisper-large-v3-turbo"
    headers = {"Authorization": f"Bearer {hf_token}"}
    
    with open(ogg_path, 'rb') as f:
        data = f.read()
    
    print(f"  Sending to HF Whisper API ({len(data)/1024/1024:.1f} MB)...")
    response = requests.post(api_url, headers=headers, data=data, timeout=300)
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, dict) and 'text' in result:
            return result['text']
        elif isinstance(result, list) and len(result) > 0:
            return result[0].get('text', '')
    
    print(f"  HF API error: {response.status_code} - {response.text[:200]}")
    return None

def save_transcript(title, video_id, text, source):
    """Save transcript to file."""
    safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:50]
    
    txt_path = OUTPUT_DIR / f"{safe}_{video_id}_transcript.txt"
    with open(txt_path, 'w') as f:
        f.write(f"# {title}\n# {video_id}\n# Source: {source}\n\n{text}")
    
    print(f"  Saved: {txt_path}")
    return txt_path

def load_progress():
    progress_file = OUTPUT_DIR / "v4_progress.json"
    if progress_file.exists():
        with open(progress_file) as f:
            return json.load(f)
    return {"done": [], "failed": [], "skipped": []}

def save_progress(progress):
    with open(OUTPUT_DIR / "v4_progress.json", 'w') as f:
        json.dump(progress, f, indent=2)

def process_video(url, hf_token, progress):
    """Process single video through the pipeline."""
    video_id = get_video_id(url)
    if not progress:
        return None, "no_video_id"
    
    # Get video info
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'untitled')
        except:
            title = "untitled"
    
    print(f"\n{'='*60}")
    print(f"Processing: {title[:60]}")
    print(f"  URL: {url}")
    
    # Step 1: Check timedtext captions
    print(f"  Checking timedtext...")
    has_captions = check_timedtext_captions(video_id)
    
    if has_captions:
        print(f"  ✅ Has timedtext captions!")
        # Extract them
        url_tt = f'https://www.youtube.com/api/timedtext?lang=en&v={video_id}'
        req = urllib.request.Request(url_tt, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = resp.read().decode('utf-8')
        root = ET.fromstring(data)
        text = ' '.join(t.text or '' for t in root.findall('text'))
        save_transcript(title, video_id, text, "youtube_timedtext")
        return {"title": title, "video_id": video_id, "method": "timedtext", "words": len(text.split())}, None
    
    # Step 2: No captions → download OGG + cloud whisper
    print(f"  ⏳ No timedtext captions. Will download OGG + use HF API.")
    
    try:
        ogg_path = download_audio_ogg(url, video_id)
    except Exception as e:
        print(f"  ❌ Download failed: {e}")
        return None, f"download_error: {str(e)[:100]}"
    
    # Transcribe with HF
    text = transcribe_with_hf(ogg_path, hf_token)
    
    if text:
        save_transcript(title, video_id, text, "hf_whisper_api")
        # Optionally remove audio file to save space
        try:
            ogg_path.unlink()
            print(f"  Cleaned up audio file")
        except:
            pass
        return {"title": title, "video_id": video_id, "method": "hf_api", "words": len(text.split())}, None
    else:
        return None, "hf_api_failed"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seymour Pipe v4")
    parser.add_argument("--hf-token", default=os.environ.get("HF_TOKEN", ""), help="HuggingFace API token")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--end", type=int, default=0, help="End index (0=all)")
    args = parser.parse_args()
    
    if not args.hf_token:
        print("ERROR: No HuggingFace token. Set HF_TOKEN env var or --hf-token")
        print("Get a free token at: https://huggingface.co/settings/tokens")
        sys.exit(1)
    
    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if args.end > 0:
        urls = urls[args.start:args.end]
    else:
        urls = urls[args.start:]
    
    progress = load_progress()
    
    print(f"Seymour Pipe v4 — Processing {len(urls)} videos")
    print(f"  HF Token: {args.hf_token[:10]}...")
    print(f"  Start: {args.start}, End: {args.end or 'all'}")
    
    done = 0
    failed = 0
    
    for i, url in enumerate(urls):
        vid = get_video_id(url)
        
        # Skip if already done
        if vid in [p.get("video_id") for p in progress["done"]]:
            print(f"\n[{i+1}/{len(urls)}] SKIP (already done): {vid}")
            continue
        
        print(f"\n[{i+1}/{len(urls)}]")
        
        try:
            result, error = process_video(url, args.hf_token, progress.get("last_index"))
            
            if result:
                progress["done"].append(result)
                done += 1
                print(f"  ✅ {result['words']} words ({result['method']})")
            else:
                progress["failed"].append({"url": url, "video_id": vid, "error": error})
                failed += 1
                print(f"  ❌ {error}")
        except Exception as e:
            progress["failed"].append({"url": url, "video_id": vid, "error": str(e)[:100]})
            failed += 1
            print(f"  ❌ {e}")
        
        # Save progress every 5 videos
        if (i + 1) % 5 == 0:
            save_progress(progress)
            print(f"\n📊 Progress: {done} done, {failed} failed, {len(urls)-i-1} remaining\n")
    
    save_progress(progress)
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"  Done: {done}")
    print(f"  Failed: {failed}")
    total_words = sum(r.get("words", 0) for r in progress["done"])
    print(f"  Total words: {total_words}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
