#!/usr/bin/env python3
"""Save transcript data from stdin to file"""
import sys
import json
from pathlib import Path

data = json.load(sys.stdin)
output_dir = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")

video_id = data['videoId']
title = data['title']
formatted = data['formatted']
srt = data.get('srt', '')

safe = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')[:50]

# Save formatted transcript
txt_path = output_dir / f"{safe}_{video_id}_transcript.txt"
with open(txt_path, 'w') as f:
    f.write(formatted)
print(f"Saved: {txt_path}")

# Save SRT
if srt:
    srt_path = output_dir / f"{safe}_{video_id}.srt"
    with open(srt_path, 'w') as f:
        f.write(srt)
    print(f"Saved: {srt_path}")

print(f"Done: {len(formatted)} chars, {video_id}")
