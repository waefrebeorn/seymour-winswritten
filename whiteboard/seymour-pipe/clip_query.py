#!/usr/bin/env python3
"""clip_query.py — Search timestamped transcripts for clip/picture-worthy moments.
Output: seconds-accurate clip boundaries for ffmpeg extraction.

Usage:
  python3 clip_query.py "keyword"                     # Search all videos
  python3 clip_query.py "keyword" --video VID         # Single video
  python3 clip_query.py "keyword" --window 30         # 30s window around every match
  python3 clip_query.py "keyword" --export-clips      # Generate ffmpeg commands
  python3 clip_query.py --topics                      # List topic files for batch clipping
"""
import json, sys, re, subprocess, shlex
from pathlib import Path

INDEX = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/master_timestamps.json")
CLIP_DIR = Path("/home/wubu/seymour-project/whiteboard/clips")
TOPICS_DIR = Path("/home/wubu/seymour-project/absorption/data/topics")

# Context window around each match (seconds)
CONTEXT_S = 5  # seconds before and after the segment

def load_index():
    if not INDEX.exists():
        print(f"Index not found. Run build_timestamps.py first.")
        sys.exit(1)
    return json.loads(INDEX.read_text())["videos"]

def search_videos(keyword, video_filter=None, window=CONTEXT_S):
    """Search all indexed videos for keyword, return clip-ready matches."""
    index = load_index()
    results = []
    
    for vid, data in sorted(index.items()):
        if video_filter and vid != video_filter:
            continue
        
        segs = data.get("segments", [])
        for seg in segs:
            text = seg.get("text", "")
            if keyword.lower() in text.lower():
                # Expand window
                start = max(0, seg["start"] - window)
                end = seg["end"] + window
                
                results.append({
                    "video_id": vid,
                    "source": data.get("source", "unknown"),
                    "model": data.get("model", "unknown"),
                    "duration_s": data.get("duration_s", 0),
                    "start_s": round(start, 1),
                    "end_s": round(end, 1),
                    "clip_len_s": round(end - start, 1),
                    "text": seg["text"].strip(),
                    "seg_start": seg["start"],
                    "seg_end": seg["end"]
                })
    
    return results

def format_clip_cmd(vid, start, end, output_path):
    """Generate ffmpeg command to extract clip.
    Uses yt-dlp to stream the source, cuts with ffmpeg.
    """
    # First try local audio
    local_audio = Path(f"/home/wubu/seymour-project/whiteboard/seymour-pipe/audio/{vid}.mp3")
    if local_audio.exists():
        in_path = shlex.quote(str(local_audio))
    else:
        in_path = f"https://www.youtube.com/watch?v={vid}"
    
    cmd = f"yt-dlp --cookies /home/wubu/seymour-project/whiteboard/seymour-pipe/cookies.txt -o - '{in_path}' 2>/dev/null | ffmpeg -i pipe:0 -ss {start} -to {end} -c copy -y {shlex.quote(str(output_path))} 2>/dev/null"
    return cmd

def load_topic_keywords(topic_name):
    """Load keywords from a topic file."""
    topic_path = TOPICS_DIR / f"{topic_name}.txt"
    if not topic_path.exists():
        print(f"Topic file not found: {topic_path}")
        print(f"Available topics: {[p.stem for p in TOPICS_DIR.glob('*.txt')]}")
        return []
    keywords = []
    for l in topic_path.read_text().splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        # Split comma-separated keywords
        for kw in l.split(","):
            kw = kw.strip()
            if kw:
                keywords.append(kw)
    return keywords

def main():
    if len(sys.argv) < 2 or "--help" in sys.argv:
        print(__doc__)
        sys.exit(0)
    
    args = sys.argv[1:]
    keyword = None
    video_filter = None
    window = CONTEXT_S
    export = False
    topic_mode = False
    
    i = 0
    while i < len(args):
        if args[i] == "--video" and i+1 < len(args):
            video_filter = args[i+1]
            i += 2
        elif args[i] == "--window" and i+1 < len(args):
            window = int(args[i+1])
            i += 2
        elif args[i] == "--export-clips":
            export = True
            i += 1
        elif args[i] == "--topics":
            topic_mode = True
            i += 1
        else:
            keyword = args[i]
            i += 1
    
    if topic_mode:
        print("═══ TOPIC BATCH CLIP QUERY ═══")
        CLIP_DIR.mkdir(parents=True, exist_ok=True)
        for topic_file in sorted(TOPICS_DIR.glob("*.txt")):
            topic = topic_file.stem
            keywords = [l.strip() for l in topic_file.read_text().splitlines()
                       if l.strip() and not l.startswith("#")]
            print(f"\n--- {topic} ({len(keywords)} keywords) ---")
            for kw in keywords[:10]:  # limit per topic
                results = search_videos(kw, window=window)
                if results:
                    print(f"  '{kw}': {len(results)} matches")
                    if export and results[:3]:
                        # Export top 3 clips
                        clip_dir = CLIP_DIR / topic
                        clip_dir.mkdir(exist_ok=True)
                        for j, r in enumerate(results[:3]):
                            out_path = clip_dir / f"{r['video_id']}_{j:02d}.txt"
                            out_path.write_text(
                                f"KEYWORD: {kw}\n"
                                f"VIDEO: {r['video_id']}\n"
                                f"TIMESTAMP: {r['start_s']}-{r['end_s']}s\n"
                                f"TEXT: {r['text']}\n"
                                f"CLIP: ffmpeg -ss {r['start_s']} -to {r['end_s']} -i ...\n"
                            )
                            print(f"    → {out_path}")
            print(f"  Total clips: {sum(1 for _ in (CLIP_DIR/topic).glob('*.txt')) if (CLIP_DIR/topic).exists() else 0}")
        return
    
    if not keyword:
        print("ERROR: provide a keyword or --topics")
        sys.exit(1)
    
    results = search_videos(keyword, video_filter, window)
    
    if not results:
        print(f"No matches for '{keyword}'")
        sys.exit(0)
    
    print(f"═══ '{keyword}' — {len(results)} matches ═══")
    print()
    
    # Group by video
    by_vid = {}
    for r in results:
        by_vid.setdefault(r["video_id"], []).append(r)
    
    for vid in sorted(by_vid.keys()):
        vresults = by_vid[vid]
        vid_dur = vresults[0]["duration_s"]
        print(f"── {vid} ({vid_dur/60:.0f}min, {vresults[0]['source']}) ──")
        for j, r in enumerate(vresults[:10]):  # cap at 10 per video
            print(f"  [{r['start_s']:.0f}s-{r['end_s']:.0f}s] ({r['clip_len_s']:.0f}s) {r['text'][:80]}")
            if export:
                clip_dir = CLIP_DIR / "queries"
                clip_dir.mkdir(parents=True, exist_ok=True)
                out = clip_dir / f"{vid}_{keyword}_{j:02d}.txt"
                out.write_text(
                    f"KEYWORD: {keyword}\nVIDEO: {vid}\n"
                    f"TIMESTAMP: {r['start_s']}-{r['end_s']}s\n"
                    f"TEXT: {r['text']}\n"
                )
        if len(vresults) > 10:
            print(f"  ... +{len(vresults)-10} more")
        print()
    
    print(f"Total: {len(results)} clips from {len(by_vid)} videos")

if __name__ == "__main__":
    main()