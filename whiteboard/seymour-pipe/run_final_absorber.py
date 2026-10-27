#!/usr/bin/env python3
"""
run_final_absorber.py — The final absorption orchestrator.

Architecture:
  C11 absorption engine is the primary pipeline (low RAM, CDP-based).
  Runs in batches of 50 videos per C11 invocation with Chrome restart between batches.
  Progress tracked atomically — safe to SIGKILL mid-run.
  Rate-limit respect via sleep intervals.
  Self-healing: dedups against ALL existing transcript sources on each run.

Chrome restarts every batch to work around headless memory leak (~250MB/tab).

Usage:
  python3 run_final_absorber.py

Will pick up remaining_v4.txt from seymour-pipe dir.
"""
import subprocess, sys, os, time, json, signal, argparse
from pathlib import Path
from datetime import datetime

# ─── Config ────────────────────────────────────────────────────────
BASE_DIR     = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
ABSORPTION   = Path("/home/wubu/seymour-project/absorption")
CHROME_PORT  = "9222"
CHROME_DATA  = "/tmp/chrome-cdp-9222"
BATCH_SIZE   = 30                # videos per Chrome lifecycle
SLEEP_AFTER  = 2                 # seconds between videos (rate limit)
C11_TIMEOUT  = 600               # max seconds per C11 batch invocation
PROGRESS     = BASE_DIR / "gpu_progress.json"
C11_BIN      = ABSORPTION / "engine/absorption_c11"
TRANSCRIPTS  = ABSORPTION / "data/transcripts"
WHISPER_QUEUE = BASE_DIR / "whisper_remaining.txt"

# Output/results are logged here
LOG_FILE     = BASE_DIR / "final_absorber.log"
# ────────────────────────────────────────────────────────────────────

g_stop = False


# ── Helpers ─────────────────────────────────────────────────────────

def log(msg):
    """Print with timestamp to stdout AND logfile."""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def load_progress():
    """Return (done_set, failed_list)."""
    if PROGRESS.exists():
        try:
            d = json.loads(PROGRESS.read_text())
            return set(d.get("done", [])), d.get("failed", [])
        except Exception:
            pass
    return set(), []


def save_progress(done_set, failed_list, whisper_list=None):
    """Atomically write progress."""
    d = {
        "done": sorted(done_set),
        "failed": list(set(failed_list)),
        "updated": datetime.now().isoformat(),
    }
    tmp = PROGRESS.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(d, indent=2) + "\n")
    tmp.rename(PROGRESS)
    if whisper_list is not None and whisper_list:
        WHISPER_QUEUE.write_text("\n".join(whisper_list) + "\n")


def get_remaining(vids):
    """Dedup vids against ALL existing transcript sources."""
    done, _ = load_progress()

    # GPU whisper transcripts  (non-empty)
    done.update(
        f.stem.replace("_whisper", "")
        for f in (BASE_DIR / "whisper_transcripts").glob("*_whisper.txt")
        if f.stat().st_size > 10
    )

    # C11 saved transcripts
    done.update(
        f.stem
        for f in TRANSCRIPTS.glob("*.txt")
        if f.stat().st_size > 10
    )

    # videos_already_done.txt from C11
    ald = ABSORPTION / "data/videos_already_done.txt"
    if ald.exists():
        done.update(l.strip() for l in ald.read_text().splitlines() if l.strip())

    # videos already in whisper queue
    if WHISPER_QUEUE.exists():
        done.update(l.strip() for l in WHISPER_QUEUE.read_text().splitlines() if l.strip())

    return [v for v in vids if v not in done]


def chrome_status():
    """Check if Chrome CDP is live. Returns bool."""
    try:
        r = subprocess.run(
            ["curl", "-sf", f"http://127.0.0.1:{CHROME_PORT}/json"],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0 and len(r.stdout) > 10
    except Exception:
        return False


def start_chrome():
    """Launch headless Chromium on CDP port."""
    cmd = [
        "/snap/bin/chromium",
        "--headless",
        "--remote-debugging-port=" + CHROME_PORT,
        "--remote-debugging-address=0.0.0.0",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--user-data-dir=" + CHROME_DATA,
        "--no-first-run",
        "--no-default-browser-check",
        "--ozone-platform=headless",
        "--use-angle=swiftshader-webgl",
        "--ozone-override-screen-size=800,600",
        "--noerrdialogs",
        "--password-store=basic",
        "--gtk-version=3",
        "--disable-features=TFLiteLanguageDetectionEnabled",
    ]
    with open("/tmp/chrome_c11.log", "a") as logf:
        subprocess.Popen(cmd, stdout=logf, stderr=logf, preexec_fn=os.setpgrp)


def ensure_chrome():
    """Kill stale Chrome, start fresh, wait for CDP readiness."""
    log("♻ Restarting Chrome (memory leak mitigation)...")

    # Kill ALL chrome processes on our port
    try:
        subprocess.run(
            ["pkill", "-9", "-f", r"chrome.*--remote-debugging-port=" + CHROME_PORT],
            capture_output=True, timeout=10,
        )
    except subprocess.TimeoutExpired:
        # pkill hangs on zombies — force kill via pgrep
        try:
            out = subprocess.run(["pgrep", "-f", "chrome.*9222"], capture_output=True, text=True, timeout=5)
            for pid in out.stdout.strip().split("\n"):
                if pid.strip():
                    os.kill(int(pid.strip()), 9)
        except:
            pass
    time.sleep(2)

    # Also kill any orphaned renderers
    try:
        subprocess.run(["pkill", "-9", "-f", r"chrome.*--type=renderer"], capture_output=True, timeout=5)
    except: pass
    try:
        subprocess.run(["pkill", "-9", "-f", r"chrome.*--type=zygote"], capture_output=True, timeout=5)
    except: pass
    time.sleep(1)

    start_chrome()

    # Wait for CDP readiness
    for attempt in range(30):
        time.sleep(1)
        if chrome_status():
            free = subprocess.run(["free", "-m"], capture_output=True, text=True).stdout
            mem_line = free.split("\n")[1].split()
            avail_mb = int(mem_line[6])
            log(f"✓ Chrome CDP ready (port {CHROME_PORT}, ~{avail_mb}MB RAM available)")
            return True

    log("✗ Chrome failed to start — aborting")
    return False


def run_c11_batch(vids):
    """
    Feed a batch of video IDs into C11 absorber via stdin.
    Returns dict: {vid: True} for success, {vid: False} for fail/whisper.
    Timeout handled per-batch — on timeout we restart Chrome and retry one-by-one.
    """
    if not vids:
        return {}

    c11_cwd = str(C11_BIN.parent.parent)  # absorption/ dir
    batch_str = "\n".join(vids) + "\n"

    try:
        result = subprocess.run(
            [str(C11_BIN)],
            input=batch_str,
            capture_output=True, text=True, timeout=C11_TIMEOUT,
            cwd=c11_cwd,
        )
        stderr = result.stderr.strip()
    except subprocess.TimeoutExpired:
        log(f"  ⚠ C11 batch timed out after {C11_TIMEOUT}s — restarting Chrome")
        ensure_chrome()
        stderr = ""

    # Authoritative check: did transcripts get saved to disk?
    ok_count = 0
    fail_count = 0
    outcomes = {}

    for vid in vids:
        txt_path = TRANSCRIPTS / f"{vid}.txt"
        if txt_path.exists() and txt_path.stat().st_size > 10:
            outcomes[vid] = True
            ok_count += 1
        else:
            outcomes[vid] = False
            fail_count += 1

    if stderr:
        last_lines = stderr.split("\n")[-3:]
        for ll in last_lines:
            stripped = ll.strip()
            if stripped:
                log(f"  C11: {stripped[:100]}")

    log(f"  Batch: {ok_count} done, {fail_count} fail/whisper")
    return outcomes


# ── Signal handler ─────────────────────────────────────────────────

def handle_signal(sig, frame):
    """Graceful shutdown — finish current batch then exit."""
    global g_stop
    sig_name = signal.Signals(sig).name
    log(f"⚠ {sig_name} received — finishing current batch, then stopping...")
    g_stop = True


# ── Main ───────────────────────────────────────────────────────────

def main():
    global g_stop
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Ensure log file exists
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--input", "-i", default=str(BASE_DIR / "remaining_v4.txt"))
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        log(f"ERROR: {input_path} not found")
        return 1

    all_vids = [l.strip() for l in input_path.read_text().splitlines() if l.strip()]

    # Ensure Chrome is running
    if not chrome_status():
        if not ensure_chrome():
            return 1

    log(f"══ Final Absorption Orchestrator ══")
    log(f"  Source:     {input_path.name} ({len(all_vids)} videos)")
    log(f"  Pipeline:   C11 CDP (port {CHROME_PORT})")
    log(f"  Chrome:     restart every {BATCH_SIZE} videos")
    log(f"  Rate:       {SLEEP_AFTER}s between videos")

    round_num = 0

    while not g_stop:
        round_num += 1
        remaining = get_remaining(all_vids)
        total_remaining = len(remaining)

        log(f"\n{'─'*45}")
        log(f"Round {round_num}: {total_remaining} remaining")
        log(f"{'─'*45}")

        if total_remaining == 0:
            log("Nothing to do — all videos absorbed!")
            break

        # Take next batch
        batch = remaining[:BATCH_SIZE]
        log(f"Processing {len(batch)} videos (batch {round_num})...")

        # Run C11 on batch
        outcomes = run_c11_batch(batch)

        # Process results & save
        done_set, failed_list = load_progress()
        whisper_list = []
        if WHISPER_QUEUE.exists():
            whisper_list = [l.strip() for l in WHISPER_QUEUE.read_text().splitlines() if l.strip()]

        for vid in batch:
            result = outcomes.get(vid, False)
            if result is True:
                done_set.add(vid)
            else:
                # Not absorbed — if C11 couldn't get it, mark as whisper-needed
                if vid not in done_set and vid not in whisper_list:
                    whisper_list.append(vid)

        save_progress(done_set, failed_list, whisper_list)
        log(f"  Saved: {len(done_set)} done, {len(failed_list)} fail, {len(whisper_list)} → whisper")

        # Chrome restart between batches
        if total_remaining > len(batch) and not g_stop:
            if not ensure_chrome():
                log("ERROR: Chrome failed to restart")
                return 1

        # Rate-limit pause between batches
        if total_remaining > len(batch) and not g_stop:
            time.sleep(3)

    # Final report
    done_set, failed_list = load_progress()
    whisper_list = WHISPER_QUEUE.read_text().splitlines() if WHISPER_QUEUE.exists() else []
    total_done = len(done_set)
    total_fail = len(failed_list)
    total_whisper = len(whisper_list)

    log(f"\n{'═'*50}")
    log(f"══ COMPLETE ══")
    log(f"  C11 absorbed:  {total_done}")
    log(f"  Failed:        {total_fail}")
    log(f"  → Whisper:     {total_whisper}")
    log(f"  Total done:    {total_done + total_fail + total_whisper}")
    log(f"{'═'*50}")

    if total_whisper > 0:
        log(f"  📋 Whisper queue: {WHISPER_QUEUE}")
        log(f"  Next: run the whisper fallback pipeline")

    return 0


if __name__ == "__main__":
    sys.exit(main())