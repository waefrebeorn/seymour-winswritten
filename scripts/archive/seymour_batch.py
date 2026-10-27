#!/usr/bin/env python3
"""
Seymour Pipe Batch Processor
Processes all WuBu Streams videos: OGG audio → transcript → H.265 clips

Usage:
    python3 seymour_batch.py [--model tiny] [--top-clips 5] [--start 0] [--end 10]
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))
from seymour_pipe import SeymourPipe

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
URL_FILE = OUTPUT_DIR / "all_videos.txt"
PROGRESS_FILE = OUTPUT_DIR / "batch_progress.json"

def load_processed():
    """Load progress from previous run."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"processed": [], "failed": [], "last_index": 0}

def save_progress(progress):
    """Save progress."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seymour Pipe Batch Processor")
    parser.add_argument("--model", default="tiny", help="Whisper model: tiny/small/medium")
    parser.add_argument("--top-clips", type=int, default=0, help="H.265 clips per video (0=skip)")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--end", type=int, default=0, help="End index (0=all)")
    args = parser.parse_args()

    if not URL_FILE.exists():
        print(f"ERROR: {URL_FILE} not found")
        sys.exit(1)

    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]

    if args.end > 0:
        urls = urls[args.start:args.end]
    else:
        urls = urls[args.start:]

    progress = load_processed()
    pipe = SeymourPipe(args.model)

    print(f"{'='*60}")
    print(f"SEYMOUR PIPE BATCH — {len(urls)} videos")
    print(f"  Model: {args.model}")
    print(f"  H.265 clips: {args.top_clips} per video")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}\n")

    success = 0
    failed = 0
    total_words = 0
    start_time = time.time()

    for i, url in enumerate(urls):
        elapsed = time.time() - start_time
        avg_time = elapsed / (i + 1) if i > 0 else 0
        eta = avg_time * (len(urls) - i - 1)

        print(f"\n[Batch {i+1}/{len(urls)}] ETA: {eta/60:.0f}min | Elapsed: {elapsed/60:.0f}min")

        try:
            result = pipe.process(url, export_clips=(args.top_clips > 0), top_n=args.top_clips)
            words = len(result["formatted_transcript"].split())
            total_words += words
            success += 1

            progress["processed"].append({
                "url": url,
                "title": result["info"]["title"],
                "words": words,
                "clips": len(result["moments"]),
                "exported": len(result["exported_clips"]),
            })
        except Exception as e:
            print(f"[Batch] ERROR: {e}")
            failed += 1
            progress["failed"].append({"url": url, "error": str(e)[:200]})

        # Save progress every 5 videos
        if (i + 1) % 5 == 0:
            save_progress(progress)
            print(f"[Batch] Progress saved. Success: {success}, Failed: {failed}, Words: {total_words}")

    # Final save
    save_progress(progress)

    total_time = time.time() - start_time
    print(f"\n\n{'='*60}")
    print(f"BATCH COMPLETE — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")
    print(f"  Total videos: {len(urls)}")
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Total words: {total_words}")
    print(f"  Total time: {total_time/60:.0f} minutes")
    print(f"  Avg per video: {total_time/len(urls)/60:.1f} minutes")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
