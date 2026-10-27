#!/usr/bin/env python3
"""
video_metadata_extractor.py — Extract comprehensive YouTube metadata for all videos.
Uses yt-dlp to fetch: title, description, tags, categories, chapters, thumbnails, 
duration, upload date, view count, like count, comments, etc.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
OUTPUT_DIR = Path("/home/wubu/seymour-project/video_metadata")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROGRESS_FILE = OUTPUT_DIR / "extraction_progress.json"
COOKIES_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/cookies.txt")

# yt-dlp fields to extract
YTDLP_FIELDS = [
    "id", "title", "description", "duration", "duration_string",
    "upload_date", "uploader", "uploader_id", "channel_id", "channel_url",
    "view_count", "like_count", "comment_count", "repost_count",
    "tags", "categories", "age_limit", "live_status", "is_live",
    "availability", "thumbnail", "thumbnails", "webpage_url",
    "chapters", "heatmap", "automatic_captions", "subtitles",
    "formats", "format_id", "ext", "resolution", "fps", "vcodec", "acodec",
    "abr", "vbr", "filesize", "tbr", "protocol", "url"
]

# Fields we actually want to keep (smaller subset)
KEEP_FIELDS = [
    "id", "title", "description", "duration", "duration_string",
    "upload_date", "uploader", "uploader_id", "channel_id",
    "view_count", "like_count", "comment_count",
    "tags", "categories", "age_limit", "live_status", "is_live",
    "thumbnail", "thumbnails", "webpage_url",
    "chapters", "heatmap", "automatic_captions", "subtitles",
    "formats",  # we'll filter this down
]

print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    with print_lock:
        print(*args, **kwargs)

def extract_video_metadata(video_id, max_retries=3):
    """Extract metadata for a single video using yt-dlp."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    cmd = [
        "yt-dlp",
        "--cookies", str(COOKIES_FILE),
        "--no-playlist",
        "--ignore-errors",
        "--no-warnings",
        "--skip-download",
        "--print-json",
        "--no-simulate",
        url
    ]
    
    for attempt in range(max_retries):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout.strip())
                # Filter to keep only needed fields
                filtered = {k: v for k, v in data.items() if k in KEEP_FIELDS}
                
                # Simplify formats - keep only best video+audio
                if "formats" in filtered:
                    filtered["formats"] = simplify_formats(filtered["formats"])
                
                return {"video_id": video_id, "success": True, "data": filtered}
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # exponential backoff
                    continue
                return {"video_id": video_id, "success": False, "error": error_msg}
                
        except subprocess.TimeoutExpired:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"video_id": video_id, "success": False, "error": "Timeout"}
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"video_id": video_id, "success": False, "error": f"JSON decode error: {e}"}
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"video_id": video_id, "success": False, "error": str(e)}
    
    return {"video_id": video_id, "success": False, "error": "Max retries exceeded"}

def simplify_formats(formats):
    """Keep only the most relevant format info."""
    if not formats:
        return []
    
    simplified = []
    for f in formats:
        # Only keep formats with both video and audio or best of each
        if f.get("vcodec") != "none" and f.get("acodec") != "none":
            simplified.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "resolution": f.get("resolution"),
                "fps": f.get("fps"),
                "vcodec": f.get("vcodec"),
                "acodec": f.get("acodec"),
                "filesize": f.get("filesize"),
                "tbr": f.get("tbr"),
                "protocol": f.get("protocol"),
                "url": f.get("url")[:100] + "..." if f.get("url") else None  # truncate URL
            })
    return simplified[:10]  # max 限制最多10个格式

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": [], "failed": [], "pending": []}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract YouTube metadata for all videos")
    parser.add_argument("--workers", type=int, default=4, help="Parallel workers")
    parser.add_argument("--limit", type=int, help="Limit number of videos to process")
    parser.add_argument("--resume", action="store_true", help="Resume from progress file")
    parser.add_argument("--video-id", help="Process single video ID")
    args = parser.parse_args()
    
    # Load index
    with open(INDEX_FILE) as f:
        index = json.load(f)
    
    video_ids = list(index.keys())
    
    if args.video_id:
        video_ids = [args.video_id] if args.video_id in video_ids else []
        if not video_ids:
            print(f"Video ID {args.video_id} not found in index")
            return
    
    # Load progress if resuming
    if args.resume:
        progress = load_progress()
        completed = set(progress.get("completed", []))
        video_ids = [v for v in video_ids if v not in completed]
        safe_print(f"Resuming: {len(completed)} done, {len(video_ids)} remaining")
    else:
        progress = {"completed": [], "failed": [], "pending": video_ids.copy()}
    
    if args.limit:
        video_ids = video_ids[:args.limit]
    
    safe_print(f"Processing {len(video_ids)} videos with {args.workers} workers...")
    
    completed_count = len(progress.get("completed", []))
    failed_count = len(progress.get("failed", []))
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_vid = {executor.submit(extract_video_metadata, vid): vid for vid in video_ids}
        
        for future in as_completed(future_to_vid):
            vid = future_to_vid[future]
            result = future.result()
            
            if result["success"]:
                # Save individual file
                out_file = OUTPUT_DIR / f"{vid}.json"
                with open(out_file, "w") as f:
                    json.dump(result["data"], f, indent=2)
                
                progress["completed"].append(vid)
                completed_count += 1
                safe_print(f"[{completed_count + failed_count}/{len(video_ids) + completed_count + failed_count}] ✓ {vid}: {result['data'].get('title', 'N/A')[:60]}")
            else:
                progress["failed"].append({"video_id": vid, "error": result["error"]})
                failed_count += 1
                safe_print(f"[{completed_count + failed_count}/{len(video_ids) + completed_count + failed_count}] ✗ {vid}: {result['error'][:80]}")
            
            # Save progress every 10 videos
            if (completed_count + failed_count) % 10 == 0:
                save_progress(progress)
    
    # Final save
    save_progress(progress)
    
    # Create summary
    summary = {
        "total_processed": len(video_ids),
        "successful": completed_count,
        "failed": failed_count,
        "success_rate": f"{completed_count / (completed_count + failed_count) * 100:.1f}%" if (completed_count + failed_count) > 0 else "0%",
        "output_dir": str(OUTPUT_DIR)
    }
    
    with open(OUTPUT_DIR / "extraction_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    safe_print(f"\n=== Extraction Complete ===")
    safe_print(f"Successful: {completed_count}")
    safe_print(f"Failed: {failed_count}")
    safe_print(f"Output: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()