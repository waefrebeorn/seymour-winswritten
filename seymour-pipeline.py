#!/usr/bin/env python3
"""
seymour-pipeline.py — Full pipeline orchestrator.

Runs: absorb → index → tag → synthesize
All in one command. Idempotent, resumable, logged.
"""

import subprocess
import sys
import time
from pathlib import Path

BASE = Path("/home/wubu/seymour-project")
WHISPER_PIPE = BASE / "whiteboard/seymour-pipe"
ABSORPTION = BASE / "absorption"
SCRIPTS = BASE / "scripts"
LOGS = BASE / "logs"
LOGS.mkdir(exist_ok=True)

def run(cmd, cwd=None, log_file=None, timeout=None):
    """Run command with logging."""
    log_path = LOGS / log_file if log_file else None
    print(f"[PIPELINE] $ {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    
    if log_path:
        with open(log_path, "a") as log:
            log.write(f"\n=== {time.ctime()} ===\n")
            log.write(f"$ {' '.join(cmd) if isinstance(cmd, list) else cmd}\n\n")
            result = subprocess.run(cmd, cwd=cwd or BASE, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    else:
        result = subprocess.run(cmd, cwd=cwd or BASE, capture_output=True, text=True, timeout=timeout)
    
    if result.returncode != 0 and result.stdout:
        print(f"[PIPELINE] ERROR (code {result.returncode}): {result.stdout[-500:]}")
    return result.returncode == 0

def check_llama():
    """Check if llama-server is running and healthy."""
    import requests
    try:
        r = requests.get("http://localhost:18802/health", timeout=5)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except:
        return False

def start_llama():
    """Start llama-server if not running."""
    if check_llama():
        print("[PIPELINE] llama-server already running")
        return True
    
    print("[PIPELINE] Starting llama-server...")
    cmd = [
        "llama.cpp/build/bin/llama-server",
        "-m", str(BASE / "models/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf"),
        "--port", "18802",
        "--ctx-size", "2048",
        "--threads", "8",
        "--mlock",
        "--cache-ram", "0",
        "--n-predict", "200",
        "--timeout", "300"
    ]
    
    # Start in background
    log_file = LOGS / "llama_server.log"
    with open(log_file, "a") as log:
        proc = subprocess.Popen(cmd, cwd="/home/wubu", stdout=log, stderr=subprocess.STDOUT)
    
    # Wait for ready
    for i in range(60):
        time.sleep(2)
        if check_llama():
            print("[PIPELINE] llama-server ready")
            return True
        print(f"  waiting... ({i+1}/60)")
    
    print("[PIPELINE] ERROR: llama-server failed to start")
    return False

def run_whisper():
    """Run whisper pipeline for remaining videos."""
    print("[PIPELINE] Running whisper pipeline...")
    return run([
        "python3", "run_whisper_pipeline.py",
        "--input", "remaining_v4.txt"
    ], cwd=WHISPER_PIPE, log_file="whisper_pipeline.log", timeout=7200)

def run_index():
    """Rebuild unified index."""
    print("[PIPELINE] Building unified index...")
    return run([
        "python3", "build_pre_seymour_index.py"
    ], cwd=BASE, log_file="build_index.log", timeout=600)

def run_tagger():
    """Run topic tagger on untagged videos."""
    print("[PIPELINE] Running topic tagger...")
    # Check how many need tagging
    import json
    with open(BASE / "pre_seymour/index.json") as f:
        idx = json.load(f)
    untagged = sum(1 for v in idx.values() if not v.get("topics"))
    print(f"  {untagged} videos need tagging")
    
    if untagged == 0:
        print("[PIPELINE] All videos already tagged")
        return True
    
    return run([
        "python3", "topic_tagger_v2.py"
    ], cwd=BASE, log_file="topic_tagger.log", timeout=10800)

def run_synthesize(query=None):
    """Test synthesis with a query."""
    if not query:
        query = "godot"
    print(f"[PIPELINE] Testing synthesis: '{query}'")
    return run([
        "python3", "scripts/seymour_synthesize.py", query, "--limit", "2"
    ], cwd=BASE, log_file="synthesize.log", timeout=180)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seymour full pipeline")
    parser.add_argument("--skip-whisper", action="store_true", help="Skip whisper (already done)")
    parser.add_argument("--skip-index", action="store_true", help="Skip index rebuild")
    parser.add_argument("--skip-tag", action="store_true", help="Skip topic tagging")
    parser.add_argument("--test-synthesize", action="store_true", help="Test synthesis after")
    parser.add_argument("--query", default="godot", help="Query for synthesis test")
    args = parser.parse_args()
    
    print("═══ SEYMOUR PIPELINE ═══")
    print(f"Base: {BASE}")
    print(f"Logs: {LOGS}")
    
    # 1. Ensure llama-server
    if not start_llama():
        sys.exit(1)
    
    # 2. Whisper (CPU, long-running)
    if not args.skip_whisper:
        if not run_whisper():
            print("[PIPELINE] Whisper failed, continuing anyway...")
    
    # 3. Index (fast, idempotent)
    if not args.skip_index:
        if not run_index():
            print("[PIPELINE] Index build failed")
            sys.exit(1)
    
    # 4. Topic tagger (GPU/CPU, long-running)
    if not args.skip_tag:
        if not run_tagger():
            print("[PIPELINE] Tagger failed")
            sys.exit(1)
    
    # 5. Test synthesis
    if args.test_synthesize:
        run_synthesize(args.query)
    
    print("\n═══ PIPELINE COMPLETE ═══")

if __name__ == "__main__":
    main()