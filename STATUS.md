Last Updated: 2026-07-01 13:51 UTC (auto-refreshed by cron)

**Last Updated:** `date -u +"%Y-%m-%d %H:%M UTC"` (auto-refreshed by cron)

---

## 🎬 Pipeline Overview

| Stage | Tool | Input | Output | Status |
|-------|------|-------|--------|--------|
| 1. Video Discovery | Manual / API | Channel/playlist | `video_ids.txt` | ✅ Done (676 IDs) |
| 2. CDP Extraction | `browser_cdp_extract.py` | YouTube pages | `captions/*_engagement.txt` | ⏸️ Needs Chromium |
| 3. C11 Absorber | `absorption_c11` | Video IDs | `data/transcripts/*.txt` | ⏸️ Process died |
| 4. Whisper Fallback | `run_whisper_batch.py` | `whisper_videos.txt` | `whisper_transcripts/*.txt` | 🟢 Running (56/205) |
| 5. Wiki Ingestion | `seymour-wiki` skill | Transcripts | Wiki entries | ⏸️ Pending |

---

## 📊 Live Counts (Auto-Updated)

```bash
# Run this to refresh counts:
# cd /home/wubu/seymour-project && ./refresh_status.sh
```

| Metric | Count | Location |
|--------|-------|----------|
| Video IDs queued | 676 | `absorber/data/videos_to_process.txt` |
| C11 transcripts | 94 | `absorber/data/transcripts/` |
| Engagement panel | 264 | `whiteboard/seymour-pipe/captions/*_engagement.txt` |
| Whisper transcripts | 53 | `whiteboard/seymour-pipe/whisper_transcripts/` |
| Wiki entries (Vol 1) | 114 | `seymour-project/ponderables/` |

---

## 🔧 Service Status

| Service | Port | PID | Health |
|---------|------|-----|--------|
| Chromium CDP (primary) | 40581 | none | ❌ Down |
| Chromium CDP (fallback) | 9222 | none | ❌ Down |
| Whisper batch | — | 2085 | 🟢 Running |
| C11 Absorber | — | none | ❌ Stopped |

---

## 🚀 One-Command Restart Stack

```bash
# Start everything from clean state
cd /home/wubu/seymour-project && ./start_all.sh
```

**`start_all.sh` does:**
1. Launch Chromium on :40581 (headless, CDP enabled)
2. Wait for CDP readiness
3. Resume C11 absorber from `videos_to_process.txt` (skips done)
4. Resume Whisper from `whisper_remaining.txt` (skips done)
5. Start CDP extractor for remaining videos
6. Write updated `STATUS.md` every 5 min via cron

---

## 📁 Key Files to Monitor

| File | Purpose |
|------|---------|
| `absorber/data/videos_to_process.txt` | Master queue (676 IDs) |
| `absorber/data/videos_already_done.txt` | Skip list for C11 |
| `whiteboard/seymour-pipe/whisper_remaining.txt` | Skip list for Whisper |
| `whiteboard/seymour-pipe/captions/browser_extract_progress.json` | CDP progress |
| `absorber/data/transcripts/` | C11 output (JSON per video) |
| `whiteboard/seymour-pipe/whisper_transcripts/` | Whisper output (txt per video) |
| `whiteboard/seymour-pipe/captions/*_engagement.txt` | CDP output |

---

## 🛠️ Quick Commands

```bash
# Refresh this dashboard
./refresh_status.sh

# View Whisper progress (tail -f)
tail -f /home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_batch.log

# View C11 absorber progress
tail -f /home/wubu/seymour-project/absorber/absorber.log

# Check CDP browser
curl -s http://127.0.0.1:40581/json/list | jq length

# Count transcripts by type
ls absorber/data/transcripts/*.txt | wc -l     # C11
ls whiteboard/seymour-pipe/whisper_transcripts/*.txt | wc -l  # Whisper
ls whiteboard/seymour-pipe/captions/*_engagement.txt | wc -l  # CDP
```