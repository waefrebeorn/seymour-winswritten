#!/usr/bin/env python3
"""
selective_clip.py — Timestamp-indexed selective transcript clipping

Builds a searchable index of all transcripts with timestamps,
then produces topic-clipped versions for Ponderable entries.

Usage:
  python3 selective_clip.py index <transcript_dir> <output_dir>
  python3 selective_clip.py clip <transcript_dir> <video_id> <keywords_file> <output.srt>
  python3 selective_clip.py search <index.json> <keyword>
  python3 selective_clip.py batch-clip <index.json> <topics_dir> <output_dir>
"""

import json, os, sys, re, hashlib
from pathlib import Path

TRANSCRIPT_DIR = "/home/wubu/seymour-project/whiteboard/seymour-pipe/captions"
INDEX_FILE = "/home/wubu/seymour-project/absorption/data/timestamp_index.json"

def extract_video_id(filename):
    """Extract 11-char video ID from transcript filename."""
    # Patterns: TITLE_VIDEOID_transcript.txt or TITLE_VIDEOID_engagement.txt
    for suffix in ['_transcript.txt', '_engagement.txt']:
        if filename.endswith(suffix):
            stem = filename[:-len(suffix)]
            # Video IDs are 11 chars, but titles can have underscores
            # Try last 11 chars before any trailing underscore
            parts = stem.rsplit('_', 1)
            if len(parts) == 2 and len(parts[1]) == 11:
                return parts[1]
            # Fallback: last 11 chars
            if len(stem) >= 11:
                candidate = stem[-11:]
                if re.match(r'^[a-zA-Z0-9_-]{11}$', candidate):
                    return candidate
    return None

def parse_inline_timestamps(text):
    """Parse inline timestamps like '0:055 seconds' from engagement panels."""
    segments = []
    # Pattern: timestamp embedded in text
    # Examples: "0:055 seconds", "1:061 minute, 6 seconds", "0:1818 seconds"
    pattern = r'(\d+):(\d+)(\d+)\s*(?:seconds?|minute)?'
    
    current_ts = 0
    current_text = ""
    
    for line in text.split('\n'):
        if not line.strip():
            continue
        
        # Find all timestamp matches in this line
        matches = list(re.finditer(pattern, line))
        
        if matches:
            # Use first match as segment start
            m = matches[0]
            mins = int(m.group(1))
            secs = int(m.group(2) + m.group(3))  # group 2+3 = seconds digits
            # Actually the pattern captures weird — let me use a simpler approach
            pass
        
        segments.append({'ts': current_ts, 'text': line})
        current_ts += 5  # Estimate 5 sec per line
    
    return segments

def parse_standard_timestamps(text):
    """Parse [MM:SS] or [HH:MM:SS] per-line timestamps."""
    segments = []
    pattern = r'\[(\d{1,2}):(\d{2})(?::(\d{2}))?\]\s*(.*)'
    
    for line in text.split('\n'):
        m = re.match(pattern, line)
        if m:
            if m.group(3):  # HH:MM:SS
                ts = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
            else:  # MM:SS
                ts = int(m.group(1)) * 60 + int(m.group(2))
            text_content = m.group(4).strip()
            if text_content:
                segments.append({
                    'ts': ts,
                    'text': text_content,
                    'ts_str': f"[{m.group(1)}:{m.group(2)}]"
                })
    
    return segments

def parse_transcript_file(filepath):
    """Auto-detect timestamp format and parse."""
    with open(filepath) as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Skip header (lines starting with #)
    body_start = 0
    for i, line in enumerate(lines):
        if not line.startswith('#') and line.strip():
            body_start = i
            break
    
    body = '\n'.join(lines[body_start:])
    
    # Detect format: check first 10 non-empty lines
    sample = '\n'.join(lines[body_start:body_start+20])
    
    if re.search(r'\[\d{1,2}:\d{2}\]', sample):
        # Standard [MM:SS] format
        return parse_standard_timestamps(body)
    elif re.search(r'\d+:\d{4,6}\s*(?:seconds?|minute)', sample):
        # Inline timestamp format (engagement panel)
        return parse_inline_timestamps(body)
    else:
        # No timestamps — treat each line as 5-second segment
        segs = []
        for i, line in enumerate(lines[body_start:]):
            if line.strip():
                segs.append({'ts': i * 5, 'text': line.strip(), 'ts_str': f"[{i*5//60:02d}:{i*5%60:02d}]"})
        return segs

def build_index(transcript_dir, output_path):
    """Build timestamp index of all transcripts."""
    index = {'videos': [], 'totals': {'words': 0, 'segments': 0, 'files': 0}}
    
    for filename in sorted(os.listdir(transcript_dir)):
        if not filename.endswith('.txt'):
            continue
        
        filepath = os.path.join(transcript_dir, filename)
        vid = extract_video_id(filename)
        
        try:
            segments = parse_transcript_file(filepath)
        except Exception as e:
            print(f"  ⚠️ {filename}: {e}")
            continue
        
        # Count words
        total_words = sum(len(s['text'].split()) for s in segments)
        duration = segments[-1]['ts'] if segments else 0
        
        # Extract title from header
        with open(filepath) as f:
            title = ""
            for line in f:
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
        
        entry = {
            'video_id': vid or '?',
            'title': title,
            'filename': filename,
            'segments': len(segments),
            'words': total_words,
            'duration_sec': duration,
            'duration_min': round(duration / 60)
        }
        
        index['videos'].append(entry)
        index['totals']['words'] += total_words
        index['totals']['segments'] += len(segments)
        index['totals']['files'] += 1
    
    # Write
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(index, f, indent=2)
    
    print(f"Index built: {index['totals']['files']} files, "
          f"{index['totals']['words']:,} words, "
          f"{index['totals']['segments']:,} segments")
    
    return index

def search_index(index_path, keyword):
    """Search index for videos containing keyword."""
    with open(index_path) as f:
        index = json.load(f)
    
    keyword_lower = keyword.lower()
    results = []
    
    for video in index['videos']:
        # Search in title
        if keyword_lower in video['title'].lower():
            results.append(video)
            continue
        
        # Search in transcript content
        filepath = os.path.join(TRANSCRIPT_DIR, video['filename'])
        try:
            with open(filepath) as f:
                content = f.read()
            if keyword_lower in content.lower():
                results.append(video)
        except:
            pass
    
    return results

def clip_video(transcript_dir, video_id, keywords, output_path, padding_sec=10):
    """Produce a clipped SRT from a video transcript matching keywords."""
    # Find the transcript file
    transcript_file = None
    for filename in os.listdir(transcript_dir):
        if video_id in filename and filename.endswith('.txt'):
            transcript_file = os.path.join(transcript_dir, filename)
            break
    
    if not transcript_file:
        print(f"  ❌ No transcript for {video_id}")
        return None
    
    # Parse segments
    segments = parse_transcript_file(transcript_file)
    
    # Find matching segments
    matched = []
    keywords_lower = [k.lower() for k in keywords]
    
    for i, seg in enumerate(segments):
        text_lower = seg['text'].lower()
        if any(kw in text_lower for kw in keywords_lower):
            # Add padding
            start_idx = max(0, i - padding_sec // 5)
            end_idx = min(len(segments), i + padding_sec // 5 + 1)
            for j in range(start_idx, end_idx):
                if j not in [m['idx'] for m in matched]:
                    matched.append({**segments[j], 'idx': j})
    
    if not matched:
        print(f"  ⚠️ No matches for {keywords}")
        return None
    
    # Sort by timestamp
    matched.sort(key=lambda x: x['ts'])
    
    # Generate SRT
    srt_lines = []
    for i, seg in enumerate(matched, 1):
        start = seg['ts']
        end = start + 5  # 5-second segments
        
        sh, sm, ss = start // 3600, (start % 3600) // 60, start % 60
        eh, em, es = end // 3600, (end % 3600) // 60, end % 60
        
        srt_lines.append(f"{i}")
        srt_lines.append(f"{sh:02d}:{sm:02d}:{ss:02d},000 --> {eh:02d}:{em:02d}:{es:02d},000")
        srt_lines.append(seg['text'])
        srt_lines.append("")
    
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(srt_lines))
    
    print(f"  ✅ Clipped {len(matched)} segments → {output_path}")
    return output_path

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 selective_clip.py index <transcript_dir> <output.json>")
        print("  python3 selective_clip.py clip <video_id> <keywords> <output.srt>")
        print("  python3 selective_clip.py search <index.json> <keyword>")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'index':
        transcript_dir = sys.argv[2] if len(sys.argv) > 2 else TRANSCRIPT_DIR
        output = sys.argv[3] if len(sys.argv) > 3 else INDEX_FILE
        build_index(transcript_dir, output)
    
    elif cmd == 'clip':
        video_id = sys.argv[2]
        keywords = sys.argv[3].split(',')
        output = sys.argv[4] if len(sys.argv) > 4 else f"/tmp/{video_id}_clip.srt"
        clip_video(TRANSCRIPT_DIR, video_id, keywords, output)
    
    elif cmd == 'search':
        index_path = sys.argv[2]
        keyword = sys.argv[3]
        results = search_index(index_path, keyword)
        print(f"\n{len(results)} videos matching '{keyword}':")
        for r in results[:20]:
            print(f"  {r['video_id']}: {r['title'][:60]} ({r['words']} words)")
    
    elif cmd == 'batch-clip':
        index_path = sys.argv[2]
        topics_dir = sys.argv[3]
        output_dir = sys.argv[4]
        # Each file in topics_dir is a .txt with keywords (one per line)
        # Output: one SRT per topic per matching video
        os.makedirs(output_dir, exist_ok=True)
        
        with open(index_path) as f:
            index = json.load(f)
        
        for topic_file in sorted(os.listdir(topics_dir)):
            if not topic_file.endswith('.txt'):
                continue
            
            topic_name = topic_file[:-4]
            with open(os.path.join(topics_dir, topic_file)) as f:
                keywords = [line.strip() for line in f if line.strip()]
            
            print(f"\nTopic: {topic_name} ({len(keywords)} keywords)")
            
            for video in index['videos']:
                filepath = os.path.join(TRANSCRIPT_DIR, video['filename'])
                try:
                    with open(filepath) as f:
                        content = f.read().lower()
                    if any(kw.lower() in content for kw in keywords):
                        out_path = os.path.join(output_dir, 
                                               f"{topic_name}_{video['video_id']}.srt")
                        clip_video(TRANSCRIPT_DIR, video['video_id'], 
                                   keywords, out_path)
                except Exception as e:
                    print(f"  ⚠️ {video['video_id']}: {e}")

if __name__ == "__main__":
    main()
