#!/usr/bin/env python3
"""
video_feature_aggregator.py — Comprehensive feature aggregation for all videos.
Compiles all available features (transcripts, timestamps, topics, metadata, vision-readiness)
into a master index with gap analysis.
"""

import json
from pathlib import Path
from collections import defaultdict

# Paths
INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
UNIFIED_TS_FILE = Path("/home/wubu/seymour-project/unified_timestamps.json")
METADATA_DIR = Path("/home/wubu/seymour-project/video_metadata")
STORYBOARD_DIR = Path("/home/wubu/seymour-project/whiteboard/storyboards")
VISION_CLIPS_DIR = Path("/home/wubu/seymour-project/vision_clips")
ABSORPTION_DIR = Path("/home/wubu/seymour-project/absorption/data/transcripts")
WHISPER_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_transcripts")
MASTER_TS_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/master_timestamps.json")
OUTPUT_FILE = Path("/home/wubu/seymour-project/video_features_master.json")

def load_json(path, default=None):
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return default or {}

def main():
    print("Loading all data sources...")
    
    # Load primary index
    index = load_json(INDEX_FILE, {})
    
    # Load unified timestamps
    unified_ts = load_json(UNIFIED_TS_FILE, {}).get("videos", {})
    
    # Load master timestamps (C11)
    master_ts = load_json(MASTER_TS_FILE, {}).get("videos", {})
    
    # Check what metadata files exist
    metadata_files = {f.stem: f for f in METADATA_DIR.glob("*.json") 
                      if f.name not in ("extraction_progress.json", "extraction_summary.json")}
    
    # Check storyboard status
    storyboard_videos = set()
    if STORYBOARD_DIR.exists():
        for topic_dir in STORYBOARD_DIR.iterdir():
            if topic_dir.is_dir():
                for clip_dir in topic_dir.iterdir():
                    if clip_dir.is_dir() and (clip_dir / "info.json").exists():
                        vid = clip_dir.name.split("_")[0]
                        storyboard_videos.add(vid)
    
    # Check vision clips
    vision_clip_videos = set()
    if VISION_CLIPS_DIR.exists():
        for clip_dir in VISION_CLIPS_DIR.iterdir():
            if clip_dir.is_dir() and (clip_dir / "manifest.json").exists():
                vid = clip_dir.name.split("_")[0]
                vision_clip_videos.add(vid)
    
    # Check absorption transcripts
    absorption_videos = {f.stem for f in ABSORPTION_DIR.glob("*.txt")}
    
    # Check whisper transcripts
    whisper_videos = {f.stem.replace("_whisper", "") for f in WHISPER_DIR.glob("*_whisper.txt")}
    
    # Build comprehensive feature matrix
    features = {}
    
    for vid, info in index.items():
        vid_unified = unified_ts.get(vid, {})
        vid_master = master_ts.get(vid, {})
        vid_metadata = metadata_files.get(vid)
        
        # Load metadata if available
        metadata = {}
        if vid_metadata:
            try:
                with open(vid_metadata) as f:
                    metadata = json.load(f)
            except:
                pass
        
        # Transcript info
        has_absorption = vid in absorption_videos
        has_whisper = vid in whisper_videos
        transcript_path = info.get("transcript_path", "")
        transcript_exists = Path(transcript_path).exists() if transcript_path else False
        transcript_size = Path(transcript_path).stat().st_size if transcript_exists else 0
        
        # Timestamp sources
        ts_sources = vid_unified.get("sources", {})
        has_c11_ts = "c11" in ts_sources
        has_whisper_ts = "whisper" in ts_sources
        has_yt_chapters = "yt_chapters" in ts_sources
        best_ts_source = vid_unified.get("best_source")
        total_segments = vid_unified.get("total_segments", 0)
        
        # Topics
        topics = info.get("topics", [])
        has_topics = len(topics) > 0
        
        # Metadata from yt-dlp
        has_metadata = bool(metadata)
        has_chapters = bool(metadata.get("chapters"))
        has_tags = bool(metadata.get("tags"))
        has_thumbnails = bool(metadata.get("thumbnails"))
        
        # Vision readiness - check manifest files for actual successful clips
        has_storyboard = False
        if STORYBOARD_DIR.exists():
            for topic_dir in STORYBOARD_DIR.iterdir():
                if topic_dir.is_dir():
                    if list(topic_dir.glob(f"{vid}_*")):
                        has_storyboard = True
                        break
        
        has_vision_clips = False
        vision_clip_count = 0
        if VISION_CLIPS_DIR.exists():
            for topic_dir in VISION_CLIPS_DIR.iterdir():
                if topic_dir.is_dir():
                    manifest_file = topic_dir / "manifest.json"
                    if manifest_file.exists():
                        try:
                            with open(manifest_file) as f:
                                manifest = json.load(f)
                            # Manifest is a list of clip objects
                            if isinstance(manifest, list):
                                for clip in manifest:
                                    if clip.get("video_id") == vid and clip.get("status") == "complete" and clip.get("frames"):
                                        has_vision_clips = True
                                        vision_clip_count += 1
                        except Exception:
                            pass
        
        # Duration
        duration = info.get("duration_sec", 0)
        
        # Feature completeness score (0-100)
        score = 0
        if has_absorption or has_whisper: score += 20  # transcript
        if has_c11_ts or has_whisper_ts: score += 25  # timestamps
        if has_topics: score += 20  # topics
        if has_metadata: score += 15  # yt metadata
        if has_chapters: score += 10  # chapters
        if has_storyboard or has_vision_clips: score += 10  # vision ready
        
        features[vid] = {
            "video_id": vid,
            "title": info.get("title", ""),
            "duration_sec": duration,
            "duration_fmt": info.get("duration_fmt", ""),
            "source": info.get("source", ""),
            
            # Transcripts
            "transcript": {
                "has_absorption": has_absorption,
                "has_whisper": has_whisper,
                "has_any": has_absorption or has_whisper,
                "transcript_path": transcript_path,
                "transcript_exists": transcript_exists,
                "transcript_size_bytes": transcript_size,
                "word_count": info.get("word_count", 0),
                "transcript_chars": info.get("transcript_chars", 0)
            },
            
            # Timestamps
            "timestamps": {
                "has_c11": has_c11_ts,
                "has_whisper": has_whisper_ts,
                "has_yt_chapters": has_yt_chapters,
                "has_any": has_c11_ts or has_whisper_ts or has_yt_chapters,
                "best_source": best_ts_source,
                "total_segments": total_segments,
                "c11_segments": ts_sources.get("c11", {}).get("segment_count", 0),
                "whisper_segments": ts_sources.get("whisper", {}).get("segment_count", 0),
                "chapter_count": ts_sources.get("yt_chapters", {}).get("segment_count", 0)
            },
            
            # Topics
            "topics": {
                "has_topics": has_topics,
                "topic_count": len(topics),
                "topics": topics
            },
            
            # YouTube metadata
            "metadata": {
                "has_metadata": has_metadata,
                "has_chapters": has_chapters,
                "has_tags": has_tags,
                "has_thumbnails": has_thumbnails,
                "view_count": metadata.get("view_count"),
                "like_count": metadata.get("like_count"),
                "comment_count": metadata.get("comment_count"),
                "upload_date": metadata.get("upload_date"),
                "channel_id": metadata.get("channel_id"),
                "tags": metadata.get("tags", [])[:20] if metadata.get("tags") else [],
                "categories": metadata.get("categories", []),
                "chapters": metadata.get("chapters", [])[:10] if metadata.get("chapters") else []
            },
            
            # Vision model readiness
            "vision_ready": {
                "has_storyboard": has_storyboard,
                "has_vision_clips": has_vision_clips,
                "is_ready": has_storyboard or has_vision_clips,
                "storyboard_path": str(STORYBOARD_DIR) if has_storyboard else None,
                "vision_clips_path": str(VISION_CLIPS_DIR) if has_vision_clips else None
            },
            
            # Overall score
            "completeness_score": score,
            "feature_gaps": {
                "missing_transcript": not (has_absorption or has_whisper),
                "missing_timestamps": not (has_c11_ts or has_whisper_ts or has_yt_chapters),
                "missing_topics": not has_topics,
                "missing_metadata": not has_metadata,
                "missing_vision_prep": not (has_storyboard or has_vision_clips)
            }
        }
    
    # Generate gap analysis
    total = len(features)
    gap_analysis = {
        "total_videos": total,
        "transcript_coverage": {
            "absorption": sum(1 for f in features.values() if f["transcript"]["has_absorption"]),
            "whisper": sum(1 for f in features.values() if f["transcript"]["has_whisper"]),
            "any": sum(1 for f in features.values() if f["transcript"]["has_any"])
        },
        "timestamp_coverage": {
            "c11": sum(1 for f in features.values() if f["timestamps"]["has_c11"]),
            "whisper": sum(1 for f in features.values() if f["timestamps"]["has_whisper"]),
            "yt_chapters": sum(1 for f in features.values() if f["timestamps"]["has_yt_chapters"]),
            "any": sum(1 for f in features.values() if f["timestamps"]["has_any"])
        },
        "topic_coverage": {
            "has_topics": sum(1 for f in features.values() if f["topics"]["has_topics"]),
            "missing_topics": sum(1 for f in features.values() if not f["topics"]["has_topics"])
        },
        "metadata_coverage": {
            "has_metadata": sum(1 for f in features.values() if f["metadata"]["has_metadata"]),
            "has_chapters": sum(1 for f in features.values() if f["metadata"]["has_chapters"]),
            "has_tags": sum(1 for f in features.values() if f["metadata"]["has_tags"])
        },
        "vision_readiness": {
            "has_storyboard": sum(1 for f in features.values() if f["vision_ready"]["has_storyboard"]),
            "has_vision_clips": sum(1 for f in features.values() if f["vision_ready"]["has_vision_clips"]),
            "ready": sum(1 for f in features.values() if f["vision_ready"]["is_ready"])
        },
        "completeness_distribution": {
            "complete_80_plus": sum(1 for f in features.values() if f["completeness_score"] >= 80),
            "partial_50_79": sum(1 for f in features.values() if 50 <= f["completeness_score"] < 80),
            "minimal_20_49": sum(1 for f in features.values() if 20 <= f["completeness_score"] < 50),
            "empty_under_20": sum(1 for f in features.values() if f["completeness_score"] < 20)
        },
        "videos_by_gap": {
            "no_transcript": [f["video_id"] for f in features.values() if f["feature_gaps"]["missing_transcript"]],
            "no_timestamps": [f["video_id"] for f in features.values() if f["feature_gaps"]["missing_timestamps"]],
            "no_topics": [f["video_id"] for f in features.values() if f["feature_gaps"]["missing_topics"]],
            "no_metadata": [f["video_id"] for f in features.values() if f["feature_gaps"]["missing_metadata"]],
            "not_vision_ready": [f["video_id"] for f in features.values() if f["feature_gaps"]["missing_vision_prep"]]
        }
    }
    
    # Top incomplete videos
    incomplete = sorted(
        [(f["video_id"], f["title"], f["completeness_score"], f["feature_gaps"]) 
         for f in features.values() if f["completeness_score"] < 50],
        key=lambda x: x[2]
    )
    gap_analysis["most_incomplete"] = incomplete[:20]
    
    # Output
    output = {
        "generated_at": __import__("datetime").datetime.now().isoformat(),
        "summary": gap_analysis,
        "features": features
    }
    
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)
    
    # Print summary
    print(f"\n=== Video Feature Aggregation Complete ===")
    print(f"Total videos: {total}")
    print(f"Transcripts: {gap_analysis['transcript_coverage']['any']}/{total} ({gap_analysis['transcript_coverage']['any']/total*100:.1f}%)")
    print(f"Timestamps: {gap_analysis['timestamp_coverage']['any']}/{total} ({gap_analysis['timestamp_coverage']['any']/total*100:.1f}%)")
    print(f"  - C11: {gap_analysis['timestamp_coverage']['c11']}")
    print(f"  - Whisper: {gap_analysis['timestamp_coverage']['whisper']}")
    print(f"  - YT Chapters: {gap_analysis['timestamp_coverage']['yt_chapters']}")
    print(f"Topics: {gap_analysis['topic_coverage']['has_topics']}/{total} ({gap_analysis['topic_coverage']['has_topics']/total*100:.1f}%)")
    print(f"Metadata: {gap_analysis['metadata_coverage']['has_metadata']}/{total} ({gap_analysis['metadata_coverage']['has_metadata']/total*100:.1f}%)")
    print(f"Vision Ready: {gap_analysis['vision_readiness']['ready']}/{total} ({gap_analysis['vision_readiness']['ready']/total*100:.1f}%)")
    print(f"\nCompleteness:")
    for k, v in gap_analysis['completeness_distribution'].items():
        print(f"  {k}: {v}")
    print(f"\nOutput: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()