#!/usr/bin/env python3
"""Extract images from ISO 9660 archives using pycdlib walk() + BytesIO."""
import sys
import io
from pathlib import Path
import pycdlib

IMAGE_EXTS = {'.bmp', '.jpg', '.jpeg', '.png', '.gif', '.tif', '.tiff', '.pcx', '.wmf', '.emf', '.ico'}

def extract_iso(iso_path: str, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    iso = pycdlib.PyCdlib()
    iso.open(iso_path)

    extracted = 0
    seen = set()
    errors = []

    for (dir_path, subdirs, files) in iso.walk(iso_path='/'):
        for fname in files:
            clean_name = fname.split(';')[0] if ';' in fname else fname
            ext = Path(clean_name).suffix.lower()
            if ext not in IMAGE_EXTS:
                continue

            iso_file_path = dir_path.rstrip('/') + '/' + fname
            category = Path(dir_path).name if dir_path != '/' else 'root'
            out_name = f"{category}_{clean_name}"
            out_path = output_dir / out_name

            if out_name in seen:
                continue
            seen.add(out_name)

            try:
                buffer = io.BytesIO()
                iso.get_file_from_iso_fp(buffer, iso_path=iso_file_path)
                data = buffer.getvalue()
                if len(data) > 0:
                    out_path.write_bytes(data)
                    extracted += 1
                    if extracted <= 10:
                        print(f"  {out_name} ({len(data)} bytes)")
            except Exception as e:
                if len(errors) < 3:
                    errors.append(f"  SKIP {clean_name}: {e}")

    for e in errors:
        print(e)

    iso.close()
    print(f"\nExtracted {extracted} images to {output_dir}")
    return extracted

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <iso_file> <output_dir>")
        sys.exit(1)
    extract_iso(sys.argv[1], sys.argv[2])
