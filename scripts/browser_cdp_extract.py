#!/usr/bin/env python3
"""
Batch YouTube Transcript Extractor — CDP v2
Uses Chrome DevTools Protocol on port 40581 to automate browser.
Navigates to each video, extracts engagement panel transcript + AI summary, saves to file.
"""

import json
import asyncio
import websockets
import re
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
URL_FILE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/all_videos.txt")
PROGRESS_FILE = OUTPUT_DIR / "browser_extract_progress.json"

CDP_PORT = 40581

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

async def get_youtube_ws_url():
    """Get WebSocket URL for a YouTube page via CDP"""
    # Get existing pages
    resp = urlopen(f'http://127.0.0.1:{CDP_PORT}/json', timeout=5)
    pages = json.loads(resp.read())
    for p in pages:
        if 'youtube.com' in p.get('url', '') and p.get('type') == 'page':
            return p['webSocketDebuggerUrl']
    # Create new page with PUT request
    req = Request(f'http://127.0.0.1:{CDP_PORT}/json/new?about:blank', method='PUT')
    resp = urlopen(req, timeout=5)
    page = json.loads(resp.read())
    return page['webSocketDebuggerUrl']

class CDPClient:
    def __init__(self, ws_url):
        self.ws = None
        self.ws_url = ws_url
        self.msg_id = 0
        
    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=100*1024*1024)
        await self.send("Page.enable")
        await self.send("Runtime.enable")
      
    async def send(self, method, params=None, timeout=30):
        self.msg_id += 1
        msg_id = self.msg_id
        msg = {"id": msg_id, "method": method}
        if params:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
      
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = await asyncio.wait_for(self.ws.recv(), timeout=2)
                data = json.loads(resp)
                if data.get("id") == msg_id:
                    return data
            except asyncio.TimeoutError:
                continue
        return None
  
    async def evaluate(self, expression, timeout=30):
        result = await self.send("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True
        }, timeout)
        if not result:
            return None
        return result.get("result", {}).get("result", {}).get("value")
  
    async def navigate(self, url):
        await self.send("Page.navigate", {"url": url})
        await asyncio.sleep(7)
  
    async def close(self):
        if self.ws:
            await self.ws.close()

async def extract_video(cdp, video_id):
    """Extract transcript and metadata from a single video"""
    url = f"https://www.youtube.com/watch?v={video_id}"
    await cdp.navigate(url)
  
    # Check for "In this video" panel - try twice
    has_panel = False
    for attempt in range(2):
        has_panel = await cdp.evaluate("""
        (function() {
            var headers = document.querySelectorAll('[class*="panel-title-header"], [class*="header-text"]');
            for (var i = 0; i < headers.length; i++) {
                if ((headers[i].textContent || '').trim() === 'In this video') return true;
            }
            return false;
        })()
        """)
        if has_panel:
            break
        if attempt == 0:
            await asyncio.sleep(5)
  
    if not has_panel:
        return {"status": "no_panel"}
  
    # Click "In this video"
    await cdp.evaluate("""
    (function() {
        var headers = document.querySelectorAll('[class*="panel-title-header"], [class*="header-text"]');
        for (var i = 0; i < headers.length; i++) {
            if ((headers[i].textContent || '').trim() === 'In this video') {
                headers[i].click();
                return 'clicked';
            }
        }
        return 'not_found';
    })()
    """)
    await asyncio.sleep(2)
  
    # Click "Transcript" tab
    clicked = await cdp.evaluate("""
    (function() {
        var tabs = document.querySelectorAll('[role="tab"]');
        for (var t = 0; t < tabs.length; t++) {
            if ((tabs[t].textContent || '').trim() === 'Transcript') {
                tabs[t].click();
                return 'clicked';
            }
        }
        return 'not_found';
    })()
    """)
  
    if clicked != 'clicked':
        return {"status": "no_transcript_tab"}
  
    await asyncio.sleep(4)
  
    # Extract transcript
    transcript = await cdp.evaluate("""
    (function() {
        var panels = document.querySelectorAll('[class*="style-scope ytd-engagement-panel-section-list-renderer"]');
        for (var i = 0; i < panels.length; i++) {
            var text = panels[i].textContent || '';
            if (/\\d+:\\d+/.test(text) && text.length > 1000) return text;
        }
        return '';
    })()
    """, timeout=60)
  
    if not transcript or len(transcript) < 100:
        # Retry: maybe content hasn't loaded yet, wait more
        await asyncio.sleep(5)
        transcript = await cdp.evaluate("""
        (function() {
            var panels = document.querySelectorAll('[class*="style-scope ytd-engagement-panel-section-list-renderer"]');
            for (var i = 0; i < panels.length; i++) {
                var text = panels[i].textContent || '';
                if (/\\d+:\\d+/.test(text) && text.length > 1000) return text;
            }
            return '';
        })()
        """, timeout=60)
        if not transcript or len(transcript) < 100:
            return {"status": "empty_transcript"}
  
    # Get title
    title = await cdp.evaluate("document.title || 'untitled'")
    if title.endswith(' - YouTube'):
        title = title[:-10]

    # Get AI summary (if present)
    ai_summary = await cdp.evaluate("""\
    (function() {
        var allText = document.body.innerText;
        var idx = allText.indexOf('AI summary');
        if (idx !== -1) return allText.substring(idx, idx + 5000);
        idx = allText.indexOf('AI overview');
        if (idx !== -1) return allText.substring(idx, idx + 5000);
        return '';
    })()\
    """)
    
    # Get video description
    description = await cdp.evaluate("""\
    (function() {
        var descEl = document.querySelector('#description-inline-formula-text') ||
                      document.querySelector('.ytd-expandable-video-description-body') ||
                      document.querySelector('ytd-video-description-renderer');
        if (descEl) return descEl.textContent || '';
        return '';
    })()\
    """)
    
    # Get chapters/key moments
    chapters = await cdp.evaluate("""\
    (function() {
        var chapters = [];
        var markers = document.querySelectorAll('ytd-engagement-panel-section-list-renderer ytd-video-chapter-renderer, ytd-macro-markers-list-renderer ytd-video-chapter-renderer');
        for (var i = 0; i < markers.length; i++) {
            var title = markers[i].querySelector('#title, .chapter-title, [class*="chapter"]');
            var time = markers[i].querySelector('#time, .chapter-time, [class*="time"]');
            if (title && time) {
                chapters.push({title: title.textContent.trim(), time: time.textContent.trim()});
            }
        }
        return JSON.stringify(chapters);
    })()\
    """)
    
    # Get full auto-generated transcript (click "Show transcript" button)
    full_transcript = ""
    try:
        # Try to find and click "Show transcript" button
        show_transcript = await cdp.evaluate("""\
        (function() {
            // Try multiple selectors for "Show transcript" button
            var selectors = [
                'ytd-button-renderer[aria-label*="transcript" i]',
                'ytd-button-renderer[aria-label*="Transcript" i]',
                'button[aria-label*="transcript" i]',
                'button[aria-label*="Transcript" i]',
                'yt-formatted-string:contains("Show transcript")',
                'yt-formatted-string:contains("Show Transcript")'
            ];
            for (var s = 0; s < selectors.length; s++) {
                var els = document.querySelectorAll(selectors[s]);
                for (var i = 0; i < els.length; i++) {
                    if (els[i].offsetParent !== null) { // visible
                        els[i].click();
                        return 'clicked';
                    }
                }
            }
            return 'not_found';
        })()\
        """)
    
        if show_transcript == 'clicked':
            await asyncio.sleep(3)  # Wait for transcript panel to open
            full_transcript = await cdp.evaluate("""\
            (function() {
                var panel = document.querySelector('ytd-engagement-panel-section-list-renderer[target-id="engagement-panel-searchable-transcript"]') ||
                           document.querySelector('ytd-transcript-search-panel-renderer') ||
                           document.querySelector('[class*="transcript-search-panel"]');
                if (panel) return panel.textContent || '';

                // Alternative: transcript segments
                var segments = document.querySelectorAll('ytd-transcript-segment-renderer, [class*="transcript-segment"]');
                var text = '';
                for (var i = 0; i < segments.length; i++) {
                    var time = segments[i].querySelector('.segment-timestamp, [class*="timestamp"]');
                    var content = segments[i].querySelector('.segment-text, [class*="text"]');
                    if (time && content) {
                        text += time.textContent.trim() + ' ' + content.textContent.trim() + '\\n';
                    }
                }
                return text;
            })()\
            """)
    except:
        pass
    
    # Get video metadata
    metadata = await cdp.evaluate("""\
    (function() {
        var meta = {};
        meta.views = document.querySelector('#count > ytd-video-view-count-renderer, [class*="view-count"]')?.textContent?.trim() || '';
        meta.likes = document.querySelector('#top-level-buttons-computed button[aria-label*="like" i]')?.textContent?.trim() || '';
        meta.upload_date = document.querySelector('#date yt-formatted-string, [class*="date"]')?.textContent?.trim() || '';
        meta.channel = document.querySelector('#channel-name a, #owner-name a, ytd-channel-name a')?.textContent?.trim() || '';
        return meta;
    })()\
    """)

    return {
        "status": "success",
        "title": title,
        "transcript": transcript,
        "full_transcript": full_transcript or "",
        "ai_summary": ai_summary or "",
        "description": description or "",
        "chapters": chapters or "",
        "metadata": metadata or {}
    }

async def main():
    ws_url = await get_youtube_ws_url()
    print(f"CDP: {ws_url}", flush=True)
  
    cdp = CDPClient(ws_url)
    await cdp.connect()
  
    with open(URL_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
  
    progress = load_progress()
    done_ids = {p.get("video_id") for p in progress.get("done", [])}
    no_panel_ids = {p.get("video_id") for p in progress.get("no_panel", [])}
    failed_ids = {p.get("video_id") for p in progress.get("failed", [])}
  
    remaining = []
    for i, url in enumerate(urls):
        vid = get_video_id(url)
        if vid and vid not in done_ids and vid not in no_panel_ids and vid not in failed_ids:
            remaining.append((i, url, vid))
  
    print(f"Total: {len(urls)}, Remaining: {len(remaining)}", flush=True)
    print("=" * 60, flush=True)
  
    success = no_panel = failed = 0
  
    for idx, (orig_idx, url, vid) in enumerate(remaining):
        print(f"\n[{idx+1}/{len(remaining)}] {vid}", flush=True)
      
        try:
            result = await extract_video(cdp, vid)
          
            if result["status"] == "success":
                transcript = result["transcript"]
                title = result["title"]
                safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:50]
              
                # Save transcript
                filepath = OUTPUT_DIR / f"{safe}_{vid}_engagement.txt"
                with open(filepath, 'w') as f:
                    f.write(f"# {title}\n# {vid}\n# Source: YouTube Engagement Panel (In this video)\n\n{transcript}")
              
                words = len(transcript.split())
                print(f"  OK {words} words ({len(transcript)} chars)", flush=True)
              
                # Save AI summary if present
                ai = result.get("ai_summary", "")
                if ai and len(ai) > 50:
                    ai_path = OUTPUT_DIR / f"{safe}_{vid}_ai_summary.txt"
                    with open(ai_path, 'w') as f:
                        f.write(f"# {title}\n# {vid}\n# AI Summary (from YouTube)\n\n{ai}")
                    print(f"  AI summary: {len(ai)} chars", flush=True)
              
                # Save full transcript if present
                full = result.get("full_transcript", "")
                if full and len(full) > 100:
                    full_path = OUTPUT_DIR / f"{safe}_{vid}_full_transcript.txt"
                    with open(full_path, 'w') as f:
                        f.write(f"# {title}\n# {vid}\n# Full Auto-Generated Transcript\n\n{full}")
                    print(f"  Full transcript: {len(full)} chars", flush=True)
              
                # Save chapters if present
                chapters = result.get("chapters", "")
                if chapters and chapters != "[]":
                    ch_path = OUTPUT_DIR / f"{safe}_{vid}_chapters.txt"
                    with open(ch_path, 'w') as f:
                        f.write(f"# {title}\n# {vid}\n# Video Chapters\n\n{chapters}")
                    print(f"  Chapters saved", flush=True)
              
                # Save metadata if present
                metadata = result.get("metadata", {})
                if isinstance(metadata, dict) and metadata and any(metadata.values()):
                    meta_path = OUTPUT_DIR / f"{safe}_{vid}_metadata.txt"
                    with open(meta_path, 'w') as f:
                        f.write(f"# {title}\n# {vid}\n# Video Metadata\n\n")
                        for k, v in metadata.items():
                            if v:
                                f.write(f"{k}: {v}\n")
                    print(f"  Metadata saved", flush=True)
              
                # Save description
                desc = result.get("description", "")
                if desc and len(desc) > 100:
                    desc_path = OUTPUT_DIR / f"{safe}_{vid}_description.txt"
                    with open(desc_path, 'w') as f:
                        f.write(f"# {title}\n# {vid}\n# Video Description\n\n{desc}")
              
                progress["done"].append({
                    "video_id": vid,
                    "title": title,
                    "words": words,
                    "source": "engagement_panel"
                })
                success += 1
              
            elif result["status"] == "no_panel":
                print(f"  No engagement panel", flush=True)
                progress["no_panel"].append({"video_id": vid, "url": url})
                no_panel += 1
              
            else:
                print(f"  FAIL: {result['status']}", flush=True)
                progress["failed"].append({"video_id": vid, "url": url, "error": result["status"]})
                failed += 1
              
        except Exception as e:
            print(f"  EXCEPTION: {str(e)[:80]}", flush=True)
            progress["failed"].append({"video_id": vid, "url": url, "error": str(e)[:100]})
            failed += 1
      
        # Save progress every 5 videos
        if (idx + 1) % 5 == 0:
            save_progress(progress)
            print(f"\n--- Progress: {success} ok, {no_panel} no panel, {failed} failed ---\n", flush=True)
  
    save_progress(progress)
    await cdp.close()
  
    print(f"\n{'='*60}")
    print(f"COMPLETE: {success} transcripts, {no_panel} no panel, {failed} failed")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(main())