#!/usr/bin/env python3
"""
vision_clip_extractor.py — Extract video clips optimized for vision model inference.
Uses yt-dlp section download + ffmpeg frame extraction at vision model's expected resolution.
Outputs frames at 896x896 (gemma-4-12B mmproj native resolution) in highly compressed WebP format.
"""

import json
import subprocess
import hashlib
import tempfile
import shutil
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import sys

# Configuration
PROJECT_ROOT = Path("/home/wubu/seymour-project")
UNIFIED_TS_FILE = PROJECT_ROOT / "unified_timestamps.json"
INDEX_FILE = PROJECT_ROOT / "pre_seymour/index.json"
CLIP_OUTPUT_DIR = PROJECT_ROOT / "vision_clips"
TEMP_DIR = Path("/tmp/vision_clips")

# Vision model specs (gemma-4-12B + mmproj)
VISION_RESOLUTION = (896, 896)  # Native resolution for gemma mmproj
FRAME_FORMAT = "webp"  # High compression, good quality
FRAME_QUALITY = 75  # WebP quality (1-100)
MAX_FRAMES_PER_CLIP = 4  # start, 1/3, 2/3, end
CLIP_MAX_DURATION = 30  # seconds max per clip

# yt-dlp settings
YTDLP_COOKIES = PROJECT_ROOT / "whiteboard/seymour-pipe/cookies.txt"
YTDLP_FORMAT = "worst[height<=480]"  # Low quality for fast download, we'll upscale

def load_unified_timestamps():
    if UNIFIED_TS_FILE.exists():
        with open(UNIFIED_TS_FILE) as f:
            return json.load(f).get("videos", {})
    return {}

def load_index():
    with open(INDEX_FILE) as f:
        return json.load(f)

def get_video_url(vid):
    return f"https://www.youtube.com/watch?v={vid}"

def extract_clip_frames(vid, start_s, end_s, output_dir, clip_id, keyword=""):
    """
    Extract frames from a video clip at vision model resolution.
    Uses yt-dlp section download for efficiency.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    duration = end_s - start_s
    if duration > CLIP_MAX_DURATION:
        end_s = start_s + CLIP_MAX_DURATION
        duration = CLIP_MAX_DURATION
    
    # Calculate frame timestamps (distributed across clip)
    if duration <= 5:
        frame_times = [0, duration/2, duration]
    else:
        frame_times = [
            0,
            duration * 0.33,
            duration * 0.66,
            duration - 0.5  # Near end
        ]
    
    # Create clip directory with descriptive name
    content_hash = hashlib.md5(f"{vid}_{start_s}_{end_s}_{keyword}".encode()).hexdigest()[:8]
    clip_dir = output_dir / f"{vid}_{content_hash}"
    clip_dir.mkdir(parents=True, exist_ok=True)
    
    clip_path = TEMP_DIR / f"clip_{vid}_{content_hash}.mkv"
    frames_extracted = []
    
    try:
        # Step 1: Download clip section using yt-dlp
        url = get_video_url(vid)
        dl_cmd = [
            "yt-dlp", "--cookies", str(YTDLP_COOKIES),
            "--no-playlist", "--ignore-errors",
            "--download-sections", f"*{start_s}-{end_s}",
            "--force-keyframes-at-cuts",
            "-f", YTDLP_FORMAT,
            "-o", str(clip_path),
            url
        ]
        
        result = subprocess.run(dl_cmd, capture_output=True, text=True, timeout=180)
        
        # Fallback if section download failed
        if not clip_path.exists() or clip_path.stat().st_size < 1000:
            clip_path = TEMP_DIR / f"clip_{vid}_{content_hash}_full.mkv"
            dl_cmd = [
                "yt-dlp", "--cookies", str(YTDLP_COOKIES),
                "--no-playlist", "--ignore-errors",
                "-f", YTDLP_FORMAT,
                "-o", str(clip_path), url
            ]
            subprocess.run(dl_cmd, capture_output=True, text=True, timeout=300)
        
        # Step 2: Extract frames at vision model resolution
        if clip_path.exists() and clip_path.stat().st_size > 1000:
            for i, ts in enumerate(frame_times):
                out_path = clip_dir / f"frame_{i:02d}_{int(start_s+ts)}s.{FRAME_FORMAT}"
                if out_path.exists() and out_path.stat().st_size > 1000:
                    frames_extracted.append(str(out_path))
                    continue
                
                # ffmpeg: seek to timestamp, extract frame, scale to vision resolution
                ff_cmd = [
                    "ffmpeg", "-ss", str(ts), "-i", str(clip_path),
                    "-vframes", "1",
                    "-vf", f"scale={VISION_RESOLUTION[0]}:{VISION_RESOLUTION[1]}:force_original_aspect_ratio=decrease,pad={VISION_RESOLUTION[0]}:{VISION_RESOLUTION[1]}:(ow-iw)/2:(oh-ih)/2",
                    "-q:v", str(100 - FRAME_QUALITY),  # WebP quality (lower = better)
                    "-y", str(out_path)
                ]
                subprocess.run(ff_cmd, capture_output=True, timeout=30)
                
                if out_path.exists() and out_path.stat().st_size > 1000:
                    frames_extracted.append(str(out_path))
        
        # Step 3: Create info.json with metadata
        info = {
            "video_id": vid,
            "clip_id": content_hash,
            "keyword": keyword,
            "start_s": round(start_s, 1),
            "end_s": round(end_s, 1),
            "duration_s": round(duration, 1),
            "frame_times": [round(t, 1) for t in frame_times],
            "frames": frames_extracted,
            "frame_count": len(frames_extracted),
            "vision_resolution": VISION_RESOLUTION,
            "frame_format": FRAME_FORMAT,
            "clip_dir": str(clip_dir),
            "status": "complete" if frames_extracted else "failed"
        }
        
        with open(clip_dir / "info.json", "w") as f:
            json.dump(info, f, indent=2)
        
        # Cleanup temp clip
        try:
            if clip_path.exists():
                clip_path.unlink()
        except:
            pass
        
        return info
        
    except subprocess.TimeoutExpired:
        return {"video_id": vid, "clip_id": content_hash, "status": "timeout", "error": "Download/extraction timeout"}
    except Exception as e:
        return {"video_id": vid, "clip_id": content_hash, "status": "error", "error": str(e)}

def create_storyboard_batch(clip_data_list, topic_name, output_base=None):
    """Create a batch of storyboard previews for human review."""
    if output_base is None:
        output_base = PROJECT_ROOT / "whiteboard/storyboards"
    
    topic_dir = output_base / topic_name
    topic_dir.mkdir(parents=True, exist_ok=True)
    
    manifest = []
    
    for clip_data in clip_data_list:
        vid = clip_data["video_id"]
        start_s = clip_data["start_s"]
        end_s = clip_data["end_s"]
        keyword = clip_data.get("keyword", "unknown")
        content_hash = hashlib.md5(f"{vid}_{start_s}_{end_s}_{keyword}".encode()).hexdigest()[:8]
        
        info = extract_clip_frames(vid, start_s, end_s, topic_dir, clip_id=content_hash, keyword=keyword)
        manifest.append(info)
    
    # Save manifest
    manifest_path = topic_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    return manifest

def main():
    parser = argparse.ArgumentParser(description="Extract vision-model-ready clips from videos")
    parser.add_argument("keyword", nargs="?", help="Search keyword for clip extraction")
    parser.add_argument("--video-id", help="Process specific video ID")
    parser.add_argument("--topic", help="Topic name for storyboard batch")
    parser.add_argument("--start", type=float, help="Start time (seconds)")
    parser.add_argument("--end", type=float, help="End time (seconds)")
    parser.add_argument("--manifest", help="Load clips from manifest JSON")
    parser.add_argument("--output", help="Custom output directory")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be processed")
    args = parser.parse_args()
    
    if args.manifest:
        with open(args.manifest) as f:
            clips = json.load(f)
    elif args.keyword:
        # Search unified timestamps for keyword
        unified = load_unified_timestamps()
        clips = []
        for vid, data in unified.items():
            if args.video_id and vid != args.video_id:
                continue
            best_source = data.get("best_source")
            if not best_source:
                continue
            segments = data["sources"][best_source].get("segments", [])
            for seg in segments:
                if args.keyword.lower() in seg.get("text", "").lower():
                    clips.append({
                        "video_id": vid,
                        "start_s": seg["start"],
                        "end_s": seg["end"],
                        "keyword": args.keyword
                    })
        print(f"Found {len(clips)} matching clips")
    elif args.video_id and args.start is not None and args.end is not None:
        clips = [{
            "video_id": args.video_id,
            "start_s": args.start,
            "end_s": args.end,
            "keyword": "manual"
        }]
    else:
        print("Usage: python3 vision_clip_extractor.py <keyword> [--video-id ID] [--topic NAME]")
        print("       python3 vision_clip_extractor.py --video-id ID --start 100 --end 130")
        print("       python3 vision_clip_extractor.py --manifest clips.json")
        return
    
    if args.dry_run:
        for c in clips:
            print(f"  {c['video_id']}: {c['start_s']:.1f}s - {c['end_s']:.1f}s ({c.get('keyword', 'N/A')})")
        return
    
    # Process clips
    output_dir = Path(args.output) if args.output else (PROJECT_ROOT / "vision_clips")
    
    if args.topic:
        # Batch mode with manifest
        manifest = create_storyboard_batch(clips, args.topic, output_dir)
        print(f"Created {len(manifest)} clips in {output_dir}/{args.topic}/")
        for m in manifest:
            print(f"  {m['video_id']}_{m['clip_id']}: {m['frame_count']} frames, {m['status']}")
    else:
        # Individual clips
        for clip in clips:
            content_hash = hashlib.md5(f"{clip['video_id']}_{clip['start_s']}_{clip['end_s']}_{clip.get('keyword', 'unknown')}".encode()).hexdigest()[:8]
            info = extract_clip_frames(
                clip["video_id"],
                clip["start_s"],
                clip["end_s"],
                output_dir,
                clip_id=content_hash,
                keyword=clip.get("keyword", "unknown")
            )
            print(f"{info['video_id']}_{info['clip_id']}: {info['frame_count']} frames - {info['status']}")

if __name__ == "__main__":
    main()