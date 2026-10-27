#!/usr/bin/env python3
"""
Seymour Wins — DAILY CAPTURE DAEMON
====================================
Local HTTP bridge for the browser plugin. Receives a fact captured from the
browser (via the Seymour Wins capture extension) and writes it into the
correct calendar/YYYY/MM/DD.md, OR creates a new issue if none exists.

This is PATH 5 of the "one for every day" system: when you read a real
historical fact on the web, one click files it into the right day.

Endpoints:
  GET  /ping                       -> {"ok": true}
  POST /capture                    -> body json {year,month,day,title,theme,fact,overlap?}
                                     appends/creates calendar/YYYY/MM/DD.md
  GET  /audit?year=2020           -> {"missing": [...], "present": N}

Run:
  python3 daily_daemon.py --port 8770

CORS is open (localhost) so the browser extension can call it.
"""
import os, sys, json, argparse, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = "/home/wubu/seymour-project"
POND = f"{ROOT}/ponderables"
CAL = f"{POND}/calendar"


def write_capture(payload):
    y = int(payload.get("year", datetime.date.today().year))
    m = int(payload.get("month", datetime.date.today().month))
    d = int(payload.get("day", datetime.date.today().day))
    theme = (payload.get("theme") or "meme").strip().lower()
    fact = (payload.get("fact") or "").strip()
    title = (payload.get("title") or f"{theme.title()} Day").strip()
    overlap = (payload.get("overlap") or "").strip()
    if not fact:
        return {"ok": False, "error": "fact required"}
    path = f"{CAL}/{y:04d}/{m:02d}/{d:02d}.md"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = ""
    if os.path.exists(path):
        existing = open(path).read().strip() + "\n\n"
    block = f"""**TITLE:** {title}
**THEME:** {theme}
**FACT:** {fact}¹
"""
    if overlap:
        block += f"**OVERLAP:** {overlap}\n"
    block += f"\n_(Captured from browser via Seymour Wins capture extension.)_\n\n---\n¹ Source: browser capture.\n"
    with open(path, "w") as f:
        f.write(existing + block)
    return {"ok": True, "path": path}


def audit(year):
    dim = [0, 31, 29 if (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)) else 28,
           31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    missing = []
    present = 0
    for m in range(1, 13):
        for d in range(1, dim[m] + 1):
            p = f"{CAL}/{year:04d}/{m:02d}/{d:02d}.md"
            if os.path.exists(p):
                present += 1
            else:
                missing.append(f"{year:04d}-{m:02d}-{d:02d}")
    return {"present": present, "missing": missing}


class H(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/ping":
            self._json({"ok": True})
        elif self.path.startswith("/audit"):
            try:
                y = int(self.path.split("year=")[1].split("&")[0])
            except Exception:
                y = datetime.date.today().year
            self._json(audit(y))
        else:
            self._json({"ok": False, "error": "unknown"}, 404)

    def do_POST(self):
        if self.path != "/capture":
            self._json({"ok": False, "error": "unknown"}, 404)
            return
        try:
            ln = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(ln) or b"{}")
            self._json(write_capture(body))
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 500)

    def _json(self, obj, code=200):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8770)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), H)
    print(f"Seymour Wins daily daemon on http://127.0.0.1:{a.port}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        srv.shutdown()


if __name__ == "__main__":
    main()
