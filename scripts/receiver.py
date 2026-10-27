#!/usr/bin/env python3
"""
HTTP receiver for transcript data from browser.
Runs on port 18767. Browser sends POST /save with JSON body.
Saves to captions/ directory.
"""

import json
import os
import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class TranscriptReceiver(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        if self.path == '/save':
            try:
                data = json.loads(body)
                video_id = data.get('videoId', 'unknown')
                title = data.get('title', f'video_{video_id}')
                text = data.get('text', '')
                
                if not text:
                    self.send_json(400, {"error": "empty text"})
                    return
                
                safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:50]
                txt_path = OUTPUT_DIR / f"{safe}_{video_id}_engagement.txt"
                
                with open(txt_path, 'w') as f:
                    f.write(f"# {title}\n# {video_id}\n# Source: YouTube Engagement Panel\n# Saved: {datetime.now().isoformat()}\n\n{text}")
                
                self.send_json(200, {
                    "ok": True,
                    "chars": len(text),
                    "words": len(text.split()),
                    "file": str(txt_path)
                })
                print("OK {} ... | {} chars | {} words".format(safe[:40], len(text), len(text.split())))
                
            except Exception as e:
                self.send_json(500, {"error": str(e)})
                print("Error: {}".format(e))
        else:
            self.send_json(404, {"error": "not found"})
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        pass

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 18767
    server = HTTPServer(('127.0.0.1', port), TranscriptReceiver)
    print("Transcript receiver listening on http://127.0.0.1:{}".format(port))
    print("Ready to receive data from browser.")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.shutdown()

if __name__ == "__main__":
    main()
