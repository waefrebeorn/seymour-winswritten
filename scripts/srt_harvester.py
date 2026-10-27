#!/usr/bin/env python3
"""
Seymour SRT Harvester
=====================
Uses browser automation to extract YouTube's auto-generated transcripts.
No local storage needed — reads directly from YouTube's engagement panel.

Strategy:
1. Navigate to video URL
2. Click "In this video" button (opens transcript panel)
3. Extract transcript text with timestamps
4. Save as formatted transcript (.txt) and SRT (.srt)
5. No audio download, no whisper, no storage bloat

Usage:
    This is a browser-context script — execute via Hermes browser_console()
"""

import os
import sys
import json
import re
from pathlib import Path

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# JS to extract transcript from YouTube engagement panel
TRANSCRIPT_JS = """
(function() {
    // Find the engagement panel section with the transcript
    var panels = document.querySelectorAll('[class*="style-scope ytd-engagement-panel-section-list-renderer"]');
    var transcriptText = '';
    
    for (var i = 0; i < panels.length; i++) {
        var text = panels[i].textContent;
        // Transcript panel has timestamps like "0:09" and "9 seconds"
        if (/\d+:\d+/.test(text) && text.length > 1000) {
            transcriptText = text;
            break;
        }
    }
    
    if (!transcriptText) {
        return JSON.stringify({error: 'No transcript found', length: 0});
    }
    
    // Parse timestamps and text
    // Format: "0:099 secondsfor once in my life..."
    var entries = [];
    var pattern = /(\d+:\d+)\d+\s*seconds([^0-9]*?)(?=\d+:\d+\d+\s*seconds|$)/g;
    var match;
    
    while ((match = pattern.exec(transcriptText)) !== null) {
        entries.push({
            timestamp: match[1],
            text: match[2].trim()
        });
    }
    
    // Try alternate format: "1 minute, 5 secondsText..."
    if (entries.length === 0) {
        var pattern2 = /(\d+:\d+|(?:\d+ minute[s]?, )?\d+ second[s]?)\s*(?:\s*)([^0-9]+?)(?=(?:\d+ minute[s]?, )?\d+ second[s]?|$)/g;
        while ((match = pattern2.exec(transcriptText)) !== null) {
            if (match[2] && match[2].trim().length > 2) {
                entries.push({
                    timestamp: match[1],
                    text: match[2].trim()
                });
            }
        }
    }
    
    return JSON.stringify({
        length: entries.length,
        textLength: transcriptText.length,
        entries: entries.slice(0, 5)
    });
"""

def format_time_to_srt(timestamp):
    """Convert YouTube timestamp format to SRT time format."""
    # Handle "0:09" or "1 minute, 5 seconds" formats
    if 'minute' in timestamp.lower():
        match = re.match(r'(\d+)\s*minute[s]?,?\s*(\d+)\s*second[s]?', timestamp)
        if match:
            mins, secs = int(match.group(1)), int(match.group(2))
            total_seconds = mins * 60 + secs
            hours = total_seconds // 3600
            remaining = total_seconds % 3600
            mins = remaining // 60
            secs = remaining % 60
            return f"{hours:02d}:{mins:02d}:{secs:02d},000"
    else:
        parts = timestamp.split(':')
        if len(parts) == 2:
            mins, secs = int(parts[0]), int(parts[1])
            return f"00:{mins:02d}:{secs:02d},000"
        elif len(parts) == 3:
            hours, mins, secs = int(parts[0]), int(parts[1]), int(parts[2])
            return f"{hours:02d}:{mins:02d}:{secs:02d},000"
    
    return "00:00:00,000"


def main():
    """Print instructions for browser automation."""
    print("=" * 60)
    print("SEYMOUR SRT HARVESTER — Browser-Based Extraction")
    print("=" * 60)
    print("")
    print("This tool uses YouTube's built-in auto-generated transcripts")
    print("to extract text WITHOUT downloading audio files.")
    print("")
    print("Instructions:")
    print("1. Navigate to each video URL via browser()")
    print("2. Click 'In this video' button (ref=eXXX)")
    print("3. Extract transcript via console() using TRANSCRIPT_JS")
    print("4. Save output to captions/ directory")
    print("")
    print("Output format:")
    print("  - .txt: Human-readable transcript with timestamps")
    print("  - .rt: Standard SRT subtitle format")
    print("")
    print("Benefits over local whisper:")
    print("  - No audio download (saves GBs of storage)")
    print("  - Uses YouTube's servers (fast, no CPU)")
    print("  - Works on all videos with auto-captions")
    print("  - No OOM risk")
    print("=" * 60)


if __name__ == "__main__":
    main()
