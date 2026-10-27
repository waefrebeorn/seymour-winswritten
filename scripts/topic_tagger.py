#!/usr/bin/env python3
"""
topic_tagger.py — Add LLM-generated topics to the Pre-Seymour index.

Uses local llama-server (Gemma-4-12B) to extract 5 high-level topics per video.
Run after whisper pipeline completes and index is rebuilt.
"""

import json
import requests
import time
from pathlib import Path

INDEX_PATH = Path("/home/wubu/seymour-project/pre_seymour/index.json")
LLAMA_URL = "http://localhost:18802/v1/chat/completions"
MODEL = "gemma-4-12B-it-qat-UD-Q4_K_XL.gguf"
BATCH_SIZE = 10  # Save after every N videos
SLEEP_BETWEEN = 1.0  # Seconds between requests

PROMPT_TEMPLATE = """Extract 5 high-level topics from this video title as a JSON array only. No other text.

Video title: "{title}"
"""

def extract_topics(title: str, max_retries=2) -> list[str]:
    """Extract topics from a single title using the local LLM."""
    prompt = PROMPT_TEMPLATE.format(title=title)
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                LLAMA_URL,
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 200
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json()
                reasoning = result['choices'][0]['message'].get('reasoning_content', '')
                content = result['choices'][0]['message'].get('content', '')
                
                # Parse topics from reasoning (looking for "Topic N: ..." patterns)
                import re
                topics = []
                
                # First try to find JSON array in content or reasoning
                for text in [content, reasoning]:
                    if text:
                        # Look for JSON array
                        json_match = re.search(r'\[.*?\]', text, re.DOTALL)
                        if json_match:
                            try:
                                arr = json.loads(json_match.group())
                                if isinstance(arr, list):
                                    topics = [str(x).strip() for x in arr if str(x).strip()]
                                    if topics:
                                        return topics[:5]
                            except:
                                pass
                
                # Fallback: extract "Topic N: ..." lines from reasoning (may have bullet points)
                for line in reasoning.split('\n'):
                    line = line.strip()
                    # Remove leading bullet points like "*   " or "- "
                    line = re.sub(r'^[\*\-\•\d\.\)]+\s*', '', line)
                    m = re.match(r'Topic\s*\d+\s*[:]\s*(.+)', line)
                    if m:
                        topic = m.group(1).strip().strip('.')
                        if topic and len(topic) < 100:
                            topics.append(topic)
                
                # Also try to extract bullet points that look like topics (short phrases after bullets)
                if not topics:
                    for line in reasoning.split('\n'):
                        line = line.strip()
                        # Match lines like "*   Topic: Something" or "* Something"
                        m = re.match(r'^[\*\-\•]\s*(.+)', line)
                        if m:
                            candidate = m.group(1).strip()
                            # Check if it looks like a topic (short, not a sentence)
                            if candidate and len(candidate) < 100 and not candidate.startswith('Input:') and not candidate.startswith('Task:') and not candidate.startswith('Format:') and not candidate.startswith('Constraint:'):
                                topics.append(candidate)
                
                if topics:
                    return topics[:5]
            
            print(f"  Attempt {attempt + 1} failed for: {title[:50]}... (status: {response.status_code})")
            if attempt < max_retries:
                time.sleep(2)
                
        except Exception as e:
            print(f"  Error on attempt {attempt + 1}: {e}")
            if attempt < max_retries:
                time.sleep(2)
    
    return []

def main():
    print(f"Loading index from {INDEX_PATH}...")
    with open(INDEX_PATH) as f:
        index = json.load(f)
    
    total = len(index)
    print(f"Total videos: {total}")
    
    # Count already tagged
    already_tagged = sum(1 for v in index.values() if v.get('topics'))
    print(f"Already tagged: {already_tagged}")
    
    # Process untagged videos
    processed = 0
    for vid, data in index.items():
        if data.get('topics'):
            continue
        
        title = data.get('title', '')
        if not title:
            continue
        
        print(f"[{processed + 1}/{total - already_tagged}] Tagging: {title[:80]}")
        topics = extract_topics(title)
        
        if topics:
            data['topics'] = topics
            print(f"  Topics: {topics}")
        else:
            data['topics'] = []
            print(f"  No topics extracted")
        
        processed += 1
        
        # Save periodically
        if processed % BATCH_SIZE == 0:
            print(f"  Saving progress ({processed} tagged)...")
            with open(INDEX_PATH, 'w') as f:
                json.dump(index, f, indent=2)
        
        time.sleep(SLEEP_BETWEEN)
    
    # Final save
    with open(INDEX_PATH, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"\nDone! Tagged {processed} videos. Index saved to {INDEX_PATH}")

if __name__ == "__main__":
    main()