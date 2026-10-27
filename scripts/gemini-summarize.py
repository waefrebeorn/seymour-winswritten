#!/usr/bin/env python3
"""
Seymour Video Summarizer
Uses Google Gemini to generate AI summaries of YouTube videos from the WuBu Streams channel.
Requires GEMINI_API_KEY or GOOGLE_API_KEY environment variable.
"""

import os
import json
import requests

API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Videos to summarize (from extraction results)
VIDEOS = [
    {"id": "REK_MmenDK8", "title": "WuBu - Psychonauts 2", "words": 29625},
    {"id": "MGKmSVmZ2OU", "title": "WuBu - Psychonauts 2 part 1", "words": 28974},
    {"id": "4LxOKWC4cho", "title": "WuBu - Poppy Playtime 5 (Part 3)", "words": 34733},
    {"id": "zzQps7kFo9M", "title": "WuBu - Poppy Playtime 5 (Part 2)", "words": 25521},
    {"id": "wyD5qtPWdIk", "title": "WuBu - Poppy Playtime Chapter 5 (Part 1)", "words": 18490},
]

OUTPUT_DIR = "/home/wubu/seymour-project/whiteboard/youtube-context"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def summarize_video(video_id, title):
    """Get AI summary of a YouTube video via Gemini."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    prompt = f"""Watch this YouTube video and provide a comprehensive summary.

Video: {title}
URL: {url}

Please provide:
1. **Overview** (2-3 sentences): What is this video about? What game is being played?
2. **Key Moments** (bullet points): The 5-10 most important/funny/interesting moments
3. **Topics Discussed** (tags): What subjects, games, or themes come up?
4. **Emotional Tone**: What's the overall vibe? (funny, tense, chaotic, calm, etc.)
5. **Memorable Quotes** (if any): Standout lines or reactions from the streamer

Format as JSON with keys: overview, key_moments, topics, tone, quotes"""

    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2048
        }
    }
    
    try:
        resp = requests.post(BASE_URL, headers=headers, params=params, json=data, timeout=120)
        resp.raise_for_status()
        result = resp.json()
        
        if "candidates" in result and result["candidates"]:
            text = result["candidates"][0]["content"]["parts"][0]["text"]
            # Try to parse as JSON
            try:
                # Strip markdown code block if present
                text = text.strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1] if "\n" in text else text[3:]
                    if text.endswith("```"):
                        text = text[:-3]
                    text = text.strip()
                parsed = json.loads(text)
                return {"success": True, "summary": parsed}
            except json.JSONDecodeError:
                return {"success": True, "summary": {"raw_text": text}}
        else:
            return {"success": False, "error": "No candidates in response", "raw": str(result)[:500]}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    if not API_KEY:
        print("ERROR: No GEMINI_API_KEY or GOOGLE_API_KEY found")
        return
    
    results = []
    
    for video in VIDEOS:
        vid_id = video["id"]
        title = video["title"]
        words = video["words"]
        
        print(f"Summarizing: {title} ({words} words of transcript)...")
        result = summarize_video(vid_id, title)
        result.update(video)
        results.append(result)
        
        if result["success"]:
            print(f"  ✓ Summary generated")
            if "overview" in result.get("summary", {}):
                print(f"    Overview: {result['summary']['overview'][:100]}...")
        else:
            print(f"  ✗ Failed: {result['error'][:100]}")
    
    # Save results
    output_path = os.path.join(OUTPUT_DIR, "_gemini-summaries.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    success_count = sum(1 for r in results if r["success"])
    print(f"\n{'='*50}")
    print(f"SUMMARY COMPLETE: {success_count}/{len(results)} successful")
    print(f"Output: {output_path}")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
