#!/usr/bin/env python3
"""
Seymour Context Extractor
Pulls YouTube auto-generated subtitles from all videos in the WuBu Streams channel
and saves them as raw text files for context building.
"""

import os
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter

# Channel videos (from vod.waefrebeorn.com)
VIDEOS = [
    {"id": "aB8Uv939hLM", "title": "WuBu Gaming Intro (not clickbait)", "type": "intro"},
    {"id": "REK_MmenDK8", "title": "WuBu - Psychonauts 2", "type": "stream"},
    {"id": "MGKmSVmZ2OU", "title": "WuBu - Psychonauts 2 part 1", "type": "stream"},
    {"id": "PnbqgIeqFFY", "title": "WuBu - Poppy Playtime 5 (Part 4)", "type": "stream"},
    {"id": "4LxOKWC4cho", "title": "WuBu - Poppy Playtime 5 (Part 3)", "type": "stream"},
    {"id": "zzQps7kFo9M", "title": "WuBu - Poppy Playtime 5 (Part 2)", "type": "stream"},
    {"id": "wyD5qtPWdIk", "title": "WuBu - Poppy Playtime Chapter 5 (Part 1)", "type": "stream"},
]

# Shorts
SHORTS = [
    {"id": "dsCbJ67d_G0", "title": "what is going on here guys", "type": "short"},
    {"id": "pFzIT2xU7es", "title": "the world is a better place now", "type": "short"},
    {"id": "flyIZI4TG4U", "title": "does anything happen in the game?", "type": "short"},
    {"id": "dSVUo5agh4o", "title": "wait a minute what happened", "type": "short"},
    {"id": "p3W4-z8W12E", "title": "omg stuff happen", "type": "short"},
]

OUTPUT_DIR = "/home/wubu/seymour-project/whiteboard/youtube-context"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_title(title):
    """Clean title for filename."""
    return re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_').lower()

def fetch_subtitles(video_id):
    """Fetch auto-generated subtitles for a video."""
    try:
        transcript = YouTubeTranscriptApi().fetch(video_id, languages=['en'])
        formatter = TextFormatter()
        text = formatter.format_transcript(transcript)
        return {
            "success": True,
            "lines": len(transcript),
            "text": text,
            "word_count": len(text.split())
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    all_videos = VIDEOS + SHORTS
    results = []
    
    for video in all_videos:
        vid_id = video["id"]
        title = video["title"]
        vtype = video["type"]
        
        print(f"Fetching [{vtype}]: {title} ({vid_id})...")
        result = fetch_subtitles(vid_id)
        result.update(video)
        results.append(result)
        
        if result["success"]:
            # Save raw text
            filename = f"{vtype}_{clean_title(title)}_{vid_id}.txt"
            filepath = os.path.join(OUTPUT_DIR, filename)
            with open(filepath, 'w') as f:
                f.write(f"# {title}\n")
                f.write(f"# Type: {vtype}\n")
                f.write(f"# Video ID: {vid_id}\n")
                f.write(f"# Lines: {result['lines']}\n")
                f.write(f"# Words: {result['word_count']}\n")
                f.write(f"# URL: https://www.youtube.com/watch?v={vid_id}\n\n")
                f.write(result["text"])
            
            print(f"  ✓ Saved {result['lines']} lines ({result['word_count']} words)")
        else:
            print(f"  ✗ Failed: {result['error'][:80]}")
    
    # Save metadata index
    index_path = os.path.join(OUTPUT_DIR, "_index.json")
    with open(index_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Summary
    total_words = sum(r.get("word_count", 0) for r in results if r["success"])
    success_count = sum(1 for r in results if r["success"])
    fail_count = sum(1 for r in results if not r["success"])
    
    print(f"\n{'='*50}")
    print(f"EXTRACTION COMPLETE")
    print(f"  Success: {success_count}")
    print(f"  Failed:  {fail_count}")
    print(f"  Total words: {total_words}")
    print(f"  Output: {OUTPUT_DIR}/")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
