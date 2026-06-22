#!/usr/bin/env python3
"""
Seymour Clipart Processor
=========================
Downloads 90s clipart from Internet Archive, runs Gemma 4 12B vision inference
to categorize/describe each image, and outputs structured metadata for the
Seymour Ponderables book pipeline.

Usage:
    python3 seymour_clipart.py download [collection_url]
    python3 seymour_clipart.py process <input_dir> <output_dir>
    python3 seymour_clipart.py catalog <metadata_dir>
"""

import os
import sys
import json
import subprocess
import hashlib
import time
from pathlib import Path
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────

LLAMA_CLI = "/home/wubu/llama.cpp/build/bin/llama-cli"
MODEL_PATH = "/home/wubu/seymour-project/models/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf"
PROJECT_DIR = Path("/home/wubu/seymour-project")
CLIPART_DIR = PROJECT_DIR / "clipart"
METADATA_DIR = PROJECT_DIR / "clipart-metadata"
PONDERABLES_DIR = PROJECT_DIR / "ponderables"

# IA collections to scrape for 90s clipart
IA_CLIPART_COLLECTIONS = [
    "web-clipart-1",
    "clickart-200000",
    "weirdwithit.clipartetc",
    "115-000-clip-art-images",
]

# Vision prompt for categorizing clipart
CLIPART_VISION_PROMPT = """Look at this 1990s clipart image and describe it for a book catalog.

Respond in this exact JSON format (no other text):
{
  "subject": "brief subject description (3-7 words)",
  "category": "one of: people | objects | nature | symbols | food | animals | buildings | abstract | holiday | technology | transportation | other",
  "mood": "one of: happy | serious | whimsical | corporate | playful | dramatic | neutral | nostalgic",
  "style": "one of: line-art | filled-color | gradient | pixel-art | watercolor-style | cartoon | realistic-clipart",
  "seymour_tag": "a short hyphenated tag suitable for cross-referencing in a Seymour Ponderable book (e.g., 'business-handshake', 'smiley-sun', 'flying-dollar')",
  "ponderable_idea": "one sentence: what philosophical or cultural idea could this clipart illustrate in a Seymour Ponderable book?"
}"""

# ── Download from Internet Archive ─────────────────────────────────────────

def download_ia_collection(identifier: str, output_dir: Path) -> list[Path]:
    """Download all image files from an Internet Archive collection item."""
    output_dir.mkdir(parents=True, exist_ok=True)
    downloaded = []

    # Use ia CLI if available, otherwise wget the item page and parse
    try:
        result = subprocess.run(
            ["ia", "download", "--glob=*.{jpg,jpeg,png,gif,bmp,tif,tiff,pcx}",
             "-d", str(output_dir), identifier],
            capture_output=True, text=True, timeout=600
        )
        if result.returncode == 0:
            for f in output_dir.iterdir():
                if f.suffix.lower() in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.pcx'):
                    downloaded.append(f)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    if not downloaded:
        # Fallback: use wget to grab the item's file list and download images
        base_url = f"https://archive.org/download/{identifier}"
        try:
            result = subprocess.run(
                ["wget", "-q", "-O", "-",
                 f"https://archive.org/metadata/{identifier}/files"],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode == 0:
                try:
                    files_data = json.loads(result.stdout)
                    for f in files_data.get("result", []):
                        fname = f.get("name", "")
                        ext = Path(fname).suffix.lower()
                        if ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.pcx', '.wmf', '.emf'):
                            out_path = output_dir / fname
                            if not out_path.exists():
                                subprocess.run(
                                    ["wget", "-q", "-O", str(out_path),
                                     f"{base_url}/{fname}"],
                                    timeout=30
                                )
                            if out_path.exists() and out_path.stat().st_size > 0:
                                downloaded.append(out_path)
                except json.JSONDecodeError:
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return downloaded


def download_all_collections():
    """Download all known 90s clipart collections."""
    all_files = []
    for coll_id in IA_CLIPART_COLLECTIONS:
        out_dir = CLIPART_DIR / coll_id
        print(f"[{datetime.now():%H:%M:%S}] Downloading: {coll_id}")
        files = download_ia_collection(coll_id, out_dir)
        print(f"  -> {len(files)} images")
        all_files.extend(files)
    print(f"\nTotal images downloaded: {len(all_files)}")
    return all_files


# ── Vision Inference ───────────────────────────────────────────────────────

def run_vision_inference(image_path: Path, max_retries: int = 2) -> dict:
    """Run Gemma 4 12B vision inference on a single image."""
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                [
                    LLAMA_CLI,
                    "-m", MODEL_PATH,
                    "--mmproj", MODEL_PATH,
                    "-p", CLIPART_VISION_PROMPT,
                    "--image", str(image_path),
                    "-n", "256",
                    "--temp", "0.1",
                    "--no-display-prompt",
                    "-ngl", "0",  # CPU only
                ],
                capture_output=True, text=True, timeout=120
            )
            output = result.stdout.strip()
            # Try to extract JSON from output
            start = output.find('{')
            end = output.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = output[start:end]
                return json.loads(json_str)
        except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                return {"error": str(e), "subject": "unknown", "category": "other"}
    return {"error": "max_retries", "subject": "unknown", "category": "other"}


def process_directory(input_dir: Path, output_dir: Path, limit: int = None):
    """Process all images in a directory with vision inference."""
    output_dir.mkdir(parents=True, exist_ok=True)
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.pcx'}
    images = [f for f in sorted(input_dir.rglob("*"))
              if f.suffix.lower() in image_exts and f.is_file()]

    if limit:
        images = images[:limit]

    print(f"Processing {len(images)} images from {input_dir}")
    results = []

    for i, img_path in enumerate(images):
        print(f"  [{i+1}/{len(images)}] {img_path.name}...", end=" ", flush=True)

        # Check for cached metadata
        meta_path = output_dir / f"{img_path.stem}.json"
        if meta_path.exists():
            print("CACHED")
            results.append(json.loads(meta_path.read_text()))
            continue

        metadata = run_vision_inference(img_path)
        metadata["source_file"] = str(img_path.relative_to(input_dir))
        metadata["file_hash"] = hashlib.md5(img_path.read_bytes()).hexdigest()[:12]
        metadata["file_size"] = img_path.stat().st_size
        metadata["processed_at"] = datetime.now().isoformat()

        meta_path.write_text(json.dumps(metadata, indent=2))
        print(f"{metadata.get('category', '?')} | {metadata.get('seymour_tag', '?')}")
        results.append(metadata)

    # Write combined catalog
    catalog_path = output_dir / "_catalog.json"
    catalog_path.write_text(json.dumps(results, indent=2))
    print(f"\nCatalog written: {catalog_path} ({len(results)} entries)")
    return results


# ── Catalog & Cross-Reference ──────────────────────────────────────────────

def build_catalog(metadata_dir: Path) -> dict:
    """Build a searchable catalog from all metadata files."""
    entries = []
    for f in sorted(metadata_dir.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            entries.append(json.loads(f.read_text()))
        except json.JSONDecodeError:
            continue

    # Build indices
    by_category = {}
    by_tag = {}
    by_mood = {}

    for e in entries:
        cat = e.get("category", "other")
        tag = e.get("seymour_tag", "untagged")
        mood = e.get("mood", "neutral")

        by_category.setdefault(cat, []).append(e.get("source_file", ""))
        by_tag.setdefault(tag, []).append(e.get("source_file", ""))
        by_mood.setdefault(mood, []).append(e.get("source_file", ""))

    catalog = {
        "total_images": len(entries),
        "categories": {k: len(v) for k, v in by_category.items()},
        "moods": {k: len(v) for k, v in by_mood.items()},
        "tags": list(by_tag.keys()),
        "by_category": by_category,
        "by_tag": by_tag,
        "by_mood": by_mood,
        "entries": entries,
    }

    out_path = metadata_dir / "_full_catalog.json"
    out_path.write_text(json.dumps(catalog, indent=2))
    print(f"Catalog: {len(entries)} entries, {len(by_category)} categories, {len(by_tag)} tags")
    return catalog


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "download":
        if len(sys.argv) > 2:
            # Single collection
            coll_id = sys.argv[2]
            out_dir = CLIPART_DIR / coll_id
            files = download_ia_collection(coll_id, out_dir)
            print(f"Downloaded {len(files)} images to {out_dir}")
        else:
            download_all_collections()

    elif cmd == "process":
        input_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else CLIPART_DIR
        output_dir = Path(sys.argv[3]) if len(sys.argv) > 3 else METADATA_DIR
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else None
        process_directory(input_dir, output_dir, limit)

    elif cmd == "catalog":
        meta_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else METADATA_DIR
        build_catalog(meta_dir)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
