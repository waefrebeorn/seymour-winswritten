#!/usr/bin/env python3
"""
timestamp_compiler.py — Merge all timestamp sources (C11, Whisper, yt-dlp chapters) 
into a unified timeline per video with deduplication and gap detection.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

# Paths
INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
MASTER_TS_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/master_timestamps.json")
WHISPER_TS_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_timestamps")
METADATA_DIR = Path("/home/wubu/seymour-project/video_metadata")
OUTPUT_FILE = Path("/home/wubu/seymour-project/unified_timestamps.json")

def load_index():
    with open(INDEX_FILE) as f:
        return json.load(f)

def load_master_timestamps():
    if MASTER_TS_FILE.exists():
        with open(MASTER_TS_FILE) as f:
            return json.load(f).get("videos", {})
    return {}

def load_whisper_timestamps():
    """Load all whisper timestamp segment files."""
    result = {}
    for ts_file in WHISPER_TS_DIR.glob("*_segments.json"):
        vid = ts_file.stem.replace("_segments", "")
        try:
            with open(ts_file) as f:
                data = json.load(f)
            result[vid] = data
        except Exception as e:
            print(f"Error loading {ts_file}: {e}")
    return result

def load_yt_chapters():
    """Extract chapters from yt-dlp metadata files."""
    result = {}
    if METADATA_DIR.exists():
        for meta_file in METADATA_DIR.glob("*.json"):
            if meta_file.name in ("extraction_progress.json", "extraction_summary.json"):
                continue
            vid = meta_file.stem
            try:
                with open(meta_file) as f:
                    data = json.load(f)
                chapters = data.get("chapters", [])
                if chapters:
                    result[vid] = chapters
            except Exception:
                pass
    return result

def merge_timestamps():
    """Merge all timestamp sources into unified format."""
    index = load_index()
    master_ts = load_master_timestamps()
    whisper_ts = load_whisper_timestamps()
    yt_chapters = load_yt_chapters()
    
    unified = {}
    
    for vid, info in index.items():
        sources = {}
        
        # C11 / master timestamps
        if vid in master_ts:
            sources["c11"] = {
                "source": master_ts[vid].get("source", "c11"),
                "model": master_ts[vid].get("model", "unknown"),
                "duration_s": master_ts[vid].get("duration_s", info.get("duration_sec", 0)),
                "segments": master_ts[vid].get("segments", []),
                "segment_count": len(master_ts[vid].get("segments", []))
            }
        
        # Whisper timestamps
        if vid in whisper_ts:
            ws = whisper_ts[vid]
            sources["whisper"] = {
                "source": "whisper",
                "model": ws.get("model", "unknown"),
                "duration_s": ws.get("duration_s", info.get("duration_sec", 0)),
                "segments": ws.get("segments", []),
                "segment_count": len(ws.get("segments", [])),
                "total_words": ws.get("total_words", 0)
            }
        
        # yt-dlp chapters
        if vid in yt_chapters:
            chapters = yt_chapters[vid]
            # Convert chapters to segment-like format
            chapter_segments = []
            for ch in chapters:
                chapter_segments.append({
                    "start": ch.get("start_time", 0),
                    "end": ch.get("end_time", ch.get("start_time", 0) + 1),
                    "text": ch.get("title", "Chapter"),
                    "is_chapter": True
                })
            sources["yt_chapters"] = {
                "source": "yt_dlp",
                "duration_s": info.get("duration_sec", 0),
                "segments": chapter_segments,
                "segment_count": len(chapter_segments)
            }
        
        # Determine best source (prefer C11 > Whisper > chapters)
        best_source = None
        if "c11" in sources:
            best_source = "c11"
        elif "whisper" in sources:
            best_source = "whisper"
        elif "yt_chapters" in sources:
            best_source = "yt_chapters"
        
        unified[vid] = {
            "video_id": vid,
            "title": info.get("title", ""),
            "duration_sec": info.get("duration_sec", 0),
            "duration_fmt": info.get("duration_fmt", ""),
            "has_transcript": info.get("has_transcript", False),
            "topics": info.get("topics", []),
            "sources": sources,
            "best_source": best_source,
            "source_count": len(sources),
            "total_segments": sum(s.get("segment_count", 0) for s in sources.values()),
            "has_timestamps": len(sources) > 0
        }
    
    return unified

def analyze_gaps(unified):
    """Analyze gaps in timestamp coverage."""
    total = len(unified)
    has_ts = sum(1 for v in unified.values() if v["has_timestamps"])
    no_ts = total - has_ts
    
    source_counts = defaultdict(int)
    for v in unified.values():
        for src in v["sources"]:
            source_counts[src] += 1
    
    # Find videos with no timestamps
    no_timestamp_videos = [
        {"video_id": vid, "title": v["title"], "duration_sec": v["duration_sec"]}
        for vid, v in unified.items() if not v["has_timestamps"]
    ]
    
    # Find videos with sparse timestamps (< 10 segments)
    sparse_videos = [
        {"video_id": vid, "title": v["title"], "segments": v["total_segments"], "sources": list(v["sources"].keys())}
        for vid, v in unified.items() if v["has_timestamps"] and v["total_segments"] < 10
    ]
    
    return {
        "total_videos": total,
        "with_timestamps": has_ts,
        "without_timestamps": no_ts,
        "coverage_pct": f"{has_ts/total*100:.1f}%",
        "source_distribution": dict(source_counts),
        "no_timestamp_videos": no_timestamp_videos,
        "sparse_timestamp_videos": sparse_videos[:50]  # top 50
    }

def main():
    print("Loading timestamp sources...")
    unified = merge_timestamps()
    
    print("Analyzing gaps...")
    gap_analysis = analyze_gaps(unified)
    
    output = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "videos": unified,
        "gap_analysis": gap_analysis
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n=== Unified Timestamps Complete ===")
    print(f"Total videos: {gap_analysis['total_videos']}")
    print(f"With timestamps: {gap_analysis['with_timestamps']} ({gap_analysis['coverage_pct']})")
    print(f"Without timestamps: {gap_analysis['without_timestamps']}")
    print(f"Source distribution: {gap_analysis['source_distribution']}")
    print(f"Sparse (<10 segments): {len(gap_analysis['sparse_timestamp_videos'])}")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()