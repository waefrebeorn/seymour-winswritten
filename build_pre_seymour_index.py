#!/usr/bin/env python3
"""
build_pre_seymour_index.py — Build unified master index of all Pre-Seymour content.

Merges C11 + Whisper transcripts, fetches metadata, outputs queryable index.
"""
import json, subprocess, sys, time
from pathlib import Path
from datetime import datetime

# ─── Paths ──────────────────────────────────────────────────────────
BASE         = Path("/home/wubu/seymour-project")
SEYMOUR_PIPE = BASE / "whiteboard/seymour-pipe"
ABSORPTION   = BASE / "absorption"

C11_DIR      = ABSORPTION / "data/transcripts"
WHISPER_DIR  = SEYMOUR_PIPE / "whisper_transcripts"

OUT_DIR      = BASE / "pre_seymour"
OUT_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE   = OUT_DIR / "index.json"
TIMELINE_FILE = OUT_DIR / "timeline.md"
ERAS_DIR     = OUT_DIR / "eras"
ERAS_DIR.mkdir(parents=True, exist_ok=True)

# ─── Helpers ────────────────────────────────────────────────────────

def get_video_metadata(vid):
    """Fetch title, upload_date, duration via yt-dlp (fast metadata only)."""
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        r = subprocess.run([
            "yt-dlp", "--cookies", str(SEYMOUR_PIPE / "cookies.txt"),
            "--sleep-interval", "2",
            "--print", "%(title)s",
            "--print", "%(upload_date)s",
            "--print", "%(duration)s",
            "--no-playlist", url
        ], capture_output=True, text=True, timeout=30)
        if r.returncode == 0:
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 3:
                return {
                    "title": lines[0][:200],
                    "upload_date": lines[1],
                    "duration_sec": int(lines[2])
                }
    except Exception:
        pass
    return None

def read_transcript(path):
    """Read transcript, return (text, word_count)."""
    try:
        text = path.read_text()
        return text, len(text.split())
    except Exception:
        return "", 0

def format_date(upload_date):
    """YYYYMMDD → YYYY-MM-DD"""
    if len(upload_date) == 8:
        return f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    return upload_date

def format_duration(sec):
    if sec >= 3600:
        return f"{sec//3600}h{(sec%3600)//60:02d}m"
    return f"{sec//60}m{sec%60:02d}s"

# ─── Build Index ────────────────────────────────────────────────────

def build_index():
    print("══ Pre-Seymour Index Builder ══")
    
    # 1. Collect all transcript files
    c11_files = {f.stem: f for f in C11_DIR.glob("*.txt") if f.stat().st_size > 10}
    whisper_files = {f.stem.replace("_whisper", ""): f for f in WHISPER_DIR.glob("*_whisper.txt") if f.stat().st_size > 10}
    
    all_vids = set(c11_files.keys()) | set(whisper_files.keys())
    print(f"C11 transcripts: {len(c11_files)}")
    print(f"Whisper transcripts: {len(whisper_files)}")
    print(f"Unique videos: {len(all_vids)}")
    
    # 2. Load existing index if present (for resume)
    existing = {}
    if INDEX_FILE.exists():
        try:
            existing = json.loads(INDEX_FILE.read_text())
            print(f"Resuming from {len(existing)} existing entries")
        except:
            pass
    
    # 3. Build entries
    index = {}
    to_fetch = []
    
    for vid in sorted(all_vids):
        if vid in existing:
            index[vid] = existing[vid]
            continue
        
        # Determine best source
        has_c11 = vid in c11_files
        has_whisper = vid in whisper_files
        
        if has_c11 and has_whisper:
            # Prefer C11 (YouTube engagement panel is cleaner)
            source = "c11"
            txt, wc = read_transcript(c11_files[vid])
            transcript_path = str(c11_files[vid])
        elif has_c11:
            source = "c11"
            txt, wc = read_transcript(c11_files[vid])
            transcript_path = str(c11_files[vid])
        else:
            source = "whisper"
            txt, wc = read_transcript(whisper_files[vid])
            transcript_path = str(whisper_files[vid])
        
        to_fetch.append((vid, source, txt, wc, transcript_path))
    
    # 4. Fetch metadata for missing entries (batched)
    print(f"Fetching metadata for {len(to_fetch)} new entries...")
    
    for i, (vid, source, txt, wc, transcript_path) in enumerate(to_fetch):
        meta = get_video_metadata(vid)
        if meta:
            upload_dt = format_date(meta["upload_date"])
        else:
            upload_dt = "unknown"
            meta = {"title": vid, "duration_sec": 0}
        
        entry = {
            "video_id": vid,
            "title": meta.get("title", vid),
            "upload_date": upload_dt,
            "duration_sec": meta.get("duration_sec", 0),
            "duration_fmt": format_duration(meta.get("duration_sec", 0)),
            "source": source,
            "word_count": wc,
            "has_transcript": wc > 0,
            "transcript_chars": len(txt),
            "transcript_path": transcript_path,
        }
        index[vid] = entry
        
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(to_fetch)}...")
            # Save progress
            INDEX_FILE.write_text(json.dumps(index, indent=2))
    
    # 5. Final save
    INDEX_FILE.write_text(json.dumps(index, indent=2))
    print(f"✓ Index saved: {INDEX_FILE} ({len(index)} videos)")
    
    return index

# ─── Timeline & Eras ────────────────────────────────────────────────

def build_timeline(index):
    """Generate chronological timeline markdown."""
    # Sort by upload_date
    dated = [(v, e) for v, e in index.items() if e["upload_date"] != "unknown"]
    dated.sort(key=lambda x: x[1]["upload_date"])
    
    lines = ["# Pre-Seymour Timeline\n", f"*Generated: {datetime.now():%Y-%m-%d %H:%M}*\n",
             f"*Total: {len(index)} videos, {sum(e['word_count'] for e in index.values()):,} words*\n"]
    
    current_year = None
    for vid, e in dated:
        year = e["upload_date"][:4]
        if year != current_year:
            current_year = year
            lines.append(f"\n## {year}\n")
        
        date = e["upload_date"]
        title = e["title"][:80]
        dur = e["duration_fmt"]
        wc = f"{e['word_count']:,}"
        src = e["source"]
        lines.append(f"- **{date}** | {dur} | {wc}w | {src} | [{title}](https://youtu.be/{vid})")
    
    TIMELINE_FILE.write_text("\n".join(lines))
    print(f"✓ Timeline: {TIMELINE_FILE}")

def build_eras(index):
    """Split into era files."""
    # Simple era buckets
    eras = {
        "2023-foundations": lambda d: d.startswith("2023"),
        "2024-deep-dives": lambda d: d.startswith("2024"),
        "2025-hiatus-prep": lambda d: d.startswith("2025"),
        "2026-absorption": lambda d: d.startswith("2026"),
    }
    
    for era_name, predicate in eras.items():
        era_vids = {v: e for v, e in index.items() 
                    if e["upload_date"] != "unknown" and predicate(e["upload_date"])}
        if era_vids:
            (ERAS_DIR / f"{era_name}.json").write_text(
                json.dumps(era_vids, indent=2)
            )
            print(f"  Era {era_name}: {len(era_vids)} videos")
    
    print(f"✓ Eras saved to {ERAS_DIR}")

# ─── Main ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    index = build_index()
    build_timeline(index)
    build_eras(index)
    print("\n✓ Pre-Seymour scaffolding complete")
    print(f"  Index:  {INDEX_FILE}")
    print(f"  Timeline: {TIMELINE_FILE}")
    print(f"  Eras:   {ERAS_DIR}/")