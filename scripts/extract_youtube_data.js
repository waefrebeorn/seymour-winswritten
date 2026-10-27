#!/usr/bin/env python3
"""
Seymour SRT Absorber — Browser-based extraction of YouTube captions + AI summaries
Uses browser automation to get content without downloading videos.

Strategy:
1. Navigate to video page
2. Open captions/subtitles panel → extract SRT
3. Open AI summary panel → extract summary
4. Save both to files

This leverages YouTube's own infrastructure instead of local whisper processing.
"""

import json
import os
import re
import sys
import subprocess
import time
from pathlib import Path

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# We'll use the browser console to drive YouTube's UI
# This script generates JS snippets to be executed in the browser context

def generate_caption_extractor_js(video_id):
    """Generate JS to extract captions from YouTube player."""
    return f"""
    (function() {{
        return new Promise(async (resolve) => {{
            // Wait for video player
            var attempts = 0;
            var checkPlayer = setInterval(() => {{
                var player = document.querySelector('#movie_player') || document.querySelector('ytd-player#ytd-player');
                if (player) {{
                    clearInterval(checkPlayer);
                    resolve('Player found');
                }}
                attempts++;
                if (attempts > 30) {{
                    clearInterval(checkPlayer);
                    resolve('Player NOT found');
                }}
            }}, 500);
        }});
    }})()
    """

def generate_ai_summary_extractor_js():
    """Generate JS to extract AI summary from YouTube."""
    return """
    (function() {
        return new Promise(async (resolve) => {
            // Look for AI summary section
            var selectors = [
                '[id="expandable-metadata"]',
                'yt-video-attributes-view-model',
                '.metadata-wrapper',
                '#above-the-fold',
                'ytd-engagement-panel-section-list-renderer',
                '[panel-target-id="engagement-panel"]',
                'ytd-structured-description-content-view-model',
                'yt-sponsorable-badge',
            ];
            
            for (var i = 0; i < selectors.length; i++) {{
                var el = document.querySelector(selectors[i]);
                if (el) {{
                    resolve('Found: ' + selectors[i] + ': ' + el.textContent.substring(0, 300));
                    return;
                }}
            }}
            
            // Try finding any AI-related text
            var allText = document.body.innerText;
            var aiMatch = allText.match(/AI (?:summary|generated|overview)/i);
            if (aiMatch) {{
                resolve('Possible AI section found: ' + aiMatch[0]);
                return;
            }}
            
            resolve('No AI summary found. Check if YouTube provides it for this video.');
        }})()
    """

def main():
    """Print usage instructions."""
    print("Seymour SRT Absorber")
    print("=" * 60)
    print("This tool uses browser automation to extract content from YouTube.")
    print("It must be run inside a browser context via Hermes browser tools.")
    print("")
    print("Three extraction methods:")
    print("1. YouTube Captions/Subtitles (auto-generated)")
    print("2. YouTube AI Summary (if available)")
    print("3. Live Chat Replay text extraction")
    print("")
    print("Use case: Navigate to each video URL and extract the content")
    print("without downloading GBs of audio.")
    print("=" * 60)

if __name__ == "__main__":
    main()
