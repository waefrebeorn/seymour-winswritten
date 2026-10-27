#!/bin/bash
# refresh_status.sh — Updates STATUS.md with live counts
# Add to cron: */5 * * * * /home/wubu/seymour-project/refresh_status.sh

set -euo pipefail

PROJECT_ROOT="/home/wubu/seymour-project"
STATUS_FILE="$PROJECT_ROOT/STATUS.md"

# Counts
C11_COUNT=$(ls "$PROJECT_ROOT/absorber/data/transcripts"/*.txt 2>/dev/null | wc -l)
WHISPER_COUNT=$(ls "$PROJECT_ROOT/whiteboard/seymour-pipe/whisper_transcripts"/*.txt 2>/dev/null | wc -l)
ENGAGEMENT_COUNT=$(ls "$PROJECT_ROOT/whiteboard/seymour-pipe/captions"/*_engagement.txt 2>/dev/null | wc -l)
VIDEO_QUEUE=$(wc -l < "$PROJECT_ROOT/absorber/data/videos_to_process.txt" 2>/dev/null || echo 0)
WHISPERERP_QUEUE=$(wc -l < "$PROJECT_ROOT/whiteboard/seymour-pipe/whisper_remaining.txt" 2>/dev/null || echo 0)

# Service checks
CHROMIUM_40581=$(curl -s http://127.0.0.1:40581/json/list 2>/dev/null | jq -r 'length' 2>/dev/null || echo "down")
CHROMIUM_9222=$(curl -s http://127.0.0.1:9222/json/list 2>/dev/null | jq -r 'length' 2>/dev/null || echo "down")
WHISPER_PID=$(pgrep -f "run_whisper_batch.py" | head -1 || echo "none")
ABSORBER_PID=$(pgrep -f "absorption_c11" | head -1 || echo "none")

# Update STATUS.md in place (sed the count lines)
sed -i "s/| C11 transcripts | [0-9]* |/| C11 transcripts | $C11_COUNT |/" "$STATUS_FILE"
sed -i "s/| Whisper transcripts | [0-9]* |/| Whisper transcripts | $WHISPER_COUNT |/" "$STATUS_FILE"
sed -i "s/| Engagement panel | [0-9]* |/| Engagement panel | $ENGAGEMENT_COUNT |/" "$STATUS_FILE"
sed -i "s/| Video IDs queued | [0-9]* |/| Video IDs queued | $VIDEO_QUEUE |/" "$STATUS_FILE"
sed -i "s/| Chromium CDP (primary) | 40581 | .* | .* |/| Chromium CDP (primary) | 40581 | ${ABSORBER_PID:-—} | $([ "$CHROMIUM_40581" != "down" ] && echo "✅ Up ($CHROMIUM_40581 tabs)" || echo "❌ Down") |/" "$STATUS_FILE"
sed -i "s/| Chromium CDP (fallback) | 9222 | .* | .* |/| Chromium CDP (fallback) | 9222 | ${ABSORBER_PID:-—} | $([ "$CHROMIUM_9222" != "down" ] && echo "✅ Up ($CHROMIUM_9222 tabs)" || echo "❌ Down") |/" "$STATUS_FILE"
sed -i "s/| Whisper batch | — | [0-9]* | .* |/| Whisper batch | — | ${WHISPER_PID:-—} | $([ "$WHISPER_PID" != "none" ] && echo "🟢 Running" || echo "❌ Stopped") |/" "$STATUS_FILE"
sed -i "s/| C11 Absorber | — | .* | .* |/| C11 Absorber | — | ${ABSORBER_PID:-—} | $([ "$ABSORBER_PID" != "none" ] && echo "🟢 Running" || echo "❌ Stopped") |/" "$STATUS_FILE"
sed -i "1s/.*/Last Updated: $(date -u +"%Y-%m-%d %H:%M UTC") (auto-refreshed by cron)/" "$STATUS_FILE"

echo "[$(date)] Status refreshed: C11=$C11_COUNT Whisper=$WHISPER_COUNT CDP=$ENGAGEMENT_COUNT" >> "$PROJECT_ROOT/status_refresh.log"