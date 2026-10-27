#!/usr/bin/env python3
"""
run_absorber.py - Orchestrator for CDP + Whisper absorbing
- If Chrome CDP available → use C11 absorber (fast)
- If not → use faster_whisper fallback (CPU)
- Resumes from progress files
"""
import subprocess, json, re, os, sys, time, signal

VIDEO_FILE = "/home/wubu/seymour-project/absorption/data/videos_to_process.txt"
DONE_FILE = "/home/wubu/seymour-project/absorption/data/videos_already_done.txt"
OUTPUT_DIR = "/home/wubu/seymour-project/whiteboard/seymour-pipe/captions"
CDP_CAT = "/home/wubu/seymour-project/absorptio./engine/absorption_c11"

def get_video_id(url):
    m = re.search(r'[?&]v=([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else None

def load_video_list():
    """Load video IDs to process."""
    if not os.path.exists(VIDEO_FILE):
        print(f"[ERROR] {VIDEO_FILE} not found")
        return []
    with open(VIDEO_FILE) as f:
        ids = [line.strip() for line in f if line.strip()]
    return ids

def load_done_ids():
    """Load IDs already processed (skip these)."""
    done = set()
    # Load from CDP progress
    progress_file = os.path.join(OUTPUT_DIR, "browser_extract_progress.json")
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            prog = json.load(f)
        for item in prog.get('done', []):
            if isinstance(item, dict):
                done.add(item.get('video_id', ''))
    # Load from our done file
    if os.path.exists(DONE_FILE):
        with open(DONE_FILE) as f:
            for line in f:
                done.add(line.strip())
    return done

def check_chrome():
    """Check if Chrome CDP is available."""
    result = subprocess.run(
        ["ss", "-tlnp"], capture_output=True, text=True
    )
    for line in result.stdout.split('\n'):
        if 'chrome' in line.lower():
            # Extract port
            m = re.search(r':(\d+)', line)
            if m:
                return m.group(1)
    return None

def run_cdp_absorber(video_ids):
    """Run the C11 C absorber."""
    if not os.path.exists(CDP_CAT):
        print("[ERROR] absorption_c11 not built. Run: make all")
        return {}
    
    batch_file = "/tmp/absorber_batch.txt"
    with open(batch_file, 'w') as f:
        f.write('\n'.join(video_ids) + '\n')
    
    print(f"[CDP] Processing {len(video_ids)} videos with C11 absorber...")
    start = time.time()
    
    with open(batch_file) as fin:
        result = subprocess.run(
            [CDP_CAT],
            stdin=fin,
            capture_output=True,
            text=True,
            timeout=600,
        )
    
    elapsed = time.time() - start
    print(f"[CDP] Completed in {elapsed:.0f}s ({len(video_ids)/elapsed*60:.0f} videos/min)")
    
    # Parse results
    results = {}
    for line in result.stdout.strip().split('\n'):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            results[r.get('video_id', '')] = r
        except json.JSONDecodeError:
            pass
    
    if result.stderr:
        print(f"[CDP] stderr: {result.stderr[:200]}")
    
    return results

def run_whisper_fallback(video_ids):
    """Run faster_whisper fallback for videos without CDP."""
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("[WHISPER] faster_whisper not installed. Run: pip install faster-whisper")
        return {}
    
    print(f"[WHISPER] Processing {len(video_ids)} videos on CPU...")
    model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
    
    results = {}
    for vid in video_ids:
        print(f"  [{video_ids.index(vid)+1}/{len(video_ids)}] {vid}")
        
        # Download audio
        import yt_dlp
        wav_path = f"/tmp/{vid}.wav"
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '16',
            }],
            'outtmpl': wav_path.replace('.wav', '.%(ext)s'),
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={vid}"])
            
            if not os.path.exists(wav_path):
                print(f"    ❌ Download failed")
                results[vid] = {"status": "failed", "error": "download"}  # type: ignore
                continue
            
            segments, _ = model.transcribe(wav_path, beam_size=5, vad_filter=True)
            text_parts = [s.text for s in segments]
            text = '\n'.join(text_parts)
            
            if text.strip():
                # Save
                safe_name = re.sub(r'[^\w\s-]', '', vid)[:50]
                out_path = os.path.join(OUTPUT_DIR, f"WHISPER_{safe_name}_{vid}_transcript.txt")
                with open(out_path, 'w') as f:
                    f.write(f"# {vid}\n# Whisper fallback (tiny.en)\n\n{text}\n")
                results[vid] = {"status": "ok", "words": len(text.split())}
                print(f"    ✅ {len(text.split())} words")
            else:
                results[vid] = {"status": "empty", "error": "no text"}
                print(f"    ⚠️ Empty transcription")
            
            # Cleanup
            os.remove(wav_path)
            
        except Exception as e:
            results[vid] = {"status": "failed", "error": str(e)[:80]}
            print(f"    ❌ {str(e)[:80]}")
    
    return results

def save_results(results):
    """Save results to progress tracking."""
    progress_file = os.path.join(OUTPUT_DIR, "batch_results.json")
    
    # Merge with existing
    if os.path.exists(progress_file):
        with open(progress_file) as f:
            existing = json.load(f)
    else:
        existing = {}
    
    existing.update(results)
    
    with open(progress_file, 'w') as f:
        json.dump(existing, f, indent=2)
    
    # Update done file
    with open(DONE_FILE, 'a') as f:
        for vid, r in results.items():
            if r.get('status') in ('ok', 'no_panel', 'empty'):
                f.write(vid + '\n')

def main():
    done_ids = load_done_ids()
    all_ids = load_video_list()
    
    if not all_ids:
        print("[DONE] No videos to process")
        return
    
    # Filter out already-done
    todo = [v for v in all_ids if v not in done_ids]
    print(f"[Status] Total: {len(all_ids)}, Done: {len(done_ids)}, Todo: {len(todo)}")
    
    if not todo:
        print("[DONE] All videos already processed!")
        return
    
    # Check Chrome availability
    chrome_port = check_chrome()
    
    if chrome_port:
        print(f"[Chrome] CDP available on port {chrome_port}")
        results = run_cdp_absorber(todo)
    else:
        print("[Chrome] CDP not available - using whisper fallback")
        results = run_whisper_fallback(todo)
    
    save_results(results)
    
    # Summary
    ok = sum(1 for r in results.values() if r.get('status') == 'ok')
    failed = sum(1 for r in results.values() if r.get('status') == 'failed')
    no_panel = sum(1 for r in results.values() if r.get('status') == 'no_panel')
    
    print(f"\n{'='*60}")
    print(f"Batch complete: {ok} ok, {no_panel} no_panel, {failed} failed")
    total_done = len(done_ids) + ok
    print(f"Total progress: {total_done}/468 ({total_done/468*100:.0f}%)")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
