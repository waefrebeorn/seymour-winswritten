#!/usr/bin/env python3
"""
filter_queue.py — Sift the remaining GPU batch queue for non-WuBu content.
Flags videos that are probably not the user speaking (commercials, music, shorts).
Output: filtered input file + skip list
"""
import subprocess, json, sys, re
from pathlib import Path

BASE = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
COOKIES = BASE / "cookies.txt"
INPUT = BASE / "gpu_batch_input.txt"
OUTPUT = BASE / "gpu_batch_input_filtered.txt"
FLAGS = BASE / "filtered_out.json"

# Titles that indicate non-WuBu content (case-insensitive substring match)
NON_WUBU_PATTERNS = [
    "education connection",
    "tv spot",
    "commercial",
    "dnsl safe haven",
    "(music video)",
    "rick astley",
    "never gonna give",
    # Channels/creators that aren't WuBu
    "caseoh",
    "alex jones",
]
# Flag any title that doesn't contain these (if it's short)
WUBU_INDICATORS = ["wubu", "wu-bu", "schedule", "death stranding", "tf2 giveaway"]

def is_wubu_content(title, duration_s):
    """Guess if this is content worth transcribing."""
    title_lower = title.lower()
    
    # Explicit non-WuBu patterns
    for pat in NON_WUBU_PATTERNS:
        if pat in title_lower:
            return False, f"pattern: {pat}"
    
    # Very short videos (<15s) that aren't clearly WuBu
    if duration_s < 30 and not any(i in title_lower for i in WUBU_INDICATORS):
        return False, "very short, unknown content"
    
    return True, "ok"

def main():
    remaining = [l.strip() for l in INPUT.read_text().splitlines() if l.strip()]
    
    # Already done/skipped
    prog = json.loads((BASE/"gpu_progress.json").read_text()) if (BASE/"gpu_progress.json").exists() else {'done':[]}
    skipped = set(json.loads((BASE/"gpu_skipped.json").read_text())) if (BASE/"gpu_skipped.json").exists() else set()
    done = set(prog.get('done', []))
    gpu_done = set(f.stem.replace('_whisper','') for f in (BASE/"whisper_transcripts").glob('*_whisper.txt'))
    c11_done = set(f.stem for f in Path("/home/wubu/seymour-project/absorption/data/transcripts").glob('*.txt'))
    all_done = done | gpu_done | c11_done
    todo = [v for v in remaining if v not in all_done and v not in skipped]
    
    print(f"Scanning {len(todo)} remaining videos for relevance...")
    
    keep = []
    filtered = []
    errors = []
    
    for i, vid in enumerate(todo):
        try:
            r = subprocess.run(
                ["yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
                 "--print", "duration", "--print", "title",
                 "--no-playlist", "--ignore-errors", f"https://www.youtube.com/watch?v={vid}"],
                capture_output=True, text=True, timeout=20
            )
            lines = r.stdout.strip().split("\n")
            if len(lines) >= 2:
                dur = float(lines[0])
                title = lines[1]
                ok, reason = is_wubu_content(title, dur)
                if ok:
                    keep.append(vid)
                else:
                    filtered.append({"video_id": vid, "duration_s": dur, "title": title, "reason": reason})
                    print(f"  FILTER: {vid} ({dur:.0f}s) — {title[:60]}")
            else:
                keep.append(vid)  # can't determine, keep it
                errors.append(vid)
        except Exception as e:
            keep.append(vid)  # error, keep it safe
            errors.append(vid)
        
        if (i+1) % 25 == 0:
            print(f"  ... {i+1}/{len(todo)}")
    
    # Write filtered input
    OUTPUT.write_text("\n".join(keep) + "\n")
    FLAGS.write_text(json.dumps({"filtered": filtered, "errors": errors, "kept": len(keep)}, indent=2))
    
    print(f"\n═══ Filter complete ═══")
    print(f"  Kept:     {len(keep)}")
    print(f"  Filtered: {len(filtered)}")
    print(f"  Errors:   {len(errors)}")
    print(f"\n  Filtered list: {FLAGS}")
    print(f"  New input:    {OUTPUT}")
    
    if filtered:
        print(f"\n  Filtered videos:")
        for f in filtered:
            print(f"    {f['video_id']} ({f['duration_s']:.0f}s) — {f['reason']} — {f['title'][:60]}")

if __name__ == "__main__":
    main()