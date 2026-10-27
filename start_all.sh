#!/bin/bash
# start_all.sh — Launch full Seymour pipeline stack
# Run once after reboot to bring everything up

set -euo pipefail

PROJECT_ROOT="/home/wubu/seymour-project"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

echo "[$(date)] Starting Seymour pipeline stack..." | tee -a "$LOG_DIR/startup.log"

# 1. Launch Chromium CDP on :40581 (headless)
echo "[$(date)] Launching Chromium on port 40581..." | tee -a "$LOG_DIR/startup.log"
/usr/bin/chromium-browser \
    --headless \
    --remote-debugging-port=40581 \
    --no-sandbox \
    --disable-gpu \
    --disable-dev-shm-usage \
    --remote-debugging-address=0.0.0.0 \
    --user-data-dir=/tmp/chrome-cdp-primary \
    > "$LOG_DIR/chromium_40581.log" 2>&1 &

CHROMIUM_PID=$!
echo $CHROMIUM_PID > "$LOG_DIR/chromium_40581.pid"
echo "[$(date)] Chromium PID: $CHROMIUM_PID" | tee -a "$LOG_DIR/startup.log"

# 2. Wait for CDP readiness
echo "[$(date)] Waiting for CDP endpoint..." | tee -a "$LOG_DIR/startup.log"
for i in {1..30}; do
    if curl -s http://127.0.0.1:40581/json/list >/dev/null 2>&1; then
        echo "[$(date)] CDP ready on :40581" | tee -a "$LOG_DIR/startup.log"
        break
    fi
    sleep 2
done

# 3. Resume C11 Absorber (background, with logging)
echo "[$(date)] Starting C11 absorber..." | tee -a "$LOG_DIR/startup.log"
cd "$PROJECT_ROOT/absorber"
cat data/videos_to_process.txt | ./engine/absorption_c11 >> "$LOG_DIR/absorber.log" 2>&1 &
ABSORBER_PID=$!
echo $ABSORBER_PID > "$LOG_DIR/absorber.pid"
echo "[$(date)] C11 Absorber PID: $ABSORBER_PID" | tee -a "$LOG_DIR/startup.log"

# 4. Resume Whisper Batch (already running, but ensure it's alive)
if ! pgrep -f "run_whisper_batch.py" >/dev/null; then
    echo "[$(date)] Restarting Whisper batch..." | tee -a "$LOG_DIR/startup.log"
    cd "$PROJECT_ROOT/whiteboard/seymour-pipe"
    python3 run_whisper_batch.py >> "$LOG_DIR/whisper_batch.log" 2>&1 &
    WHISPER_PID=$!
    echo $WHISPER_PID > "$LOG_DIR/whisper.pid"
    echo "[$(date)] Whisper PID: $WHISPER_PID" | tee -a "$LOG_DIR/startup.log"
else
    echo "[$(date)] Whisper already running" | tee -a "$LOG_DIR/startup.log"
fi

# 5. Start CDP Extractor for remaining videos (background)
echo "[$(date)] Starting CDP extractor..." | tee -a "$LOG_DIR/startup.log"
cd "$PROJECT_ROOT"
python3 scripts/browser_cdp_extract.py >> "$LOG_DIR/cdp_extract.log" 2>&1 &
CDP_PID=$!
echo $CDP_PID > "$LOG_DIR/cdp_extract.pid"
echo "[$(date)] CDP Extractor PID: $CDP_PID" | tee -a "$LOG_DIR/startup.log"

# 6. Install cron job for status refresh (every 5 min)
CRON_JOB="*/5 * * * * $PROJECT_ROOT/refresh_status.sh"
(crontab -l 2>/dev/null | grep -v "refresh_status.sh"; echo "$CRON_JOB") | crontab -
echo "[$(date)] Cron job installed for status refresh" | tee -a "$LOG_DIR/startup.log"

# 7. Initial status refresh
"$PROJECT_ROOT/refresh_status.sh"

echo "[$(date)] Stack startup complete. PIDs: Chromium=$CHROMIUM_PID Absorber=$ABSORBER_PID CDP=$CDP_PID" | tee -a "$LOG_DIR/startup.log"
echo "Monitor: tail -f $LOG_DIR/*.log"
echo "Status:  cat $PROJECT_ROOT/STATUS.md"