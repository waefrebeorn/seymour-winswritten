#!/usr/bin/env python3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import os

OUTPUT = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
OUTPUT.mkdir(parents=True, exist_ok=True)

class H(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(n)
        if self.path == '/save':
            try:
                d = json.loads(body)
                vid = d.get('videoId','?')
                title = d.get('title','untitled')
                text = d.get('text','')
                safe = "".join(c for c in title if c.isalnum() or c in " _-").strip()[:50]
                p = OUTPUT / f"{safe}_{vid}_engagement.txt"
                with open(p,'w') as f:
                    f.write(f"# {title}\n# {vid}\n# Source: YouTube Engagement Panel\n\n{text}")
                self.send_response(200)
                self.end_headers()
                resp = {"ok":True,"words":len(text.split()),"chars":len(text)}
                self.wfile.write(json.dumps(resp).encode())
                print("SAVED {} ({} words)".format(p.name, resp['words']))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(str(e).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self,*a): pass

print("Receiver on 18768")
HTTPServer(('0.0.0.0',18768),H).serve_forever()
