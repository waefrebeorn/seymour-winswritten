#!/usr/bin/env python3
"""
seymour-pre — Query tool for Pre-Seymour era content.

Usage:
  seymour-pre "search terms"          # Full-text search in transcripts
  seymour-pre --era 2024              # Filter by era
  seymour-pre --tag "godot"           # Filter by LLM tag (future)
  seymour-pre --video-id ABC123       # Show specific video
  seymour-pre --random                # Random quote/video
  seymour-pre --stats                 # Show stats
"""
import json, sys, argparse, random, re
from pathlib import Path

INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
ERAS_DIR = Path("/home/wubu/seymour-project/pre_seymour/eras")

def load_index():
    return json.loads(INDEX_FILE.read_text())

def filter_by_tag(index, tag):
    """Filter by LLM-generated topic tag."""
    tag_lower = tag.lower()
    return {v: entry for v, entry in index.items() 
            if entry.get('topics') and any(tag_lower in t.lower() for t in entry['topics'])}

def search_transcripts(index, query, limit=10):
    """Search in transcript text using stored transcript_path."""
    results = []
    query_terms = [t.lower() for t in query.split()]
    
    for vid, entry in index.items():
        if not entry.get("has_transcript"):
            continue
        
        transcript_path = entry.get("transcript_path")
        if not transcript_path:
            continue
            
        try:
            text = Path(transcript_path).read_text().lower()
            if all(term in text for term in query_terms):
                # Find context
                context = ""
                for term in query_terms:
                    idx = text.find(term)
                    if idx >= 0:
                        start = max(0, idx - 100)
                        end = min(len(text), idx + 200)
                        context = text[start:end].strip()
                        break
                results.append({
                    "video_id": vid,
                    "title": entry["title"],
                    "date": entry["upload_date"],
                    "source": entry["source"],
                    "context": context[:300],
                    "word_count": entry["word_count"]
                })
                if len(results) >= limit:
                    break
        except Exception as e:
            print(f"Warning: could not read transcript for {vid}: {e}")
            pass
    
    return results

def filter_by_era(index, era_name):
    """Filter by era file."""
    era_file = ERAS_DIR / f"{era_name}.json"
    if not era_file.exists():
        return {}
    era_data = json.loads(era_file.read_text())
    return {v: entry for v, entry in index.items() if v in era_data}

def show_video(index, vid):
    """Show detailed info for one video."""
    if vid not in index:
        print(f"Video {vid} not found")
        return
    e = index[vid]
    print(f"\n{'='*60}")
    print(f"Video: {vid}")
    print(f"Title: {e['title']}")
    print(f"Date:  {e['upload_date']}")
    print(f"Dur:   {e['duration_fmt']} ({e['duration_sec']}s)")
    print(f"Source: {e['source']}")
    print(f"Words: {e['word_count']:,}")
    print(f"URL:   https://youtu.be/{vid}")
    print(f"{'='*60}")

def show_stats(index):
    total = len(index)
    dated = [e for e in index.values() if e["upload_date"] != "unknown"]
    words = sum(e["word_count"] for e in index.values())
    c11 = sum(1 for e in index.values() if e["source"] == "c11")
    whisper = sum(1 for e in index.values() if e["source"] == "whisper")
    print(f"\n📊 Pre-Seymour Stats")
    print(f"  Total videos:   {total}")
    print(f"  Dated videos:   {len(dated)}")
    print(f"  Total words:    {words:,}")
    print(f"  C11 source:     {c11}")
    print(f"  Whisper source: {whisper}")
    if dated:
        dates = [e["upload_date"] for e in dated]
        print(f"  Date range:     {min(dates)} → {max(dates)}")

def main():
    parser = argparse.ArgumentParser(description="Pre-Seymour query tool")
    parser.add_argument("query", nargs="*", help="Search terms")
    parser.add_argument("--era", "-e", help="Filter by era (2023-foundations, 2024-deep-dives, 2025-hiatus-prep, 2026-absorption)")
    parser.add_argument("--tag", "-t", help="Filter by LLM topic tag")
    parser.add_argument("--video-id", "-v", help="Show specific video")
    parser.add_argument("--random", "-r", action="store_true", help="Random video")
    parser.add_argument("--stats", "-s", action="store_true", help="Show stats")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Result limit")
    
    args = parser.parse_args()
    
    index = load_index()
    
    if args.stats:
        show_stats(index)
        return
    
    if args.video_id:
        show_video(index, args.video_id)
        return
    
    if args.random:
        vid = random.choice(list(index.keys()))
        show_video(index, vid)
        return
    
    # Apply era filter
    if args.era:
        index = filter_by_era(index, args.era)
        if not index:
            print(f"No videos in era: {args.era}")
            return
    
    # Apply tag filter
    if args.tag:
        index = filter_by_tag(index, args.tag)
        if not index:
            print(f"No videos with tag: {args.tag}")
            return
    
    # Search
    if args.query:
        query = " ".join(args.query)
        print(f"🔍 Searching: \"{query}\" ({len(index)} videos in scope)")
        results = search_transcripts(index, query, args.limit)
        if not results:
            print("No matches found in transcripts")
            return
        for i, r in enumerate(results):
            print(f"\n{i+1}. [{r['date']}] {r['video_id']} — {r['title'][:60]}")
            print(f"    {r['source']} | {r['word_count']:,}w")
            print(f"    ...{r['context']}...")
    else:
        print("Usage: seymour-pre \"search terms\" [--era ERA] [--video-id ID] [--random] [--stats]")

if __name__ == "__main__":
    main()