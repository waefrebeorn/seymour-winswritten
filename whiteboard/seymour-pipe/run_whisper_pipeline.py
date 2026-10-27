#!/usr/bin/env python3
"""
run_whisper_pipeline.py — Final whisper fallback for remaining videos.

Strategy:
  - CPU-only using faster-whisper tiny.en (~75MB RAM)
  - Downloads audio via yt-dlp with --sleep-interval 3 (rate-limit safe)
  - 10-min chunked ffmpeg streaming (no full audio in RAM)
  - Saves to whisper_transcripts/{vid}_whisper.txt
  - Progress tracked in whisper_progress.json (atomic resume)
  - Self-healing: dedups against ALL existing transcript sources

Usage: python3 run_whisper_pipeline.py [--input remaining_v4.txt]
"""
import subprocess, sys, os, time, json, signal, argparse, math
from pathlib import Path
from datetime import datetime

# ─── Config ────────────────────────────────────────────────────────
BASE_DIR     = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
ABSORPTION   = Path("/home/wubu/seymour-project/absorption")
CHUNK_SEC    = 600               # 10-minute audio chunks
AUDIO_BITRATE = "16k"            # ~0.7 MB/min
MODEL_NAME   = "tiny.en"         # CPU-friendly, ~75MB
DEVICE       = "cpu"
COMPUTE_TYPE = "int8"
BEAM         = 5
VAD          = True
SLEEP_BETWEEN = 3                # rate-limit respect
YT_TIMEOUT   = 3600              # 1hr max per download

WHISPER_DIR  = BASE_DIR / "whisper_transcripts"
AUDIO_DIR    = BASE_DIR / "audio_whisper"
PROGRESS     = BASE_DIR / "whisper_progress.json"
COOKIES      = BASE_DIR / "cookies.txt"
LOG_FILE     = BASE_DIR / "whisper_pipeline.log"
# ────────────────────────────────────────────────────────────────────

g_stop = False

# ── Helpers ─────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_progress():
    if PROGRESS.exists():
        try:
            d = json.loads(PROGRESS.read_text())
            return set(d.get("done", [])), set(d.get("failed", []))
        except: pass
    return set(), set()


def save_progress(done_set, failed_set):
    d = {"done": sorted(done_set), "failed": sorted(failed_set),
         "updated": datetime.now().isoformat()}
    tmp = PROGRESS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=2) + "\n")
    tmp.rename(PROGRESS)


def get_remaining(vids):
    """Dedup against ALL existing transcript sources (whisper, C11, progress)."""
    done, failed = load_progress()

    # Existing whisper transcripts (non-empty)
    done.update(f.stem.replace("_whisper","")
                for f in WHISPER_DIR.glob("*_whisper.txt") if f.stat().st_size > 10)

    # C11 transcripts
    c11_dir = ABSORPTION / "data/transcripts"
    if c11_dir.exists():
        done.update(f.stem for f in c11_dir.glob("*.txt") if f.stat().st_size > 10)

    # C11 already_done list
    ald = ABSORPTION / "data/videos_already_done.txt"
    if ald.exists():
        done.update(l.strip() for l in ald.read_text().splitlines() if l.strip())

    return [v for v in vids if v not in done and v not in failed]


def get_duration(vid):
    """Get video duration via yt-dlp (fast metadata only)."""
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        r = subprocess.run(
            ["yt-dlp", "--cookies", str(COOKIES), "--sleep-interval", "2",
             "--print", "duration", "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0 and r.stdout.strip():
            return float(r.stdout.strip())
    except: pass
    return None


def download_audio(vid):
    """Download audio at low bitrate. Returns path or None."""
    path = AUDIO_DIR / f"{vid}.mp3"
    if path.exists() and path.stat().st_size > 5000:
        return path

    url = f"https://www.youtube.com/watch?v={vid}"
    cmd = [
        "yt-dlp", "--cookies", str(COOKIES),
        "--sleep-interval", "3", "--max-sleep-interval", "6",
        "-x", "--audio-format", "mp3",
        "--postprocessor-args", f"ffmpeg:-b:a {AUDIO_BITRATE}",
        "-o", str(AUDIO_DIR / f"{vid}.%(ext)s"),
        "--no-playlist", url
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=YT_TIMEOUT)
        if r.returncode == 0 and path.exists():
            mb = path.stat().st_size / 1e6
            log(f"  DL {vid} ({mb:.1f}MB)")
            return path
        log(f"  DL FAIL {vid}: {r.stderr[-120:]}")
        return None
    except Exception as e:
        log(f"  DL ERR {vid}: {e}")
        return None


def read_audio_chunk(vid, start_sec, duration_sec, sr=16000):
    """Read a slice of audio as raw PCM int16 using ffmpeg. Returns bytes or None."""
    import numpy as np
    audio_path = AUDIO_DIR / f"{vid}.mp3"
    if not audio_path.exists():
        return None

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-i", str(audio_path),
        "-f", "s16le",
        "-ac", "1",
        "-ar", str(sr),
        "-loglevel", "error",
        "pipe:1"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=300)
        if r.returncode != 0:
            return None
        return r.stdout
    except:
        return None


def transcribe_video(vid, model):
    """Transcribe a single video using chunked ffmpeg streaming."""
    txt_path = WHISPER_DIR / f"{vid}_whisper.txt"
    if txt_path.exists() and txt_path.stat().st_size > 10:
        return True

    audio_path = AUDIO_DIR / f"{vid}.mp3"
    if not audio_path.exists():
        return False

    # Get duration via ffprobe
    dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(audio_path)]
    try:
        r = subprocess.run(dur_cmd, capture_output=True, text=True, timeout=30)
        dur_s = float(r.stdout.strip())
    except:
        log(f"  SKIP {vid}: can't determine duration")
        return False

    if dur_s <= 0:
        return False

    import numpy as np
    num_chunks = max(1, math.ceil(dur_s / CHUNK_SEC))
    all_segments = []
    all_text = []

    for ci in range(num_chunks):
        start_s = ci * CHUNK_SEC
        chunk_dur = min(CHUNK_SEC, dur_s - start_s)
        if chunk_dur <= 0:
            break

        raw = read_audio_chunk(vid, start_s, chunk_dur)
        if raw is None or len(raw) < 16000:  # <1s audio
            continue

        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        try:
            segments, _ = model.transcribe(samples, beam_size=BEAM, vad_filter=VAD)
            for seg in segments:
                all_segments.append(seg)
                all_text.append(seg.text)
        except Exception as e:
            log(f"  CHUNK ERR {vid} ch{ci}: {str(e)[:60]}")
            continue

        del samples, raw

    if not all_text:
        return False

    full_text = " ".join(all_text).strip()
    txt_path.write_text(full_text)
    word_count = len(full_text.split())
    log(f"  ✓ {vid} ({dur_s/60:.0f}min, {num_chunks} chunks, {word_count} words)")
    return True


def signal_handler(sig, frame):
    global g_stop
    log(f"⚠ {signal.Signals(sig).name} received — finishing current video, saving progress...")
    g_stop = True


# ── Main ───────────────────────────────────────────────────────────

def main():
    global g_stop
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    WHISPER_DIR.mkdir(parents=True, exist_ok=True)
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default=str(BASE_DIR / "remaining_v4.txt"))
    parser.add_argument("--whisper-queue", "-w", default=str(BASE_DIR / "whisper_remaining.txt"))
    args = parser.parse_args()

    # Build video list from primary input + whisper queue (deduped)
    input_vids = []
    for p in [args.input, args.whisper_queue]:
        path = Path(p)
        if path.exists():
            input_vids.extend(l.strip() for l in path.read_text().splitlines() if l.strip())

    if not input_vids:
        log("ERROR: no videos found in input or whisper queue")
        return 1

    remaining = get_remaining(input_vids)
    total = len(remaining)

    log(f"══ Whisper Pipeline (CPU {MODEL_NAME}) ══")
    log(f"  Videos:   {total} remaining")
    log(f"  Model:    {MODEL_NAME} on {DEVICE} ({COMPUTE_TYPE})")
    log(f"  Chunk:    {CHUNK_SEC//60}min ffmpeg (no OOM)")
    log(f"  Rate:     {SLEEP_BETWEEN}s between downloads")
    log(f"  Started:  {datetime.now():%H:%M}")

    if not remaining:
        log("Nothing to do!")
        return 0

    # Load whisper model
    from faster_whisper import WhisperModel
    log("Loading model...")
    t0 = time.time()
    model = WhisperModel(MODEL_NAME, device=DEVICE, compute_type=COMPUTE_TYPE,
                         cpu_threads=4, num_workers=1)
    log(f"done in {time.time()-t0:.0f}s")

    done_set, failed_set = load_progress()

    for i, vid in enumerate(remaining):
        if g_stop:
            break

        log(f"[{i+1}/{total}] {vid}")

        # Download
        ap = download_audio(vid)
        if not ap:
            failed_set.add(vid)
            save_progress(done_set, failed_set)
            continue

        # File size check (keep whisper OOM-safe)
        mb = ap.stat().st_size / 1e6
        if mb > 500:
            log(f"  SKIP {vid}: {mb:.0f}MB > 500MB limit")
            ap.unlink()
            time.sleep(SLEEP_BETWEEN)
            continue

        # Transcribe
        ok = transcribe_video(vid, model)
        if ok:
            done_set.add(vid)
        else:
            failed_set.add(vid)

        # Cleanup audio
        if ap.exists():
            ap.unlink()

        # Save progress every video
        save_progress(done_set, failed_set)

        # Rate-limit
        if i < total - 1:
            time.sleep(SLEEP_BETWEEN)

        # Periodic status
        if (i+1) % 10 == 0:
            elapsed_h = (time.time() - t0) / 3600
            done_count = len(done_set)
            log(f"  → {done_count}/{total} done ({elapsed_h:.1f}h elapsed)")

    # Cleanup
    del model

    # Final report
    done_set, failed_set = load_progress()
    log(f"\n══ WHISPER PIPELINE COMPLETE ══")
    log(f"  Done:   {len(done_set)}")
    log(f"  Fail:   {len(failed_set)}")
    log(f"  Total:  {len(done_set) + len(failed_set)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())