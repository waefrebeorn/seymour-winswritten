#!/usr/bin/env python3
"""
Whisper Fallback Batch Processor — QUALITY MODE
Processes videos that don't have engagement panels
Uses yt-dlp to download audio + faster_whisper for transcription
NO SKIPPING - every video gets processed
QUALITY: small.en model, 64k audio, validation checks
"""

import subprocess
import os
import sys
import argparse
from pathlib import Path
import json

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument('--input', default='/home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_videos.txt')
parser.add_argument('--model', default='small.en', choices=['tiny.en', 'small.en', 'medium.en'])
parser.add_argument('--min-words', type=int, default=100, help='Minimum words for valid transcript')
args = parser.parse_args()

VIDEO_IDS_FILE = args.input
OUTPUT_DIR = Path('/home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_transcripts')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR = Path('/home/wubu/seymour-project/whiteboard/seymour-pipe/audio')
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Use decent bitrate (64k) for quality - still manageable size
# 64k mp3 = ~2.8 MB per minute, so 3 hours = ~500 MB (manageable)
AUDIO_BITRATE = '64k'

def download_audio(video_id):
    """Download audio using yt-dlp with decent quality"""
    audio_path = AUDIO_DIR / f"{video_id}.mp3"
    if audio_path.exists() and audio_path.stat().st_size > 10000:
        return audio_path
    
    url = f"https://www.youtube.com/watch?v={video_id}"
    cmd = [
        'yt-dlp',
        '--cookies', '/home/wubu/seymour-project/whiteboard/seymour-pipe/cookies.txt',
        '--js-runtimes', 'node:/usr/bin/node',
        '--remote-components', 'ejs:github',
        '--extractor-args', 'youtube:player_client=web_creator,web_embedded',
        '-x', '--audio-format', 'mp3',
        '--audio-quality', '5',  # ~64k bitrate
        '-o', str(AUDIO_DIR / f"{video_id}.%(ext)s"),
        '--no-playlist',
        url
    ]
    try:
        # 4 hours max for download (streams can be 6+ hours)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if result.returncode == 0 and audio_path.exists() and audio_path.stat().st_size > 10000:
            print(f"  Downloaded: {video_id} ({audio_path.stat().st_size/1024/1024:.1f} MB)")
            return audio_path
        else:
            print(f"  Download failed for {video_id}: {result.stderr[:500]}")
            if audio_path.exists():
                audio_path.unlink()
            return None
    except subprocess.TimeoutExpired:
        print(f"  Download timeout (4h) for {video_id}")
        return None
    except Exception as e:
        print(f"  Error downloading {video_id}: {e}")
        return None

def transcribe_audio(audio_path, video_id):
    """Transcribe using faster_whisper with quality model"""
    output_path = OUTPUT_DIR / f"{video_id}_whisper.txt"
    if output_path.exists() and output_path.stat().st_size > 1000:
        print(f"  Already transcribed: {video_id} ({output_path.stat().st_size} bytes)")
        return output_path
    
    # Write transcription script
    script = f'''
import sys
from faster_whisper import WhisperModel

try:
    m = WhisperModel('{args.model}', device='cpu', compute_type='int8')
    segs, info = m.transcribe('{audio_path}', beam_size=5, vad_filter=True, vad_parameters=dict(min_silence_duration_ms=400, threshold=0.5))
    segments = []
    for s in segs:
        if s.text.strip():
            segments.append(f"[{{int(s.start//60):02d}}:{{int(s.start%60):02d}}] {{s.text.strip()}}")
    text = "\\n".join(segments)
    word_count = len(text.split())
    if word_count < {args.min_words}:
        print(f"TRANSCRIBE REJECTED: only {{word_count}} words (min {args.min_words})", file=sys.stderr)
        sys.exit(2)
    with open('{output_path}', 'w') as f:
        f.write(text)
    print(f"Transcribed {{len(text)}} chars, {{word_count}} words")
except Exception as e:
    print(f"TRANSCRIBE ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
'''
    script_path = AUDIO_DIR / f"transcribe_{video_id}.py"
    with open(script_path, 'w') as f:
        f.write(script)
    
    try:
        # 4 hours max for transcription
        result = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=14400)
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 1000:
            print(f"  Transcribed: {video_id} ({output_path.stat().st_size} bytes)")
            return output_path
        elif result.returncode == 2:
            print(f"  Rejected (too short): {video_id} - {result.stderr.strip()}")
            return None
        else:
            print(f"  Transcription failed for {video_id}: {result.stderr[:500]}")
            if result.stdout:
                print(f"  Stdout: {result.stdout[:500]}")
            if output_path.exists():
                output_path.unlink()
            return None
    except subprocess.TimeoutExpired:
        print(f"  Transcription timeout (4h) for {video_id}")
        return None
    except Exception as e:
        print(f"  Error transcribing {video_id}: {e}")
        return None
    finally:
        if script_path.exists():
            script_path.unlink()

def main():
    import sys
    import re
    print("DEBUG: Starting main()", flush=True)
    sys.stdout.flush()
    # Load video IDs
    print(f"DEBUG: Reading input file {VIDEO_IDS_FILE}", flush=True)
    sys.stdout.flush()
    with open(VIDEO_IDS_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    # Extract video IDs from URLs
    video_ids = []
    for url in urls:
        match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
        if match:
            video_ids.append(match.group(1))
        else:
            print(f"  WARNING: Could not extract video ID from {url}", flush=True)
    
    print(f"DEBUG: Loaded {len(video_ids)} video IDs from {len(urls)} URLs", flush=True)
    sys.stdout.flush()
    
    print(f"Processing {len(video_ids)} videos for Whisper fallback (NO SKIPPING)...", flush=True)
    print(f"Model: {args.model}, Min words: {args.min_words}, Audio bitrate: {AUDIO_BITRATE}", flush=True)
    sys.stdout.flush()
    
    success = 0
    failed = 0
    rejected = 0
    
    for i, video_id in enumerate(video_ids):
        print(f"DEBUG: Loop iteration {i+1}/{len(video_ids)} for {video_id}", flush=True)
        sys.stdout.flush()
        print(f"\n[{i+1}/{len(video_ids)}] {video_id}", flush=True)
        sys.stdout.flush()
        
        # Download audio
        print(f"  Downloading audio...", flush=True)
        sys.stdout.flush()
        audio_path = download_audio(video_id)
        if not audio_path:
            failed += 1
            continue
        
        # Transcribe
        print(f"  Transcribing with {args.model}...")
        result = transcribe_audio(audio_path, video_id)
        if result:
            success += 1
        elif result is None and audio_path and audio_path.exists():
            # Check if it was rejected for too few words
            # We can't easily distinguish, so count as failed
            failed += 1
        else:
            failed += 1
        
        # Clean up audio to save space
        if audio_path and audio_path.exists():
            audio_path.unlink()
    
    print(f"\n=== Complete ===")
    print(f"Success: {success}")
    print(f"Failed: {failed}")
    print(f"Output: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()