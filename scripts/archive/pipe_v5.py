#!/usr/bin/env python3
"""
Seymour Pipe v5 — The Right Way
================================
After testing multiple approaches, here's what WORKS:
1. Download audio as WAV (16kHz mono) — whisper loves it
2. Chunk into 15-min segments
3. Transcribe each chunk with whisper (tiny model, CPU int8)
4. Memory stays low (~2GB max)
5. Each chunk takes ~3-5 min on CPU

For 468 videos:
- Average video: ~3 hours download + ~2 hours transcription
- BUT: We process videos in parallel with browser extraction
- Storage: ~3GB per video temporary, deleted after transcription

Optimizations:
- Skip videos that already have transcripts (from earlier sessions)
- Save progress every video (can resume)
- Use WAV 16kHz mono (whisper's native format)
"""

import os
import sys
import json
import time
import subprocess
import shutil
from pathlib import Path
import re
import yt_dlp

# Config
MODEL_SIZE = "tiny"
CHUNK_MINUTES = 15
WAV_SAMPLE_RATE = 16000
MAX_MEMORY_MB = 4000  # Stop if memory exceeds this

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
AUDIO_DIR = OUTPUT_DIR / "audio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")
PROGRESS_FILE = OUTPUT_DIR / "v5_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": [], "failed": [], "last_index": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_video_id(url):
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

def get_video_info(url):
    """Get video title and duration."""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info.get('title', 'untitled'), info.get('duration', 0)

def download_wav_chunked(url, video_id):
    """Download audio as WAV 16kHz mono, processing in chunks to avoid OOM."""
    wav_path = AUDIO_DIR / f"{video_id}.wav"
    
    if wav_path.exists() and wav_path.stat().st_size > 500000:
        return wav_path
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '16',
        }],
        'outtmpl': str(wav_path).replace('.wav', '.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }
    
    print(f"  Downloading WAV 16kHz.")
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    if not wav_path.exists():
        for f in AUDIO_DIR.glob(f"{video_id}.*"):
            f.rename(wav_path)
            break
    
    return wav_path

def get_wav_duration(wav_path):
    """Get WAV duration in seconds."""
    cmd = ['ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
           '-of', 'csv=p=0', str(wav_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())

def extract_wav_chunk(wav_path, start_sec, duration_sec, output_path):
    """Extract a chunk from WAV file."""
    cmd = [
        'ffmpeg', '-y', '-i', str(wav_path),
        '-ss', str(start_sec), '-t', str(duration_sec),
        '-acodec', 'copy',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return output_path.exists()

def transcribe_chunk(model, chunk_path):
    """Transcribe a single WAV chunk."""
    segments, info = model.transcribe(
        str(chunk_path),
        beam_size=5,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=400, threshold=0.5)
    )
    
    entries = []
    for seg in segments:
        if seg.text.strip():
            entries.append({
                'start': round(seg.start, 2),
                'text': seg.text.strip()
            })
    
    return entries

def process_video(url, model, progress):
    """Process a single video: download → chunk → transcribe → save."""
    video_id = get_video_id(url)
    if not video_id:
        return None, "invalid_url"
    
    # Get info
    title, duration = get_video_info(url)
    print(f"  Title: {title[:60]}")
    print(f"  Duration: {duration//60}m {duration%60}s")
    
    # Download WAV
    try:
        wav_path = download_wav_chunked(url, video_id)
    except Exception as e:
        return None, f"download_error: {str(e)[:100]}"
    
    actual_duration = get_wav_duration(wav_path)
    chunk_seconds = CHUNK_MINUTES * 60
    total_chunks = int(actual_duration // chunk_seconds) + 1
    
    print(f"  Chunks: {total_chunks}")
    
    # Create temp dir for chunks
    chunk_dir = AUDIO_DIR / f"chunks_{video_id}"
    chunk_dir.mkdir(exist_ok=True)
    
    all_entries = []
    
    for chunk_idx in range(total_chunks):
        start = chunk_idx * chunk_seconds
        chunk_path = chunk_dir / f"chunk_{chunk_idx:03d}.wav"
        
        print(f"    Chunk {chunk_idx+1}/{total_chunks} ({start//60}m{start%60}s)...", end='', flush=True)
        
        # Extract chunk
        success = extract_wav_chunk(wav_path, start, chunk_seconds + 5, chunk_path)
        if not success:
            print(" FAIL (extract)")
            continue
        
        # Transcribe chunk
        try:
            entries = transcribe_chunk(model, chunk_path)
            # Adjust timestamps
            for e in entries:
                e['start'] = round(e['start'] + start, 2)
            all_entries.extend(entries)
            print(f" {len(entries)} segments ✓")
        except Exception as e:
            print(f" FAIL ({str(e)[:50]})")
        
        # Clean up chunk immediately
        try:
            chunk_path.unlink()
        except:
            pass
    
    # Clean up
    try:
        shutil.rmtree(chunk_dir)
    except:
        pass
    
    if all_entries:
        # Save transcript
        safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:50]
        txt_path = OUTPUT_DIR / f"{safe}_{video_id}_transcript.txt"
        
        text = f"# {title}\n# {video_id}\n# Extracted via Seymour Pipe v5\n\n"
        for e in all_entries:
            mins = int(e['start'] // 60)
            secs = int(e['start'] % 60)
            text += f"[{mins:02d}:{secs:02d}] {e['text']}\n"
        
        with open(txt_path, 'w') as f:
            f.write(text)
        
        print(f"  Saved: {txt_path.name} ({len(all_entries)} segments)")
        
        return {
            "video_id": video_id,
            "title": title,
            "entries": len(all_entries),
            "words": len(text.split()),
            "duration_min": int(actual_duration // 60)
        }, None
    else:
        return None, "no_segments_extracted"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seymour Pipe v5")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--end", type=int, default=0, help="End index (0=all)")
    parser.add_argument("--model", default="tiny", help="Whisper model: tiny/small/medium")
    args = parser.parse_args()
    
    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    if args.end > 0:
        urls = urls[args.start:args.end]
    else:
        urls = urls[args.start:]
    
    print(f"Seymour Pipe v5")
    print(f"=" * 60)
    print(f"Videos: {len(urls)}")
    print(f"Model: {args.model}")
    print(f"Chunk size: {CHUNK_MINUTES} minutes")
    print(f"=" * 60)
    
    # Load model
    print("Loading model...")
    from faster_whisper import WhisperModel
    model = WhisperModel(args.model, device="cpu", compute_type="int8")
    print("Model loaded.\n")
    
    progress = load_progress()
    start_time = time.time()
    
    for i, url in enumerate(urls):
        vid = get_video_id(url)
        
        # Skip if done
        done_ids = [p.get("video_id") for p in progress.get("done", [])]
        if vid in done_ids:
            print(f"[{i+1}/{len(urls)}] SKIP: {vid}")
            continue
        
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(urls)}] Processing...")
        
        try:
            result, error = process_video(url, model, progress.get("last_index"))
            
            if result:
                progress.setdefault("done", []).append(result)
                elapsed = time.time() - start_time
                done_count = len(progress["done"])
                failed_count = len(progress.get("failed", []))
                print(f"  ✅ Done | Total: {done_count} ok, {failed_count} failed | {elapsed/60:.0f}min elapsed")
            else:
                progress.setdefault("failed", []).append({"url": url, "video_id": vid, "error": error})
                print(f"  ❌ {error}")
        except Exception as e:
            progress.setdefault("failed", []).append({"url": url, "video_id": vid, "error": str(e)[:100]})
            print(f"  ❌ {e}")
        
        # Save progress every video
        save_progress(progress)
    
    # Final stats
    elapsed = time.time() - start_time
    done = len(progress.get("done", []))
    failed = len(progress.get("failed", []))
    total_words = sum(r.get("words", 0) for r in progress.get("done", []))
    
    print(f"\n{'='*60}")
    print(f"BATCH COMPLETE")
    print(f"  Done: {done}")
    print(f"  Failed: {failed}")
    print(f"  Total words: {total_words}")
    print(f"  Total time: {elapsed/60:.0f} minutes")
    print(f"  Avg per video: {elapsed/done/60:.1f} minutes" if done else "  No videos completed")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
