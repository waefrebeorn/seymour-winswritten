#!/usr/bin/env python3
"""Parse YouTube transcript format and save as .txt"""
import sys
import re

raw = sys.stdin.read()

# Parse the format: "0:099 secondsTEXT" or "1 hour, 5 secondsTEXT"
# Pattern: (MM:SS or H:MM:SS or variations) + "seconds" + TEXT
entries = []

# Split by finding timestamp boundaries
# Timestamps look like: "0:09" "9 seconds" or "1:01" "1 minute, 1 second"
# Concatenated they look like: "0:099 seconds" "1:011 minute, 1 second"

# Find all timestamp positions
pattern = re.compile(r'(\d+:\d{2})\s*\d*\s*(?:minute[s]?,?\s*)?\d*\s*second[s]?')

matches = list(pattern.finditer(raw))

for i, match in enumerate(matches):
    time_str = match.group(1)
    start = match.end()
    end = matches[i+1].start() if i+1 < len(matches) else len(raw)
    text = raw[start:end].strip()
    if text:
        entries.append((time_str, text))

# Format output
lines = []
for time_str, text in entries:
    parts = time_str.split(':')
    if len(parts) == 2:
        mins = int(parts[0])
        secs = int(parts[1])
        hours = mins // 60
        mins = mins % 60
        ts = f"{hours:02d}:{mins:02d}:{secs:02d}"
    else:
        time_str
    lines.append(f"[{ts}] {text}")

sys.stdout.write('\n'.join(lines))
print(f"\nTotal entries: {len(entries)}", file=sys.stderr)
