#!/usr/bin/env python3
"""
Stream Whisper v5 — no-OOM, zero-hold streaming for ANY duration
  - Uses ffmpeg to stream audio in 10-min raw PCM chunks (no librosa, no full-load)
  - Loads WhisperModel ONCE at startup, reuses for all videos
  - Proper GPU memory cleanup between videos
  - Chunked output stitched into final transcript
"""
import subprocess, os, sys, json, time, argparse, math, shutil
from pathlib import Path
from datetime import datetime

# ─── Config ──────────────────────────────────────────────────────
CHUNK_SEC    = 600          # 10-minute chunks
MODEL        = "small.en"
DTYPE        = "float16"
DEVICE       = "cuda"
BEAM         = 5
VAD          = True
AUDIO_BITRATE = "16k"       # ~0.7 MB/min
MAX_FILE_MB  = 500

BASE         = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
WHISPER      = BASE / "whisper_transcripts"
TIMESTAMPS   = BASE / "whisper_timestamps"
CHUNKS_DIR   = BASE / "whisper_chunks"
AUDIO        = BASE / "audio"
PROGRESS     = BASE / "gpu_progress.json"
SKIP_LOG     = BASE / "gpu_skipped.json"
COOKIES      = BASE / "cookies.txt"
# ─────────────────────────────────────────────────────────────────

for d in [WHISPER, TIMESTAMPS, CHUNKS_DIR, AUDIO]:
    d.mkdir(parents=True, exist_ok=True)

def load_json(p, default=None):
    if p.exists():
        try: return json.loads(p.read_text())
        except: pass
    return default if default is not None else {}

def save_json(p, data):
    p.write_text(json.dumps(data, indent=2) + "\n")

def get_duration(vid):
    """Get video duration in seconds."""
    url = f"https://www.youtube.com/watch?v={vid}"
    try:
        r = subprocess.run(
            ["yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
             "--sleep-interval", "2", "--print", "duration", "--no-playlist", url],
            capture_output=True, text=True, timeout=60
        )
        if r.returncode == 0 and r.stdout.strip():
            return float(r.stdout.strip())
        r2 = subprocess.run(
            ["yt-dlp", "--cookies", str(COOKIES), "--sleep-interval", "2",
             "-s", "--print", "duration", "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if r2.returncode == 0 and r2.stdout.strip():
            return float(r2.stdout.strip())
        return None
    except:
        return None

def download_low_bw(vid):
    """Download audio at low bitrate — small files even for long streams."""
    path = AUDIO / f"{vid}.mp3"
    if path.exists() and path.stat().st_size > 5000:
        return path

    url = f"https://www.youtube.com/watch?v={vid}"
    cmd = ["yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
           "--sleep-interval", "3", "--max-sleep-interval", "6",
           "-x", "--audio-format", "mp3",
           "--postprocessor-args", f"ffmpeg:-b:a {AUDIO_BITRATE}",
           "-o", str(AUDIO / f"{vid}.%(ext)s"), "--no-playlist", url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if r.returncode == 0 and path.exists():
            mb = path.stat().st_size / 1e6
            print(f"  DL {vid} ({mb:.1f}MB @ {AUDIO_BITRATE})")
            return path
        # Fallback without bitrate override
        r2 = subprocess.run(
            ["yt-dlp", "--cookies", str(COOKIES), "--sleep-interval", "3",
             "-x", "--audio-format", "mp3",
             "-o", str(AUDIO / f"{vid}.%(ext)s"), "--no-playlist", url],
            capture_output=True, text=True, timeout=14400
        )
        if r2.returncode == 0 and path.exists():
            mb = path.stat().st_size / 1e6
            print(f"  DL {vid} (fallback, {mb:.1f}MB)")
            return path
        print(f"  DL FAIL {vid}: {r.stderr[-200:]}")
        return None
    except Exception as e:
        print(f"  DL ERR {vid}: {e}")
        return None

def read_audio_pipe(vid, start_sec, duration_sec, sr=16000):
    """
    Use ffmpeg to read a slice of audio as raw PCM int16 samples.
    Returns bytes or None.
    Never loads more than (duration_sec * sr * 2) bytes into RAM ≈ a few MB.
    """
    audio_path = AUDIO / f"{vid}.mp3"
    if not audio_path.exists():
        return None

    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_sec),
        "-t", str(duration_sec),
        "-i", str(audio_path),
        "-f", "s16le",          # raw signed 16-bit PCM
        "-ac", "1",             # mono
        "-ar", str(sr),         # sample rate
        "-loglevel", "error",
        "pipe:1"
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=600)
        if r.returncode != 0:
            print(f"  ffmpeg err: {r.stderr.decode().strip()[:100]}")
            return None
        return r.stdout
    except subprocess.TimeoutExpired:
        print(f"  ffmpeg timeout at {start_sec}s")
        return None
    except Exception as e:
        print(f"  ffmpeg err: {e}")
        return None

def transcribe_video(vid, audio_path, model):
    """Transcribe a video using chunked streaming via ffmpeg pipes."""
    import numpy as np

    txt_path  = WHISPER / f"{vid}_whisper.txt"
    ts_path   = TIMESTAMPS / f"{vid}_segments.json"

    if txt_path.exists() and ts_path.exists():
        print(f"  Already done: {vid}")
        return True

    # Get audio duration with ffprobe
    dur_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "csv=p=0", str(audio_path)
    ]
    try:
        r = subprocess.run(dur_cmd, capture_output=True, text=True, timeout=30)
        dur_s = float(r.stdout.strip())
    except:
        # Fallback: estimate from file size
        mb = audio_path.stat().st_size / 1e6
        dur_s = mb * 60 / 0.7  # rough estimate at 16k
        print(f"  Duration: ~{dur_s/60:.0f}min (estimated)")
    else:
        print(f"  Duration: {dur_s/60:.1f}min ({int(dur_s//3600)}h{int((dur_s%3600)//60):02d}m)")

    if dur_s <= 0:
        print(f"  SKIP: zero duration")
        return False

    # Chunk
    num_chunks = max(1, math.ceil(dur_s / CHUNK_SEC))
    all_segments = []
    all_text_parts = []

    for ci in range(num_chunks):
        start_s = ci * CHUNK_SEC
        chunk_dur = min(CHUNK_SEC, dur_s - start_s)
        if chunk_dur <= 0:
            break

        print(f"  Chunk {ci+1}/{num_chunks} ({start_s/60:.1f}–{(start_s+chunk_dur)/60:.1f}min)...", end=" ", flush=True)

        raw = read_audio_pipe(vid, start_s, chunk_dur)
        if raw is None or len(raw) == 0:
            print("NO AUDIO")
            continue

        # Convert raw PCM bytes to float32 normalized array
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        try:
            segs, info = model.transcribe(samples, beam_size=BEAM, vad_filter=VAD)
            for seg in segs:
                abs_start = round(seg.start + start_s, 2)
                abs_end = round(seg.end + start_s, 2)
                all_text_parts.append(seg.text)
                all_segments.append({
                    "start": abs_start,
                    "end": abs_end,
                    "text": seg.text.strip()
                })
            print(f"{len(all_segments)} total segs")
        except Exception as e:
            print(f"TRANSCRIBE FAIL: {e}")
            return False

        # Force cleanup
        del samples, raw

    if not all_text_parts:
        print(f"  WARN: no segments for {vid}")
        return False

    full_text = " ".join(all_text_parts).strip()
    txt_path.write_text(full_text)

    ts_data = {
        "video_id": vid, "duration_s": round(dur_s, 1),
        "model": MODEL, "segments": all_segments,
        "total_words": len(full_text.split()),
        "chunks": num_chunks
    }
    ts_path.write_text(json.dumps(ts_data, indent=2))

    print(f"  ✓ {len(all_segments)} segs, {len(all_text_parts)} chunks → {len(full_text.split())} words")
    return True

def build_remaining_list(vids_path):
    """Build remaining list, deduping against all existing transcripts."""
    if not vids_path.exists():
        print(f"ERROR: {vids_path} not found")
        return [], 0

    vids = [l.strip() for l in vids_path.read_text().splitlines() if l.strip()]

    # Already transcribed
    done_union = set()

    # C11 transcripts
    c11_dir = Path("/home/wubu/seymour-project/absorption/data/transcripts")
    if c11_dir.exists():
        done_union.update(f.stem for f in c11_dir.iterdir() if f.suffix == ".txt")

    # GPU whisper transcripts
    done_union.update(f.name.replace("_whisper.txt", "")
                       for f in WHISPER.iterdir() if f.name.endswith("_whisper.txt"))

    # C11 already_done list
    ald = Path("/home/wubu/seymour-project/absorption/data/videos_already_done.txt")
    if ald.exists():
        done_union.update(l.strip() for l in ald.read_text().splitlines() if l.strip())

    # Our own progress
    prog = load_json(PROGRESS, {})
    done_union.update(prog.get("done", []))

    # Skipped
    sk = load_json(SKIP_LOG, [])
    if isinstance(sk, list):
        skipped = set(sk)
    else:
        skipped = set()

    remaining = [v for v in vids if v not in done_union and v not in skipped]
    return remaining, len(vids)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(BASE / "remaining_v4.txt"))
    args = parser.parse_args()

    remaining, total = build_remaining_list(Path(args.input))

    print(f"══ Stream Whisper v5 (ffmpeg-streamed, zero-hold) ══")
    print(f"  Model:      {MODEL}  RTX 4050")
    print(f"  Chunk:      {CHUNK_SEC}s ({CHUNK_SEC//60} min)")
    print(f"  Bitrate:    {AUDIO_BITRATE}")
    print(f"  Total:      {total}")
    print(f"  Remaining:  {len(remaining)}")
    print(f"  Started:    {datetime.now():%H:%M}")
    print()

    if not remaining:
        print("Nothing to do!")
        return

    # Load WhisperModel ONCE
    from faster_whisper import WhisperModel
    print(f"Loading model {MODEL} on {DEVICE} ({DTYPE})...", end=" ", flush=True)
    t0 = time.time()
    model = WhisperModel(MODEL, device=DEVICE, compute_type=DTYPE)
    print(f"done in {time.time()-t0:.0f}s")
    print()

    prog = load_json(PROGRESS, {"done": [], "failed": []})
    done_list = set(prog.get("done", []))
    success = len(done_list)
    failed = len(prog.get("failed", []))

    for i, vid in enumerate(remaining):
        if vid in done_list:
            continue

        print(f"[{i+1}/{len(remaining)}] https://youtube.com/watch?v={vid}")

        # Download at low bitrate
        ap = download_low_bw(vid)
        if not ap:
            prog["failed"].append(vid)
            failed += 1
            save_json(PROGRESS, prog)
            continue

        # File size safety check
        mb = ap.stat().st_size / 1e6
        if mb > MAX_FILE_MB:
            print(f"  SKIP ({mb:.0f}MB > {MAX_FILE_MB}MB limit)")
            sk = load_json(SKIP_LOG, [])
            if isinstance(sk, list):
                sk.append(vid)
                save_json(SKIP_LOG, list(set(sk)))
            ap.unlink()
            continue

        # Transcribe with zero-hold ffmpeg streaming
        try:
            ok = transcribe_video(vid, ap, model)
            if ok is True:
                prog["done"].append(vid)
                done_list.add(vid)
                success += 1
            elif ok is False:
                # Failed transcription — don't retry the OOM ones
                sk = load_json(SKIP_LOG, [])
                if isinstance(sk, list):
                    sk.append(vid)
                    save_json(SKIP_LOG, list(set(sk)))
                else:
                    prog["failed"].append(vid)
                    failed += 1
            else:
                prog["failed"].append(vid)
                failed += 1
        except MemoryError as e:
            print(f"  OOM: {e} → skip")
            sk = load_json(SKIP_LOG, [])
            if isinstance(sk, list):
                sk.append(vid)
                save_json(SKIP_LOG, list(set(sk)))
        except Exception as e:
            err = str(e)
            if any(w in err.lower() for w in ["allocate", "cuda out of memory", "memory"]):
                sk = load_json(SKIP_LOG, [])
                if isinstance(sk, list):
                    sk.append(vid)
                    save_json(SKIP_LOG, list(set(sk)))
                print(f"  OOM: {err}")
            else:
                prog["failed"].append(vid)
                failed += 1
                print(f"  ERROR: {err}")

        if ap.exists(): ap.unlink()
        save_json(PROGRESS, prog)

        finished = success + failed
        if finished % 3 == 0:
            print(f"  → {success} ok, {failed} fail, {len(remaining)-finished} left")

    del model
    print(f"\n══ COMPLETE ══ OK:{success} Fail:{failed} Left:{len(remaining)-success-failed}")

if __name__ == "__main__":
    main()