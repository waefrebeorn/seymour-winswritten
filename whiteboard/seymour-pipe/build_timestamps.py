#!/usr/bin/env python3
"""Build unified timestamp index from GPU whisper segments + C11 transcripts.
Output: master timestamp index JSON with video_id → {segments, duration, model, title}

For clip/picture creation, we need: video_id, start_s, end_s, text, confidence
"""
import json, re, os
from pathlib import Path
from datetime import datetime

BASE      = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
WHISPER_TS = BASE / "whisper_timestamps"
C11_DIR   = Path("/home/wubu/seymour-project/absorption/data/transcripts")
INDEX_OUT = BASE / "master_timestamps.json"
SUMM_OUT  = BASE / "timestamp_summary.txt"

def parse_c11_timestamps(text):
    """Parse C11's inline timestamp formats.
    Two formats:
      M:SSHH — minutes:seconds.hundredths  (e.g. '0:2323 seconds' = 23.23s)
      H:MM:SS — hours:minutes:seconds       (e.g. '3:35:29' = 3h35m29s)
    """
    segments = []
    
    # Pattern A: H:MM:SS (hours:minutes:seconds) — 2+ digit groups
    pattern_a = r'(\d+):(\d{2}):(\d{2})\s*(?:seconds?|minutes?)?'
    # Pattern B: M:SSHH (minutes:seconds.hundredths) — 3-digit hundredths on end
    pattern_b = r'(\d+):(\d{2})(\d{2})\s*(?:seconds?|minutes?)?'
    
    # Find all timestamps with their position and type
    timestamps = []  # (pos, total_secs, end_pos)
    
    for m in re.finditer(pattern_a, text):
        hours = int(m.group(1))
        mins = int(m.group(2))
        secs = int(m.group(3))
        total_secs = hours * 3600 + mins * 60 + secs
        if total_secs < 360000:  # 100hr cap
            timestamps.append((m.start(), total_secs, m.end()))
    
    for m in re.finditer(pattern_b, text):
        # Check it's not overlapping with a pattern_a match
        overlapping = False
        for start, _, end in timestamps:
            if m.start() < end and m.end() > start:
                overlapping = True
                break
        if overlapping:
            continue
        mins = int(m.group(1))
        secs = int(m.group(2))
        hundredths = int(m.group(3))
        total_secs = mins * 60 + secs + hundredths / 100.0
        if total_secs < 360000:
            timestamps.append((m.start(), total_secs, m.end()))
    
    timestamps.sort()
    
    for i, (pos, total_secs, end_pos) in enumerate(timestamps):
            # Text between this timestamp and the next one
            if i + 1 < len(timestamps):
                next_start = timestamps[i+1][0]
            else:
                next_start = len(text)
            between = text[end_pos:next_start].strip()
            # Clean up brackets
            between = re.sub(r'\[.*?\]', '', between).strip()
            # Aggressive cleanup: remove ANY timestamp-shaped prefix
            between = re.sub(r'^[\s,:;.\-–—]*\d*\s*(?:hours?|minutes?|seconds?)[\s,;.\-–—]*', '', between).strip()
            between = re.sub(r'^[\s,:;.\-–—]*\d*\s*hours?[\s,;.\-–—]*\d*\s*minutes?[\s,;.\-–—]*', '', between).strip()
            between = re.sub(r'^[\s,:;.\-–—]*\d*\s*minutes?[\s,;.\-–—]*\d*\s*seconds?[\s,;.\-–—]*', '', between).strip()
            between = re.sub(r'^s[\s,;.:]+\d*[\s,;.:]*', '', between).strip()
            between = re.sub(r'^[\s,:;.\-–—]+', '', between).strip()

            if between:
                # End time: use next timestamp if within 10min, else +15s
                end_secs = total_secs + 15
                if i + 1 < len(timestamps):
                    next_ts = timestamps[i+1][1]
                    if next_ts > total_secs and next_ts < total_secs + 600:
                        end_secs = next_ts
                segments.append({
                    "start": round(total_secs, 2),
                    "end": round(end_secs, 2),
                    "text": between
                })
    
    return segments

def extract_video_id_from_c11(filename):
    """Extract video ID from C11 transcript filename (they're just VID.txt)"""
    stem = filename.stem
    if re.match(r'^[a-zA-Z0-9_-]{11}$', stem):
        return stem
    return None

def main():
    index = {}
    stats = {"gpu_segments": 0, "c11_segments": 0, "gpu_videos": 0, "c11_videos": 0}
    
    # --- GPU whisper segment JSONs ---
    for f in sorted(WHISPER_TS.glob("*_segments.json")):
        vid = f.stem.replace("_segments", "")
        try:
            data = json.loads(f.read_text())
        except:
            continue
        
        segs = data.get("segments", [])
        if not segs:
            continue
        
        index[vid] = {
            "video_id": vid,
            "source": "gpu_whisper",
            "model": data.get("model", "unknown"),
            "duration_s": data.get("duration_s", 0),
            "chunked": data.get("chunked", False),
            "segments": segs,
            "total_words": data.get("total_words", 0),
            "seg_count": len(segs)
        }
        stats["gpu_segments"] += len(segs)
        stats["gpu_videos"] += 1
    
    # --- C11 transcripts with inline timestamps ---
    for f in sorted(C11_DIR.glob("*.txt")):
        vid = extract_video_id_from_c11(f)
        if not vid:
            continue
        if vid in index:
            continue  # GPU whisper has better timestamps
        
        text = f.read_text()
        segs = parse_c11_timestamps(text)
        if not segs:
            continue
        
        # Estimate duration from last segment
        dur = max(s["end"] for s in segs) if segs else 0
        
        index[vid] = {
            "video_id": vid,
            "source": "c11_inline",
            "model": "c11_legacy",
            "duration_s": dur,
            "chunked": False,
            "segments": segs,
            "total_words": sum(len(s["text"].split()) for s in segs),
            "seg_count": len(segs)
        }
        stats["c11_segments"] += len(segs)
        stats["c11_videos"] += 1
    
    # Write master index
    INDEX_OUT.write_text(json.dumps({
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "videos": index
    }, indent=2))
    
    # Write summary
    total_segs = stats["gpu_segments"] + stats["c11_segments"]
    total_vids = stats["gpu_videos"] + stats["c11_videos"]
    total_words = sum(v["total_words"] for v in index.values())
    
    summary = f"""═══ TIMESTAMP INDEX SUMMARY ═══
Generated: {datetime.now():%Y-%m-%d %H:%M}

GPU Whisper timestamped videos: {stats['gpu_videos']} ({stats['gpu_segments']} segments)
C11 legacy videos:            {stats['c11_videos']} ({stats['c11_segments']} segments)
────────────────────────────────────
Total indexed videos:         {total_vids}
Total segments:               {total_segs}
Total words:                  {total_words}

Video duration range: {min((v.get('duration_s',0) for v in index.values()), default=0):.0f}s – {max((v.get('duration_s',0) for v in index.values()), default=0)/60:.0f}min

Videos with chunked GPU whisper (long streams): {sum(1 for v in index.values() if v.get('chunked'))}
"""
    SUMM_OUT.write_text(summary)
    print(summary)
    
    # Also list videos sorted by title/date for Ponderable matching
    print("\n═══ ALL INDEXED VIDEOS ═══")
    for vid in sorted(index.keys()):
        v = index[vid]
        dur_min = v.get("duration_s", 0) / 60
        print(f"  {vid}  {dur_min:5.0f}min  {v['seg_count']:4d} segs  {v['total_words']:5d}w  {v['source']}")
    
    print(f"\nTotal: {total_vids} videos, {total_segs} segments, {total_words} words")

if __name__ == "__main__":
    main()
