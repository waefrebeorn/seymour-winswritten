---
title: "Whisper Fallback Pipeline"
created: "2026-06-25"
updated: "2026-06-25"
tags: [source, pipeline, transcription]
sources: 1
status: active
---

# Whisper Fallback Pipeline

## Purpose

When YouTube CDP "In this video" transcripts are unavailable (~15-20% of videos), fall back to audio transcription via faster_whisper.

## Pipeline

```
YouTube URL → yt-dlp audio extraction → faster_whisper transcription → wiki/raw/youtube/<slug>.md
```

## Tool: faster_whisper (already installed)

- **Model:** `tiny.en` (fastest CPU, English)
- **Quantization:** int8 (fastest on CPU)
- **Device:** CPU (no GPU needed for this workload)
- **Location:** `/home/wubu/.hermes/hermes-agent/venv/lib/python3.11/site-packages/faster_whisper/`

### Usage

```python
from faster_whisper import WhisperModel

model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
segments, info = model.transcribe("audio.wav", beam_size=5, vad_filter=True)
for segment in segments:
    print(f"[{segment.start:.1f}s -> {segment.end:.1f}s] {segment.text}")
```

### Alternative Models (speed vs accuracy)

| Model | Size | CPU Speed | Accuracy | Use When |
|-------|------|-----------|----------|----------|
| `tiny.en` | 39MB | ~0.05 RTF | Good for clear speech | Default fallback |
| `base.en` | 74MB | ~0.03 RTF | Better | If tiny misses words |
| `small.en` | 244MB | Slower | Best accuracy | Critical content |

### Audio Extraction

```bash
yt-dlp -f "bestaudio" --extract-audio --audio-format wav -o "audio.%(ext)s" <URL>
```

## Research Notes (from Grok, June 2026)

### Fastest CPU ASR Options (June 2026)

1. **whisper.cpp v1.9.1** (June 19, 2026) — C/C++ port, AVX/NEON, Q4/Q5 quantization. Fastest possible.
2. **NVIDIA Parakeet TDT 0.6B v3** (ONNX INT8) — ~18-30x speedup, RTF ~0.03-0.05. Best throughput.
3. **NVIDIA Nemotron Speech Streaming 0.6B** — Low-latency streaming, int4 quantized, ~0.67GB.
4. **faster-whisper** (ours) — CTranslate2 + whisper, Python, easy. Already installed.

### Video Frame Recognition

- **Ultralytics YOLO26** — 43% faster ONNX CPU vs YOLO11, NMS-free, nano variant ~39ms/frame on CPU.

## References

- → [[YouTube CDP Extraction]] — primary transcript method
- → [[Pipeline Architecture]] — how transcription feeds the wiki
