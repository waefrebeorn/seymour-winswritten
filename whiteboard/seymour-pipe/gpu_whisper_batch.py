#!/home/wubu/seymour-project/.venv/bin/python3
"""
GPU Whisper Batch v4 — NO skipping for long vids, OOM-proof
  - Uses soundfile chunked loading via librosa (ffmpeg subprocess)
  - Stereo → mono on the fly, no full-RAM allocation
  - 30-min chunks: load 30min, transcribe, load next 30min, repeat
  - Merges overlapping segments at boundaries
  - Resumes cleanly, tracks progress
"""
import subprocess, os, sys, json, time, argparse, io, math
from pathlib import Path
from datetime import datetime

MODEL     = "small.en"
DTYPE     = "float16"
DEVICE    = "cuda"
BEAM      = 5
VAD       = True
CHUNK_S   = 30 * 60  # 30-min chunks
OVERLAP_S = 10        # 10s overlap between chunks for seamless merge

BASE      = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
WHISPER   = BASE / "whisper_transcripts"
TIMESTAMPS = BASE / "whisper_timestamps"
AUDIO     = BASE / "audio"
PROGRESS  = BASE / "gpu_progress.json"
COOKIES   = BASE / "cookies.txt"
SKIP_LOG  = BASE / "gpu_skipped.json"

for d in [WHISPER, TIMESTAMPS, AUDIO]:
    d.mkdir(parents=True, exist_ok=True)

def load_progress():
    if PROGRESS.exists():
        try: return json.loads(PROGRESS.read_text())
        except: pass
    return {"done": [], "failed": []}

def save_progress(p):
    PROGRESS.write_text(json.dumps(p, indent=2) + "\n")

def load_skipped():
    if SKIP_LOG.exists():
        try: return set(json.loads(SKIP_LOG.read_text()))
        except: pass
    return set()

def save_skipped(s):
    SKIP_LOG.write_text(json.dumps(sorted(s), indent=2) + "\n")

def download(vid):
    path = AUDIO / f"{vid}.mp3"
    if path.exists() and path.stat().st_size > 10000:
        return path
    url = f"https://www.youtube.com/watch?v={vid}"
    cmd = ["yt-dlp", "--cookies", str(COOKIES), "--js-runtimes", "node:/usr/bin/node",
           "-x", "--audio-format", "mp3", "--audio-quality", "10",
           "--sleep-interval", "15", "--max-sleep-interval", "30",
           "--throttled-rate", "100K",
           "-o", str(AUDIO / f"{vid}.%(ext)s"), "--no-playlist", url,
           "--no-part", "--no-mtime", "--no-post-overwrites",
           "--retries", "5", "--fragment-retries", "5"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if r.returncode == 0 and path.exists():
            mb = path.stat().st_size / 1e6
            print(f"  DL {vid} ({mb:.1f}MB)")
            return path
        # Fallback: rate-limit safe with sleep
        time.sleep(10)
        r2 = subprocess.run(
            ["yt-dlp", "--cookies", str(COOKIES), "--sleep-interval", "15", "--max-sleep-interval", "30",
             "--throttled-rate", "100K",
             "-x", "--audio-format", "mp3",
             "-o", str(AUDIO / f"{vid}.%(ext)s"), "--no-playlist", url,
             "--retries", "5", "--fragment-retries", "5"],
            capture_output=True, text=True, timeout=14400
        )
        if r2.returncode == 0 and path.exists():
            mb = path.stat().st_size / 1e6
            print(f"  DL {vid} (fallback, {mb:.1f}MB)")
            return path
        err = r.stderr[-300:] if r.stderr else "no output"
        print(f"  DL FAIL {vid}: {err}")
        return None
    except Exception as e:
        print(f"  DL ERR {vid}: {e}")
        return None

def load_audio_duration(audio_path):
    """Get audio duration without loading into memory."""
    try:
        import soundfile as sf
        info = sf.info(str(audio_path))
        return info.duration, info.samplerate, info.channels
    except:
        # Fallback with ffprobe
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
             str(audio_path)],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0 and r.stdout.strip():
            return float(r.stdout.strip()), None, None
        return None, None, None

def load_chunk(audio_path, start_s, duration_s, target_sr=16000):
    """Load a chunk of audio starting at start_s for duration_s seconds."""
    import librosa
    # librosa loads with offset/duration — only decodes what's needed
    aud, sr = librosa.load(
        str(audio_path), sr=target_sr, mono=True,
        offset=start_s, duration=duration_s
    )
    return aud, sr

def merge_segments(all_segments, overlap_s=OVERLAP_S):
    """Merge adjacent segments, de-duplicating the overlap zone."""
    if not all_segments:
        return [], ""
    merged = []
    # Sort by start time
    sorted_segs = sorted(all_segments, key=lambda s: s["start"])
    merged.append(sorted_segs[0])
    for seg in sorted_segs[1:]:
        prev = merged[-1]
        # If this segment overlaps heavily with previous (within overlap window)
        if seg["start"] < prev["end"] + overlap_s:
            # Merge: extend end if later, keep text from both avoiding redundancy
            new_end = max(prev["end"], seg["end"])
            prev_text = prev["text"].strip()
            seg_text = seg["text"].strip()
            # Simple merge: if seg text isn't already contained in prev
            if seg_text.lower() not in prev_text.lower():
                # Find the overlapping part — take the longer end
                prev["text"] = prev_text + " " + seg_text
            prev["end"] = new_end
        else:
            merged.append(seg)
    text = " ".join(s["text"] for s in merged).strip()
    return merged, text

def transcribe(vid, audio_path):
    from faster_whisper import WhisperModel

    txt_path  = WHISPER / f"{vid}_whisper.txt"
    ts_path   = TIMESTAMPS / f"{vid}_segments.json"

    if txt_path.exists() and ts_path.exists():
        print(f"  Already done: {vid}")
        return True

    # Get duration without loading file into RAM
    duration, orig_sr, channels = load_audio_duration(audio_path)
    if duration is None:
        print(f"  CAN'T GET DURATION — skipping")
        return False

    # Convert to 16kHz mono sample count
    target_sr = 16000
    total_s = int(math.ceil(duration))
    mb = audio_path.stat().st_size / 1e6
    print(f"  {duration/60:.1f}min, {mb:.0f}MB audio", end="", flush=True)

    # For short audio (< CHUNK_S), load in one shot — simpler, faster
    if duration <= CHUNK_S:
        print(f" (single chunk)")
        import librosa
        try:
            aud, sr = librosa.load(str(audio_path), sr=target_sr, mono=True)
        except Exception as e:
            print(f"  AUDIO LOAD FAIL: {e}")
            return False
        print(f"  [{MODEL}] Transcribing...", end=" ", flush=True)
        try:
            m = WhisperModel(MODEL, device=DEVICE, compute_type=DTYPE)
        except Exception as e:
            print(f"MODEL LOAD FAIL: {e}")
            return False
        t0 = time.time()
        try:
            segs, info = m.transcribe(aud, beam_size=BEAM, vad_filter=VAD)
        except Exception as e:
            print(f"TRANSCRIBE FAIL: {e}")
            del m
            return False
        segments = []
        text_parts = []
        for seg in segs:
            text_parts.append(seg.text)
            segments.append({
                "start": round(seg.start, 2),
                "end":   round(seg.end, 2),
                "text":  seg.text.strip()
            })
        full_text = " ".join(text_parts).strip()
        elapsed = time.time() - t0
        rtfx = duration / elapsed if elapsed > 0 else 0
        print(f"{elapsed:.0f}s ({rtfx:.0f}x RTF, {len(segments)} segs)")
        del m
    else:
        # Long audio — process in chunks
        print(f" ({math.ceil(duration/CHUNK_S)} chunks of {CHUNK_S//60}min)")
        try:
            m = WhisperModel(MODEL, device=DEVICE, compute_type=DTYPE)
        except Exception as e:
            print(f"MODEL LOAD FAIL: {e}")
            return False

        all_segments = []
        chunk_start = 0
        chunk_num = 0
        total_chunks = math.ceil(duration / CHUNK_S)

        while chunk_start < duration:
            chunk_dur = min(CHUNK_S + OVERLAP_S, duration - chunk_start)
            print(f"  Chunk {chunk_num+1}/{total_chunks} ({chunk_start/60:.0f}min)...", end=" ", flush=True)

            try:
                aud, sr = load_chunk(audio_path, chunk_start, chunk_dur)
            except Exception as e:
                print(f"LOAD FAIL at {chunk_start}s: {e}")
                chunk_start += CHUNK_S
                chunk_num += 1
                continue

            t0 = time.time()
            try:
                segs, info = m.transcribe(aud, beam_size=BEAM, vad_filter=VAD)
            except Exception as e:
                print(f"TRANSCRIBE FAIL at {chunk_start}s: {e}")
                chunk_start += CHUNK_S
                chunk_num += 1
                continue

            seg_count = 0
            for seg in segs:
                # Shift timestamps by chunk offset
                adj_start = round(seg.start + chunk_start, 2)
                adj_end   = round(seg.end + chunk_start, 2)
                all_segments.append({
                    "start": adj_start,
                    "end":   adj_end,
                    "text":  seg.text.strip()
                })
                seg_count += 1

            elapsed = time.time() - t0
            print(f"{elapsed:.0f}s ({seg_count} segs)")
            chunk_start += CHUNK_S
            chunk_num += 1

        del m

        # Merge overlapping segments
        print(f"  Merging {len(all_segments)} segments...", end=" ", flush=True)
        merged_segs, full_text = merge_segments(all_segments)
        print(f"{len(merged_segs)} after merge")

        if not full_text:
            print(f"  WARNING: empty transcript for {vid}")
            return False

        segments = merged_segs
        elapsed_total = duration  # placeholder
        print(f"  Done: {len(full_text.split())} words")

    # Save transcript
    txt_path.write_text(full_text)
    # Save timestamps
    ts_data = {"video_id": vid, "duration_s": round(duration, 1),
               "model": MODEL, "segments": segments,
               "total_words": len(full_text.split()),
               "chunked": duration > CHUNK_S}
    ts_path.write_text(json.dumps(ts_data, indent=2))

    return True

def merge_video_lists(vids, prog):
    """Merge done/failed/skipped + C11 transcripts so we don't redo work."""
    done_set = set(prog.get("done", []))
    failed_set = set(prog.get("failed", []))
    skipped_set = load_skipped()

    # Load C11 transcripts
    c11_dir = Path("/home/wubu/seymour-project/absorption/data/transcripts")
    if c11_dir.exists():
        for f in c11_dir.iterdir():
            if f.suffix == ".txt":
                done_set.add(f.stem)

    # Load GPU whisper transcripts
    for f in WHISPER.iterdir():
        if f.name.endswith("_whisper.txt"):
            done_set.add(f.name.replace("_whisper.txt", ""))

    return [v for v in vids if v not in done_set and v not in failed_set and v not in skipped_set]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(BASE / "gpu_batch_input.txt"))
    parser.add_argument("--no-cleanup", action="store_true",
                       help="Keep audio files after transcribing (debug)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found")
        alt = BASE / "whisper_remaining_final.txt"
        if alt.exists(): print(f"  Try: {alt}")
        return

    with open(args.input) as f:
        raw_vids = [l.strip() for l in f if l.strip()]

    prog = load_progress()
    vids = merge_video_lists(raw_vids, prog)

    total_skipped_initial = len(raw_vids) - len(vids)
    skipped_set = load_skipped()

    print(f"══ GPU Whisper Batch v4 (Chunked, No-Skip) ══")
    print(f"  Model:     {MODEL}  RTX 4050")
    print(f"  Videos:    {len(raw_vids)} total → {len(vids)} remaining")
    print(f"  Pre-skip:  {total_skipped_initial} (already done/failed/skipped)")
    print(f"  Chunk:     {CHUNK_S//60}min + {OVERLAP_S}s overlap (no max duration)")
    print(f"  Cleanup:   {'NO' if args.no_cleanup else 'delete audio after'}")
    print(f"  Started:   {datetime.now():%H:%M}")
    print()

    # Initial cooldown to let any rate-limit cool off
    print("  Cooling off 60s before first download...", flush=True)
    time.sleep(60)

    done_set = set(prog.get("done", []))
    success = len(done_set)
    failed_count = len(prog.get("failed", []))

    for i, vid in enumerate(vids):
        if vid in done_set:
            continue

        print(f"[{i+1}/{len(vids)}] {vid}")

        # Download
        ap = download(vid)
        if not ap:
            prog["failed"].append(vid)
            failed_count += 1
            save_progress(prog)
            continue

        # Transcribe — OOM protected via chunked loading
        try:
            ok = transcribe(vid, ap)
            if ok:
                prog["done"].append(vid)
                done_set.add(vid)
                success += 1
            else:
                skipped_set.add(vid)
                save_skipped(skipped_set)
        except MemoryError as e:
            print(f"  OOM on {vid}: {e}")
            skipped_set.add(vid)
            save_skipped(skipped_set)
        except Exception as e:
            print(f"  ERROR: {e}")
            err_str = str(e)
            if "allocate" in err_str or "CUDA out of memory" in err_str:
                skipped_set.add(vid)
                save_skipped(skipped_set)
            else:
                prog["failed"].append(vid)
                failed_count += 1
                save_progress(prog)

        # Cleanup audio unless --no-cleanup
        if not args.no_cleanup and ap.exists():
            ap.unlink()
        save_progress(prog)

        total_finished = success + failed_count
        if total_finished % 5 == 0:
            eta_remaining = len(vids) - total_finished
            print(f"  → {success} ok, {failed_count} fail, {len(skipped_set)} skipped, {eta_remaining} left")

    print(f"\n══ COMPLETE ══")
    print(f"  OK: {success}  Fail: {failed_count}  Skipped: {len(skipped_set)}")
    print(f"  Total processed: {len(vids)}")
    print(f"  Transcripts: {WHISPER}")
    print(f"  Timestamps:  {TIMESTAMPS}")

if __name__ == "__main__":
    main()