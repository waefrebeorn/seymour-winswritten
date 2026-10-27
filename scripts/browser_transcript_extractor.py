#!/usr/bin/env python3
"""
Save transcript from browser CDP.
Connects to the browser's CDP, navigates to each video,
extracts transcript, and saves to file.
"""

import json
import subprocess
import time
import re
import os
import sys
import asyncio
import websockets
import base64
from pathlib import Path

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")
PROGRESS_FILE = OUTPUT_DIR / "browser_extract_progress.json"

def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": [], "no_panel": [], "failed": [], "last_index": 0}

def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def get_video_id(url):
    match = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else None

async def get_ws_url():
    """Get WebSocket URL for the browser page"""
    import urllib.request
    resp = urllib.request.urlopen('http://localhost:9222/json', timeout=5)
    pages = json.loads(resp.read())
    for p in pages:
        if 'youtube.com' in p.get('url', ''):
            return p['webSocketDebuggerUrl']
    # Return first page if no youtube
    if pages:
        return pages[0]['webSocketDebuggerUrl']
    return None

async def send_cdp(ws, method, params=None, timeout=30):
    """Send CDP command and wait for response"""
    msg_id = int(time.time() * 1000) % 1000000
    msg = {"id": msg_id, "method": method}
    if params:
        msg["params"] = params
    
    await ws.send(json.dumps(msg))
    
    # Wait for response
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = await asyncio.wait_for(ws.recv(), timeout=1)
            data = json.loads(resp)
            if data.get("id") == msg_id:
                return data
        except asyncio.TimeoutError:
            continue
    return None

async def navigate_and_extract(ws, video_id):
    """Navigate to video and extract transcript from engagement panel"""
    
    # Navigate
    url = f"https://www.youtube.com/watch?v={video_id}"
    await send_cdp(ws, "Page.navigate", {"url": url})
    await asyncio.sleep(4)  # Wait for page load
    
    # Check if "In this video" panel exists
    check_js = """
    (function() {
        var headers = document.querySelectorAll('[class*="panel-title-header"], [class*="header-text"]');
        for (var i = 0; i < headers.length; i++) {
            if ((headers[i].textContent || '').trim() === 'In this video') {
                return 'HAS_PANEL';
            }
        }
        return 'NO_PANEL';
    })()
    """
    result = await send_cdp(ws, "Runtime.evaluate", {"expression": check_js})
    if not result or "NO_PANEL" in str(result):
        return None, "no_panel"
    
    # Click the "In this video" panel
    click_js = """
    (function() {
        var headers = document.querySelectorAll('[class*="panel-title-header"], [class*="header-text"]');
        for (var i = 0; i < headers.length; i++) {
            if ((headers[i].textContent || '').trim() === 'In this video') {
                headers[i].click();
                return 'CLICKED';
            }
        }
        return 'NOT_FOUND';
    })()
    """
    await send_cdp(ws, "Runtime.evaluate", {"expression": click_js})
    await asyncio.sleep(1.5)
    
    # Click Transcript tab
    transcript_js = """
    (function() {
        var tabs = document.querySelectorAll('[role="tab"]');
        for (var t = 0; t < tabs.length; t++) {
            if ((tabs[t].textContent || '').trim() === 'Transcript') {
                tabs[t].click();
                return 'CLICKED_TRANSCRIPT';
            }
        }
        return 'NO_TRANSCRIPT_TAB';
    })()
    """
    result = await send_cdp(ws, "Runtime.evaluate", {"expression": transcript_js})
    if result and "NO_TRANSCRIPT_TAB" in str(result):
        return None, "no_transcript_tab"
    
    await asyncio.sleep(3)  # Wait for transcript to load
    
    # Extract transcript text
    extract_js = """
    (function() {
        var panels = document.querySelectorAll('[class*="style-scope ytd-engagement-panel-section-list-renderer"]');
        for (var i = 0; i < panels.length; i++) {
            var text = panels[i].textContent || '';
            if (/\\d+:\\d+/.test(text) && text.length > 1000) {
                return text;
            }
        }
        return '';
    })()
    """
    result = await send_cdp(ws, "Runtime.evaluate", {"expression": extract_js}, timeout=30)
    
    if not result:
        return None, "extraction_failed"
    
    # Get the result value
    value = result.get("result", {}).get("result", {}).get("value", "")
    if not value or len(value) < 100:
        return None, "empty_transcript"
    
    return value, "success"

async def get_video_title(ws):
    """Get the video title"""
    js = "document.title || ''"
    result = await send_cdp(ws, "Runtime.evaluate", {"expression": js})
    if result:
        return result.get("result", {}).get("result", {}).get("value", "untitled")
    return "untitled"

async def process_all():
    """Process all videos"""
    ws_url = await get_ws_url()
    if not ws_url:
        print("ERROR: Browser not available at localhost:9222")
        return
    
    print(f"Connected to browser: {ws_url}")
    
    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
    
    progress = load_progress()
    done_ids = {p.get("video_id") for p in progress.get("done", [])}
    no_panel_ids = {p.get("video_id") for p in progress.get("no_panel", [])}
    
    print(f"Total videos: {len(urls)}")
    print(f"Already done: {len(done_ids)}")
    print(f"No panel (previously): {len(no_panel_ids)}")
    
    remaining = []
    for i, url in enumerate(urls):
        vid = get_video_id(url)
        if vid and vid not in done_ids and vid not in no_panel_ids:
            remaining.append((i, url, vid))
    
    print(f"Remaining: {len(remaining)}")
    print("=" * 60)
    
    async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
        # Enable Page domain
        await send_cdp(ws, "Page.enable")
        
        success_count = 0
        no_panel_count = 0
        fail_count = 0
        
        for idx, (orig_idx, url, vid) in enumerate(remaining):
            print(f"\n[{idx+1}/{len(remaining)}] {vid}")
            
            try:
                text, status = await navigate_and_extract(ws, vid)
                
                if status == "success" and text:
                    # Get title
                    title = await get_video_title(ws)
                    
                    # Save to file
                    safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:50]
                    filename = f"{safe}_{vid}_engagement.txt"
                    filepath = OUTPUT_DIR / filename
                    
                    with open(filepath, 'w') as f:
                        f.write(f"# {title}\n# {vid}\n# Source: YouTube Engagement Panel\n\n{text}")
                    
                    words = len(text.split())
                    print(f"  ✅ SAVED: {words} words → {filename}")
                    
                    progress["done"].append({
                        "video_id": vid,
                        "title": title,
                        "words": words,
                        "source": "engagement_panel"
                    })
                    success_count += 1
                    
                elif status == "no_panel":
                    print(f"  ⚠️ No engagement panel")
                    progress["no_panel"].append({
                        "video_id": vid,
                        "url": url
                    })
                    no_panel_count += 1
                    
                else:
                    print(f"  ❌ {status}")
                    progress["failed"].append({
                        "video_id": vid,
                        "url": url,
                        "error": status
                    })
                    fail_count += 1
                    
            except Exception as e:
                print(f"  ❌ Exception: {e}")
                progress["failed"].append({
                    "video_id": vid,
                    "url": url,
                    "error": str(e)[:100]
                })
                fail_count += 1
            
            # Save progress every 5 videos
            if (idx + 1) % 5 == 0:
                save_progress(progress)
                print(f"\n--- Progress saved: {success_count} ok, {no_panel_count} no panel, {fail_count} failed ---\n")
        
        # Final save
        save_progress(progress)
        
        print(f"\n{'='*60}")
        print(f"BATCH COMPLETE")
        print(f"  Success: {success_count}")
        print(f"  No panel: {no_panel_count}")
        print(f"  Failed: {fail_count}")
        print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(process_all())
