
import subprocess
import time
import os

video_ids_path = '/home/wubu/seymour-project/whiteboard/seymour-pipe/video_ids.txt'
output_path = '/home/wubu/seymour-project/whiteboard/seymour-pipe/absorber_results.jsonl'

with open(video_ids_path, 'r') as f:
    video_ids = f.read().strip()

print(f"Starting absorber for {len(video_ids.split(chr(10)))} videos...")
print(f"Output: {output_path}")

proc = subprocess.Popen(
    ['./engine/absorption_c11'],
    stdin=subprocess.PIPE,
    stdout=open(output_path, 'w'),
    stderr=subprocess.PIPE,
    text=True,
    cwd='/home/wubu/seymour-project/absorber'
)

# Write all video IDs
proc.stdin.write(video_ids)
proc.stdin.close()

# Monitor progress
start = time.time()
last_count = 0
while True:
    line = proc.stderr.readline()
    if not line and proc.poll() is not None:
        break
    if line:
        print(f"[STDERR] {line.strip()}")
        if 'processed' in line:
            try:
                count = int(line.split()[-1].replace('videos', ''))
                elapsed = time.time() - start
                rate = count / elapsed * 60 if elapsed > 0 else 0
                remaining = (len(video_ids.split(chr(10))) - count) / rate if rate > 0 else 0
                print(f"  Progress: {count}/{len(video_ids.split(chr(10)))} videos | {rate:.1f} videos/min | ETA: {remaining:.1f} min")
            except:
                pass

print(f"absorber finished with exit code: {proc.returncode}")
