#!/usr/bin/env python3
"""
storyboard.py — Create picture preview storyboard from clip matches.
Extracts frames and prepares clips for human approval.

Pipeline:
  1. clip_query.py "keyword" --export-json  →  clip manifest JSON
  2. storyboard.py manifest.json             →  frame previews + approval queue
  3. storyboard.py --approve manifest.json   →  download approved clips

Output:
  storyboards/<topic>/<vid>_<idx>/
    frame.jpg       — single best frame at the clip's midpoint
    thumbnail.jpg   — 320px thumbnail for quick preview
    info.json       — clip metadata + approval status
"""
import json, os, sys, subprocess, shlex, tempfile, shutil, hashlib
from pathlib import Path

BASE        = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
MASTER_TS   = BASE / "master_timestamps.json"
COOKIES     = BASE / "cookies.txt"
STORY_DIR   = Path("/home/wubu/seymour-project/whiteboard/storyboards")
CLIP_DIR    = Path("/home/wubu/seymour-project/whiteboard/clips")
AUDIO_DIR   = BASE / "audio"

# How many frames to extract from a clip (for the storyboard)
FRAMES_PER_CLIP = 3    # start, mid, end
THUMB_WIDTH     = 320
FRAME_WIDTH     = 1280

def load_index():
    return json.loads(MASTER_TS.read_text())["videos"]

def vid_url(vid):
    return f"https://www.youtube.com/watch?v={vid}"

def get_thumbnail_url(vid):
    """Get a high-res thumbnail via yt-dlp (fast, no download)."""
    try:
        r = subprocess.run(
            ["yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
             "--print", "thumbnail", "--no-playlist", "--ignore-errors",
             vid_url(vid)],
            capture_output=True, text=True, timeout=30
        )
        if r.stdout.strip():
            return r.stdout.strip().split("\n")[0]
    except:
        pass
    return f"https://i.ytimg.com/vi/{vid}/maxresdefault.jpg"

def extract_frames(vid, start_s, end_s, output_dir, clip_idx):
    """Extract frames using yt-dlp section download (fast for clips).
    Downloads only the clip segment, then extracts frames from local file.
    """
    timestamps = [0]  # Always grab the first frame of the clip (start)
    if end_s - start_s > 5:
        timestamps.append(int((end_s - start_s) / 2))
    if end_s - start_s > 10:
        timestamps.append(int(end_s - start_s) - 2)
    timestamps = sorted(set(t for t in timestamps if t >= 0))
    
    frames = []
    url = vid_url(vid)
    clip_dur = int(end_s - start_s)
    
    # Download just the clip segment as a temp file
    clip_path = output_dir / f"clip_{vid}.mkv"
    if not (clip_path.exists() and clip_path.stat().st_size > 1000):
        dl_cmd = [
            "yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
            "--no-playlist", "--ignore-errors",
            "--download-sections", f"*{start_s}-{end_s}",
            "--force-keyframes-at-cuts",
            "-f", "worst[height<=480]",
            "-o", str(clip_path),
            url
        ]
        subprocess.run(dl_cmd, capture_output=True, text=True, timeout=120)

    # Fallback if section download failed
    if not clip_path.exists() or clip_path.stat().st_size < 1000:
        fallback_path = output_dir / f"clip_{vid}_full.mkv"
        dl_cmd = [
            "yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
            "--no-playlist", "--ignore-errors",
            "-f", "worst[height<=480]",
            "-o", str(fallback_path), url
        ]
        subprocess.run(dl_cmd, capture_output=True, text=True, timeout=300)
        if fallback_path.exists() and fallback_path.stat().st_size > 1000:
            clip_path = fallback_path

    # Extract frames from whatever we have
    if clip_path.exists() and clip_path.stat().st_size > 1000:
        for i, ts in enumerate(timestamps):
            out_path = output_dir / f"frame_{i:02d}_{int(start_s+ts)}s.jpg"
            if out_path.exists() and out_path.stat().st_size > 1000:
                frames.append(str(out_path))
                continue
            ff_cmd = [
                "ffmpeg", "-ss", str(ts), "-i", str(clip_path),
                "-vframes", "1", "-q:v", "3",
                "-y", str(out_path)
            ]
            subprocess.run(ff_cmd, capture_output=True, timeout=30)
            if out_path.exists() and out_path.stat().st_size > 1000:
                frames.append(str(out_path))

        # Clean up clip file if no frames extracted
        if not frames:
            try: os.unlink(clip_path)
            except: pass

    return frames

def download_local_audio(vid, start_s, end_s, output_path):
    """Download the audio clip locally for preview.
    Uses yt-dlp section download for speed, then ffmpeg audio extraction.
    """
    if output_path.exists() and output_path.stat().st_size > 5000:
        return str(output_path)

    url = vid_url(vid)
    clip_len = end_s - start_s

    # Use section download for audio (fast)
    m4a_path = output_path.with_suffix(".m4a")
    dl_cmd = [
        "yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
        "--no-playlist", "--ignore-errors",
        "--download-sections", f"*{start_s}-{end_s}",
        "--force-keyframes-at-cuts",
        "-f", "worstaudio+worst",  # fastest audio download
        "-o", str(m4a_path),
        url
    ]
    try:
        subprocess.run(dl_cmd, capture_output=True, text=True, timeout=120)
    except:
        pass

    # If m4a exists, convert/stream to mp3
    if m4a_path.exists() and m4a_path.stat().st_size > 5000:
        ff_cmd = [
            "ffmpeg", "-i", str(m4a_path),
            "-acodec", "libmp3lame", "-ab", "64k",
            "-y", str(output_path)
        ]
        subprocess.run(ff_cmd, capture_output=True, timeout=30)
        try: os.unlink(m4a_path)
        except: pass
    else:
        # Fallback: pipe method (slower but reliable)
        try:
            p1 = subprocess.Popen([
                "yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
                "-o", "-", "--no-playlist", "--ignore-errors",
                "-x", "--audio-format", "mp3", url
            ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            p2 = subprocess.Popen([
                "ffmpeg", "-ss", str(start_s), "-i", "pipe:0",
                "-to", str(clip_len), "-c", "copy",
                "-y", str(output_path)
            ], stdin=p1.stdout, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            p1.stdout.close()
            p2.wait(timeout=300)
            p1.wait(timeout=60)
        except:
            pass

    if output_path.exists() and output_path.stat().st_size > 5000:
        return str(output_path)
    return None

def create_storyboard(clip_data, output_dir=None, auto_approve=False):
    """Given a clip match dict, create a storyboard preview.
    
    clip_data format:
      {video_id, start_s, end_s, text, keyword, topic (optional)}
    
    Creates directory:
      storyboards/topic_or_query/<vid>_<hash>/
        frame_00.jpg       — clip frame
        thumbnail.jpg      — video thumbnail
        audio_preview.mp3  — 30s audio clip
        info.json          — metadata + approval status
    """
    vid = clip_data["video_id"]
    start_s = clip_data["start_s"]
    end_s = clip_data["end_s"]
    keyword = clip_data.get("keyword", "unknown")
    topic = clip_data.get("topic", "queries")
    text = clip_data.get("text", "")
    
    # Create a stable directory name
    content_hash = hashlib.md5(f"{vid}_{start_s}_{end_s}".encode()).hexdigest()[:8]
    clip_dir = (output_dir or STORY_DIR) / topic / f"{vid}_{content_hash}"
    clip_dir.mkdir(parents=True, exist_ok=True)
    
    result = {
        "video_id": vid,
        "keyword": keyword,
        "topic": topic,
        "start_s": start_s,
        "end_s": end_s,
        "text": text,
        "dir": str(clip_dir),
        "frames": [],
        "thumbnail": None,
        "audio_preview": None,
        "approved": auto_approve
    }
    
    # 1. Get video thumbnail (fastest — yt-dlp metadata only)
    thumb_url = get_thumbnail_url(vid)
    thumb_path = clip_dir / "thumbnail.jpg"
    if not thumb_path.exists():
        try:
            subprocess.run([
                "curl", "-s", "-o", str(thumb_path), thumb_url
            ], timeout=15)
        except:
            pass
    if thumb_path.exists() and thumb_path.stat().st_size > 1000:
        result["thumbnail"] = str(thumb_path)
        # Create 320px thumbnail
        try:
            from PIL import Image
            img = Image.open(thumb_path)
            img.thumbnail((THUMB_WIDTH, THUMB_WIDTH))
            img.save(clip_dir / "thumb_320.jpg")
            result["thumbnail_320"] = str(clip_dir / "thumb_320.jpg")
        except:
            pass
    
    # 2. Extract frames from the clip
    frames = extract_frames(vid, start_s, end_s, clip_dir, 0)
    if frames:
        result["frames"] = frames
    
    # 3. Download audio preview (first 30s of clip)
    audio_preview_path = clip_dir / "audio_preview.mp3"
    clip_len = min(30.0, end_s - start_s)
    aud = download_local_audio(vid, start_s, start_s + clip_len, audio_preview_path)
    if aud:
        result["audio_preview"] = aud
    
    # 4. Write info.json
    info_path = clip_dir / "info.json"
    info_path.write_text(json.dumps(result, indent=2))
    
    return result

def process_manifest(manifest_path, auto_approve=False):
    """Process a clip manifest JSON (from clip_query.py export)."""
    manifest = json.loads(Path(manifest_path).read_text())
    
    if isinstance(manifest, dict) and "clips" in manifest:
        clips = manifest["clips"]
    elif isinstance(manifest, list):
        clips = manifest
    else:
        clips = [manifest]
    
    print(f"══ Processing {len(clips)} clips ══\n")
    
    all_results = []
    for i, clip in enumerate(clips):
        print(f"[{i+1}/{len(clips)}] {clip.get('video_id','?')} "
              f"@{clip.get('start_s',0):.0f}s-{clip.get('end_s',0):.0f}s "
              f"«{clip.get('text','')[:50]}...»")
        
        result = create_storyboard(clip, auto_approve=auto_approve)
        all_results.append(result)
        
        # Print summary
        print(f"  → {result['dir']}/")
        if result.get("thumbnail"):
            print(f"  → Thumb: {result['thumbnail']}")
        if result.get("frames"):
            print(f"  → {len(result['frames'])} frames (start/mid/end)")
        if result.get("audio_preview"):
            aud_size = Path(result["audio_preview"]).stat().st_size / 1e3
            print(f"  → Audio: {aud_size:.0f}KB preview")
        print(f"  → Text: {clip.get('text','')[:80]}")
        print()
    
    # Write combined manifest
    out_path = Path(manifest_path).with_suffix(".storyboard.json")
    json.dump({
        "clips": all_results,
        "pending_approval": sum(1 for r in all_results if not r.get("approved"))
    }, open(out_path, "w"), indent=2)
    
    print(f"═══ Summary ═══")
    print(f"  Total clips: {len(all_results)}")
    print(f"  With frames: {sum(1 for r in all_results if r.get('frames'))}")
    print(f"  With audio:  {sum(1 for r in all_results if r.get('audio_preview'))}")
    print(f"  Auto-approved: {sum(1 for r in all_results if r.get('approved'))}")
    print(f"\n  Review in: {out_path}")
    
    return all_results

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Storyboard: create picture+audio previews of clips")
    parser.add_argument("manifest", nargs="?", help="Clip manifest JSON from clip_query.py export")
    parser.add_argument("--approve", action="store_true", help="Auto-approve all clips (skip review)")
    parser.add_argument("--keyword", "-k", help="Search keyword and build storyboard directly")
    parser.add_argument("--video", help="Restrict keyword search to one video")
    parser.add_argument("--window", type=int, default=10, help="Context window around match (seconds)")
    parser.add_argument("--topic", help="Use topic file keywords for batch")
    parser.add_argument("--max", type=int, default=5, help="Max clips per keyword/topic")
    parser.add_argument("--export", help="Export frame files to this directory")
    args = parser.parse_args()
    
    if args.keyword:
        # Direct keyword search → storyboard
        from clip_query import search_videos
        results = search_videos(args.keyword, video_filter=args.video, window=args.window)
        if not results:
            print(f"No matches for '{args.keyword}'")
            sys.exit(1)
        
        # Create manifest
        clips = []
        seen = set()
        for r in results:
            key = (r["video_id"], r["start_s"])
            if key not in seen:
                seen.add(key)
                r["keyword"] = args.keyword
                r["topic"] = args.topic or "queries"
                clips.append(r)
        
        clips = clips[:args.max]
        print(f"═══ '{args.keyword}' — {len(results)} matches → {len(clips)} clips ═══\n")
        
        for i, clip in enumerate(clips):
            result = create_storyboard(clip, auto_approve=args.approve)
            print(f"[{i+1}/{len(clips)}] {clip['video_id']} @{clip['start_s']:.0f}s")
            if result.get("frames"):
                print(f"  Frames: {len(result['frames'])}")
            if result.get("thumbnail"):
                print(f"  Thumb: {result['thumbnail']}")
            if result.get("audio_preview"):
                print(f"  Audio: {result['audio_preview']}")
            print(f"  Text: {clip['text'][:100]}")
            print()
    
    elif args.topic:
        # Topic file batch
        topic_path = Path(f"/home/wubu/seymour-project/absorption/data/topics/{args.topic}.txt")
        if not topic_path.exists():
            print(f"Topic not found. Available: {[p.stem for p in Path('/home/wubu/seymour-project/absorption/data/topics').glob('*.txt')]}")
            sys.exit(1)
        from clip_query import search_videos, load_topic_keywords
        keywords = load_topic_keywords(args.topic)
        print(f"═══ Topic '{args.topic}' — {len(keywords)} keywords ═══\n")
        
        all_results = []
        for kw in keywords:
            results = search_videos(kw, window=args.window)
            clips = results[:args.max]
            for r in clips:
                r["keyword"] = kw
                r["topic"] = args.topic
                result = create_storyboard(r, auto_approve=args.approve)
                all_results.append(result)
                if result.get("frames"):
                    print(f"  '{kw}': {result['video_id']} @{result['start_s']:.0f}s")
        
        print(f"\n═══ Topic complete: {len(all_results)} storyboards ═══")
    
    elif args.manifest:
        process_manifest(args.manifest, auto_approve=args.approve)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()