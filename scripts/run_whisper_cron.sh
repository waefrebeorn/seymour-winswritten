#!/bin/bash
# run_whisper_cron.sh — Cron wrapper for whisper batch processing
# Runs the whisper batch on the clean queue.
# Idempotent: skips already-transcribed videos.

set -euo pipefail

PROJECT_ROOT="/home/wubu/seymour-project"
WHISPER_DIR="$PROJECT_ROOT/whiteboard/seymour-pipe"
LOG_DIR="$PROJECT_ROOT/logs"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Check if whisper is already running
if pgrep -f "run_whisper_batch.py.*whisper_new" > /dev/null 2>&1; then
    echo "[$TIMESTAMP] Whisper batch already running — skipping"
    exit 0
fi

# Check if queue is empty
QUEUE_FILE="$WHISPER_DIR/whisper_new.txt"
if [ ! -f "$QUEUE_FILE" ] || [ ! -s "$QUEUE_FILE" ]; then
    echo "[$TIMESTAMP] Queue empty — nothing to process"
    exit 0
fi

# Rebuild queue: remove videos that got transcribed since last run
python3 -c "
from pathlib import Path
wd = Path('$WHISPER_DIR')
queue = {l.strip() for l in (wd / 'whisper_new.txt').read_text().splitlines() if l.strip()}
done = set()
for f in wd.glob('whisper_transcripts/*_whisper.txt'):
    vid = f.stem.replace('_whisper', '')
    done.add(vid)
remaining = queue - done
if remaining:
    (wd / 'whisper_new.txt').write_text('\n'.join(sorted(remaining)) + '\n')
    print(f'Remaining: {len(remaining)} videos')
else:
    (wd / 'whisper_new.txt').unlink(missing_ok=True)
    print('All done — queue cleared')
"

# Process if queue still exists
if [ -s "$QUEUE_FILE" ]; then
    echo "[$TIMESTAMP] Starting whisper batch ($(wc -l < "$QUEUE_FILE") videos)"
    cd "$WHISPER_DIR"
    python3 run_whisper_batch.py --input whisper_new.txt >> "$LOG_DIR/whisper_cron.log" 2>&1
    echo "[$TIMESTAMP] Batch finished (exit: $?)"
fi