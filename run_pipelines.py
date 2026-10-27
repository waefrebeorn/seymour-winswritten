#!/usr/bin/env python3
"""
Legacy wrapper - redirects to seymour_unified.py
"""
import sys
import subprocess

# Map old args to new unified commands
args = sys.argv[1:]

if "--whisper" in args and "--clipart" in args:
    # Old: python3 run_pipelines.py --whisper --clipart 20 --wiki
    # New: seymour_unified.py whisper && seymour_unified.py clipart --batch 20 && seymour_unified.py wiki
    batch = 20
    if "--clipart" in args:
        idx = args.index("--clipart")
        if idx + 1 < len(args):
            try:
                batch = int(args[idx + 1])
            except:
                pass
    
    subprocess.run(["python3", "scripts/seymour_unified.py", "whisper"])
    subprocess.run(["python3", "scripts/seymour_unified.py", "clipart", "--batch", str(batch)])
    subprocess.run(["python3", "scripts/seymour_unified.py", "wiki"])
else:
    print("Usage: python3 run_pipelines.py --whisper --clipart N --wiki")
    print("This wrapper is deprecated. Use: python3 scripts/seymour_unified.py <cmd>")