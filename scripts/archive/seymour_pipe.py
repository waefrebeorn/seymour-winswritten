#!/usr/bin/env python3
"""
Seymour Pipe v2 — The Writer's Video Editor
=============================================
Audio: OGG Vorbis (saves ~80% space vs WAV)
Clips: H.265/HEVC MP4 (saves ~50% space vs H.264)

Usage:
    python3 seymour_pipe.py <youtube_url> [--model tiny] [--export-clips]
    python3 seymour_pipe.py batch <url_file.txt>
"""

import os
import sys
import json
import re
import subprocess
import tempfile
from pathlib import Path
from faster_whisper import WhisperModel
import yt_dlp
import numpy as np

OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Separate dir for OGG audio files
AUDIO_DIR = OUTPUT_DIR / "audio"
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Separate dir for H.265 clips
CLIPS_DIR = OUTPUT_DIR / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)


class SeymourPipe:
    def __init__(self, model_size="tiny"):
        self.model_size = model_size
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the whisper model."""
        print(f"[Seymour Pipe] Loading model: {self.model_size}...")
        self.model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        print("[Seymour Pipe] Model loaded.")

    def get_video_info(self, url):
        """Get video metadata without downloading."""
        ydl_opts = {"quiet": True, "no_warnings": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                "id": info.get("id"),
                "title": info.get("title", "untitled"),
                "duration": info.get("duration", 0),
                "channel": info.get("channel", info.get("uploader", "unknown")),
                "view_count": info.get("view_count", 0),
                "upload_date": info.get("upload_date", ""),
                "description": info.get("description", "")[:500],
            }

    def download_audio_ogg(self, url, video_id):
        """Download audio as OGG Vorbis (much smaller than WAV)."""
        safe_title = re.sub(r"[^\w\s-]", "", video_id).strip()[:30]
        ogg_path = AUDIO_DIR / f"{safe_title}_{video_id}.ogg"

        if ogg_path.exists():
            print(f"[Seymour Pipe] Audio already exists: {ogg_path}")
            return ogg_path

        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "vorbis",
                "preferredquality": "3",
            }],
            "outtmpl": str(ogg_path).replace(".ogg", ".%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }

        print(f"[Seymour Pipe] Downloading audio (OGG)...")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find actual output file
        if not ogg_path.exists():
            for f in AUDIO_DIR.glob(f"*{video_id}*"):
                f.rename(ogg_path)
                break

        size_mb = ogg_path.stat().st_size / 1024 / 1024
        print(f"[Seymour Pipe] Audio saved: {ogg_path} ({size_mb:.1f} MB)")
        return ogg_path

    def ogg_to_wav_chunk(self, ogg_path, start_time, duration_sec):
        """Convert OGG chunk to WAV for whisper (lossless pipe to ffmpeg)."""
        cmd = [
            "ffmpeg", "-y", "-i", str(ogg_path),
            "-ss", str(start_time), "-t", str(duration_sec),
            "-ar", "16000", "-ac", "1",
            "-f", "wav", "pipe:1"
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg chunk failed: {result.stderr[:200]}")

        # Convert raw PCM to float32
        audio_data = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
        return audio_data

    def transcribe(self, ogg_path):
        """Transcribe OGG audio with chunked processing."""
        print(f"[Seymour Pipe] Transcribing: {ogg_path}")

        file_size = ogg_path.stat().st_size

        # Get duration from OGG
        cmd = ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
               "-of", "csv=p=0", str(ogg_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        duration = float(result.stdout.strip())

        print(f"[Seymour Pipe] Audio: {duration/60:.1f} minutes, {file_size/1024/1024:.1f} MB (OGG)")

        # For files > 50MB OGG (~4+ hours), use chunked
        if file_size > 50 * 1024 * 1024:
            print(f"[Seymour Pipe] Large file — using chunked transcription")
            return self._transcribe_chunked(ogg_path, duration)

        # Small files: convert entire OGG to WAV pipe, then transcribe
        audio_data = self.ogg_to_wav_chunk(ogg_path, 0, int(duration) + 10)
        segments_iter, info = self.model.transcribe(
            audio_data,
            beam_size=5,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300, threshold=0.5)
        )

        transcript_parts = []
        for segment in segments_iter:
            transcript_parts.append({
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip(),
            })

        print(f"[Seymour Pipe] Transcribed {len(transcript_parts)} segments")
        return {
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": duration,
            "segments": transcript_parts,
        }

    def _transcribe_chunked(self, ogg_path, duration, chunk_minutes=15):
        """Transcribe large OGG in chunks via ffmpeg pipe to whisper."""
        chunk_seconds = chunk_minutes * 60
        total_chunks = int(duration // chunk_seconds) + 1

        print(f"[Seymour Pipe] Processing {total_chunks} chunks of {chunk_minutes}min each")

        all_segments = []
        language = "en"
        lang_prob = 0.0

        for chunk_idx in range(total_chunks):
            start_time = chunk_idx * chunk_seconds
            print(f"[Seymour Pipe] Chunk {chunk_idx+1}/{total_chunks} ({start_time//60}m{start_time%60}s)...")

            try:
                audio_data = self.ogg_to_wav_chunk(ogg_path, start_time, chunk_seconds)
                segments_iter, info = self.model.transcribe(
                    audio_data,
                    beam_size=5,
                    vad_filter=True,
                    vad_parameters=dict(min_silence_duration_ms=300, threshold=0.5),
                )

                chunk_segments = []
                for segment in segments_iter:
                    chunk_segments.append({
                        "start": round(segment.start + start_time, 2),
                        "end": round(segment.end + start_time, 2),
                        "text": segment.text.strip(),
                    })

                all_segments.extend(chunk_segments)
                language = info.language
                lang_prob = info.language_probability
                print(f"[Seymour Pipe]   Done: {len(chunk_segments)} segments")
            except Exception as e:
                print(f"[Seymour Pipe]   Failed: {e}")

        print(f"[Seymour Pipe] Total: {len(all_segments)} segments from {total_chunks} chunks")
        return {
            "language": language,
            "language_probability": lang_prob,
            "duration": duration,
            "segments": all_segments,
        }

    def detect_moments(self, transcript):
        """Detect interesting moments for clipping."""
        segments = transcript["segments"]
        moments = []

        patterns = {
            "reaction": [
                r"\b(oh\s*my|wow|holy|what|no\s*way|are\s*you\s*kidding|insane|nuts)\b",
                r"\b(lol|lmao|hahaha|haha|rofl)\b",
            ],
            "story_beat": [
                r"\b(so\s*then|and\s*then|but\s*then|suddenly|finally|here\'s\s*the\s*thing)\b",
                r"\b(listen|okay\s*so|here\'s\s*what|so\s*here\'s)\b",
            ],
            "emotional": [
                r"\b(can\'t\s*believe|never\s*thought|dream|forget|remember\s*when)\b",
                r"\b(miss|loved|lost|found|kept)\b",
            ],
            "gameplay_key": [
                r"\b(boss|final|beat|won|lost|dies?|killed|defeated)\b",
                r"\b(secret|hidden|easter\s*egg|ending|twist)\b",
            ],
            "penny_philosophy": [
                r"\b(penny|pennies|nickel|dollar|money|coin|change)\b",
                r"\b(mom|mother|wife|family|remember)\b",
            ],
        }

        for i, seg in enumerate(segments):
            text = seg["text"].lower()
            for category, regex_list in patterns.items():
                for pattern in regex_list:
                    if re.search(pattern, text, re.IGNORECASE):
                        moments.append({
                            "index": i,
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": seg["text"],
                            "category": category,
                            "score": self._score_moment(seg, category),
                        })
                        break

        # Deduplicate nearby moments (within 5 seconds)
        deduped = []
        moments.sort(key=lambda x: x["start"])
        for m in moments:
            if not deduped or (m["start"] - deduped[-1]["start"]) > 5:
                deduped.append(m)

        return deduped

    def _score_moment(self, segment, category):
        """Score a moment for clip-worthiness."""
        text = segment["text"]
        score = 1.0

        if 10 <= len(text.split()) <= 30:
            score += 0.5
        elif len(text.split()) > 30:
            score += 0.3

        if category in ["reaction", "penny_philosophy", "emotional"]:
            score += 1.0
        elif category == "story_beat":
            score += 0.7

        return round(score, 2)

    def export_clip(self, video_url, start_time, end_time, clip_index, title=""):
        """Export a clip as H.265 MP4 from YouTube (no re-download needed)."""
        safe_title = re.sub(r"[^\w\s-]", "", title).strip().replace(" ", "_")[:30]
        clip_path = CLIPS_DIR / f"{safe_title}_clip{clip_index:03d}.mp4"

        if clip_path.exists():
            print(f"[Seymour Pipe] Clip already exists: {clip_path}")
            return clip_path

        # Download segment using yt-dlp + ffmpeg H.265 encoding
        duration = end_time - start_time
        ydl_opts = {
            "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "quiet": True,
            "no_warnings": True,
        }

        # Use ffmpeg to download segment and encode to H.265
        # First get the direct stream URL
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            formats = info.get("formats", [])
            # Get best video
            video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
            if video_formats:
                video_url_direct = sorted(video_formats, key=lambda x: x.get("height", 0), reverse=True)[0]["url"]
            else:
                video_url_direct = info.get("url")

        # Download + encode H.265 in one pass
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(start_time),
            "-i", video_url_direct,
            "-t", str(duration),
            "-c:v", "libx265", "-crf", "28", "-preset", "fast",
            "-c:a", "aac", "-b:a", "128k",
            "-tag:v", "hvc1",
            "-movflags", "+faststart",
            str(clip_path)
        ]

        print(f"[Seymour Pipe] Exporting clip {clip_index} (H.265): {start_time}s-{end_time}s")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0 and clip_path.exists():
            size_mb = clip_path.stat().st_size / 1024 / 1024
            print(f"[Seymour Pipe] Clip saved: {clip_path} ({size_mb:.1f} MB)")
            return clip_path
        else:
            print(f"[Seymour Pipe] Clip export failed: {result.stderr[:200]}")
            return None

    def export_top_clips(self, url, moments, title, top_n=10):
        """Export the top N scored clips as H.265 MP4."""
        if not moments:
            return []

        # Sort by score, take top N
        sorted_moments = sorted(moments, key=lambda x: x["score"], reverse=True)[:top_n]
        # Sort by time for consistent ordering
        sorted_moments.sort(key=lambda x: x["start"])

        exported = []
        for i, m in enumerate(sorted_moments):
            clip_path = self.export_clip(url, m["start"], m["end"], i + 1, title)
            if clip_path:
                exported.append({
                    "path": str(clip_path),
                    "start": m["start"],
                    "end": m["end"],
                    "category": m["category"],
                    "score": m["score"],
                    "text": m["text"][:100],
                })

        return exported

    def format_transcript(self, transcript, title=""):
        """Format transcript for reading."""
        lines = []
        if title:
            lines.append(f"# {title}")
            lines.append("")

        for seg in transcript["segments"]:
            minutes = int(seg["start"] // 60)
            seconds = int(seg["start"] % 60)
            timestamp = f"{minutes:02d}:{seconds:02d}"
            lines.append(f"[{timestamp}] {seg['text']}")

        return "\n".join(lines)

    def format_clips(self, moments, title=""):
        """Format clip suggestions."""
        lines = []
        lines.append(f"# Clip Suggestions: {title}")
        lines.append(f"# Generated by Seymour Pipe")
        lines.append(f"# Total moments detected: {len(moments)}")
        lines.append("")

        for i, m in enumerate(moments):
            start_min = int(m["start"] // 60)
            start_sec = int(m["start"] % 60)
            end_min = int(m["end"] // 60)
            end_sec = int(m["end"] % 60)

            lines.append(f"## Clip {i+1}: {m['category'].upper()} (score: {m['score']})")
            lines.append(f"   Time: {start_min:02d}:{start_sec:02d} — {end_min:02d}:{end_sec:02d}")
            lines.append(f"   \"{m['text'][:120]}\"")
            lines.append("")

        return "\n".join(lines)

    def process(self, url, export_clips=False, top_n=10):
        """Full pipeline: download OGG → transcribe → detect moments → optional H.265 clips."""
        # Get video info
        info = self.get_video_info(url)
        print(f"\n{'='*60}")
        print(f"SEYMOUR PIPE v2 — Processing:")
        print(f"  Title: {info['title']}")
        print(f"  Duration: {info['duration'] // 60}m {info['duration'] % 60}s")
        print(f"  Channel: {info['channel']}")
        print(f"{'='*60}\n")

        # Download audio as OGG
        ogg_path = self.download_audio_ogg(url, info["id"])

        # Transcribe
        transcript = self.transcribe(ogg_path)

        # Format output
        formatted = self.format_transcript(transcript, info["title"])

        # Detect moments
        moments = self.detect_moments(transcript)
        clips_formatted = self.format_clips(moments, info["title"])

        # Export H.265 clips if requested
        exported_clips = []
        if export_clips and moments:
            print(f"\n[Seymour Pipe] Exporting top {top_n} clips as H.265 MP4...")
            exported_clips = self.export_clip(url, moments, info["title"], top_n)

        # Save
        safe_title = re.sub(r"[^\w\s-]", "", info["title"]).strip().replace(" ", "_")[:50]

        # Save transcript
        transcript_path = OUTPUT_DIR / f"{safe_title}_{info['id']}_transcript.txt"
        with open(transcript_path, "w") as f:
            f.write(formatted)
        print(f"\n[Seymour Pipe] Transcript saved: {transcript_path}")

        # Save clips list
        clips_path = OUTPUT_DIR / f"{safe_title}_{info['id']}_clips.txt"
        with open(clips_path, "w") as f:
            f.write(clips_formatted)
        print(f"[Seymour Pipe] Clips saved: {clips_path}")

        # Save raw JSON
        json_path = OUTPUT_DIR / f"{safe_title}_{info['id']}_raw.json"
        with open(json_path, "w") as f:
            json.dump({
                "info": info,
                "transcript": transcript,
                "moments": moments,
                "exported_clips": exported_clips,
            }, f, indent=2)
        print(f"[Seymour Pipe] Raw data saved: {json_path}")

        # Print summary
        print(f"\n{'='*60}")
        print(f"SUMMARY")
        print(f"  Transcript: {len(transcript['segments'])} segments, ~{len(formatted.split())} words")
        print(f"  Clips detected: {len(moments)}")
        if exported_clips:
            print(f"  Clips exported (H.265): {len(exported_clips)}")
        categories = {}
        for m in moments:
            categories[m["category"]] = categories.get(m["category"], 0) + 1
        for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
            print(f"    {cat}: {count}")
        print(f"{'='*60}\n")

        print(clips_formatted)

        return {
            "info": info,
            "transcript": transcript,
            "moments": moments,
            "exported_clips": exported_clips,
            "formatted_transcript": formatted,
            "formatted_clips": clips_formatted,
        }


def main():
    if len(sys.argv) < 2:
        print("Seymour Pipe v2 — The Writer's Video Editor")
        print("")
        print("Usage:")
        print("  python3 seymour_pipe.py <youtube_url> [--model tiny] [--export-clips]")
        print("  python3 seymour_pipe.py batch <url_file.txt>")
        print("")
        print("Examples:")
        print("  python3 seymour_pipe.py 'https://www.youtube.com/watch?v=4LxOKWC4cho'")
        print("  python3 seymour_pipe.py 'https://...' --export-clips")
        print("  python3 seymour_pipe.py batch my_videos.txt")
        sys.exit(1)

    if sys.argv[1] == "batch":
        url_file = sys.argv[2]
        model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "tiny"
        pipe = SeymourPipe(model)

        with open(url_file) as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]

        print(f"[Seymour Pipe] Processing {len(urls)} videos...")
        for i, url in enumerate(urls):
            print(f"\n[Seymour Pipe] Video {i+1}/{len(urls)}")
            try:
                pipe.process(url)
            except Exception as e:
                print(f"[Seymour Pipe] ERROR: {e}")
                continue
    else:
        url = sys.argv[1]
        model = sys.argv[sys.argv.index("--model") + 1] if "--model" in sys.argv else "tiny"
        export = "--export-clips" in sys.argv
        pipe = SeymourPipe(model)
        result = pipe.process(url, export_clips=export)

        print("\n\n" + "=" * 60)
        print("FULL TRANSCRIPT")
        print("=" * 60)
        print(result["formatted_transcript"])


if __name__ == "__main__":
    main()
