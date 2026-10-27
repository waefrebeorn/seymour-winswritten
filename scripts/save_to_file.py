#!/usr/bin/env python3
"""
Save transcript text to file via curl.
Usage: python3 save_to_file.py <video_id> <title> <text_file>
"""
import sys
import os
import re
from pathlib import Path

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

if len(sys.argv) < 4:
    print("Usage: python3 save_to_file.py <video_id> <title> <text_file>")
    sys.exit(1)

video_id = sys.argv[1]
title = sys.argv[2]
text_file = sys.argv[3]

# Read the raw transcript
with open(text_file) as f:
    raw = f.read()

# Parse YouTube transcript format
import re
entries = []

# Pattern: Timestamp + text until next timestamp
pattern = re.compile(r'(\d+:\d{2})\s*\d*\s*(?:minute[s]?,?\s*)?\d*\s*second[s]?')
matches = list(pattern.finditer(raw))

for i, match in enumerate(matches):
    time_str = match.group(1)
    start = match.end()
    end = matches[i+1].start() if i+1 < len(matches) else len(raw)
    text = raw[start:end].strip()
    if text:
        parts = time_str.split(':')
        if len(parts) == 2:
            mins = int(parts[0])
            secs = int(parts[1])
            hours = mins // 60
            mins = mins % 60
            ts = f"{hours:02d}:{mins:02d}:{secs:02d}"
        else:
            ts = time_str
        entries.append(f"[{ts}] {text}")

# Save
safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:50]
txt_path = OUTPUT_DIR / f"{safe}_{video_id}_transcript.txt"

with open(txt_path, 'w') as f:
    f.write(f"# {title}\n# {video_id}\n# Source: YouTube Engagement Panel\n\n")
    f.write('\n'.join(entries))

print(f"Saved: {txt_path} ({len(entries)} entries, {sum(len(e.split()) for e in entries)} words)")
