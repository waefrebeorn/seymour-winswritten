#!/usr/bin/env python3
"""
Absorber Engine — YouTube CDP Transcript Extractor (C11)
Builds and runs the C absorber binary. Handles progress tracking in Python.
"""
import subprocess, json, os, sys, time

ABSORBER_BIN = "./engine/absorption_c11"
DATA_DIR = "./data/transcripts"
PROGRESS_FILE = os.path.join(DATA_DIR, "absorption_progress.json")

def ensure_dirs():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs("./data/failed", exist_ok=True)

def build():
    """Compile the C11 absorber engine."""
    cmd = [
        "gcc",
        "-std=gnu11",
        "-O3",
        "-march=native",
        "-ffast-math",
        "-funroll-loops",
        "-ftree-vectorize",
        "-Wall", "-Wextra",
        "-Wno-unused-parameter",
        "-Werror=implicit-function-declaration",
        "-D_GNU_SOURCE",
        "-I", "include",
        "-o", ABSORBER_BIN,
        "engine/absorber_main.c",
        "engine/cdp_client.c",
        "engine/http_raw.c",
        "engine/video_store.c",
        "-lpthread",
    ]
    print(f"[build] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[build ERROR]\n{result.stderr}")
        sys.exit(1)
    print(f"[build OK] {ABSORBER_BIN}")

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": [], "no_panel": [], "failed": [], "whisper_needed": []}

def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)

def run_batch(video_ids):
    """Run the C absorber on a batch of video IDs."""
    done = load_progress()
    todo = [v for v in video_ids if v not in done["done"] and v not in done["no_panel"]]
    print(f"[run] {len(todo)} to process, {len(done['done'])} already done")
    
    if not todo:
        print("[run] Nothing to do.")
        return done
    
    # Feed video IDs via stdin to the C binary
    batch = "\n".join(todo) + "\n"
    
    start = time.time()
    result = subprocess.run(
        [ABSORBER_BIN],
        input=batch,
        capture_output=True,
        text=True,
        timeout=600,  # 10 min max per batch
    )
    elapsed = time.time() - start
    
    if result.returncode != 0:
        print(f"[run ERROR] exit={result.returncode}\n{result.stderr[:500]}")
        # Mark all as failed
        for vid in todo:
            done["failed"].append({"video_id": vid, "error": "crash", "ts": time.time()})
    else:
        # Parse the C output (one JSON line per result)
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                vid = r.get("video_id", "")
                status = r.get("status", "unknown")
                if status == "ok":
                    done["done"].append(vid)
                elif status == "no_panel":
                    done["no_panel"].append(vid)
                elif status == "whisper":
                    done["whisper_needed"].append(vid)
                elif status == "empty":
                    done["failed"].append({"video_id": vid, "error": "empty", "ts": time.time()})
                else:
                    done["failed"].append({"video_id": vid, "error": status, "ts": time.time()})
            except json.JSONDecodeError:
                print(f"[parse ERROR] {line[:100]}")
    
    save_progress(done)
    print(f"[run] {len(done['done'])} done, {len(done['no_panel'])} no_panel, "
          f"{len(done['whisper_needed'])} need_whisper, {len(done['failed'])} failed, "
          f"{elapsed:.1f}s")
    return done

if __name__ == "__main__":
    ensure_dirs()
    build()
    
    # Read video IDs from stdin or file
    if not sys.stdin.isatty():
        ids = [l.strip() for l in sys.stdin if l.strip()]
    elif len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            ids = [l.strip() for l in f if l.strip()]
    else:
        print("Usage: python3 build_absorber.py [video_ids.txt]")
        print("       cat video_ids.txt | python3 build_absorber.py")
        sys.exit(1)
    
    run_batch(ids)