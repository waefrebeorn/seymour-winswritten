#!/usr/bin/env python3
"""
Extract image files from ISO 9660 archives using pure Python.
No external tools needed.
"""

import os
import sys
import struct
from pathlib import Path

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.pcx', '.wmf', '.emf', '.ico'}

def read_iso9660_images(iso_path: str, output_dir: str):
    """Extract files from an ISO 9660 image."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(iso_path, 'rb') as f:
        # Skip system area (16 sectors = 32768 bytes)
        f.seek(32768)

        # Read Primary Volume Descriptor
        sector = f.read(2048)
        if sector[:6] != b'\x01CD001':
            # Try at offset 16*2048
            f.seek(16 * 2048)
            sector = f.read(2048)

        # Parse root directory record
        # PVD starts at byte 156 for root directory entry
        root_dir = sector[155:190]

        # Extract root directory LBA and size
        root_lba = struct.unpack('<I', sector[156:160])[0]
        root_size = struct.unpack('<I', sector[160:164])[0]

        print(f"Root directory: LBA={root_lba}, size={root_size}")

        # Read root directory
        f.seek(root_lba * 2048)
        root_data = f.read(root_size)

        # Parse directory entries
        extracted = 0
        pos = 0
        while pos < len(root_data):
            entry_len = root_data[pos]
            if entry_len == 0:
                # Skip padding
                pos += 1
                continue

            entry = root_data[pos:pos+entry_len]

            # Parse entry
            ext_attr_len = entry[1]
            data_lba = struct.unpack('<I', entry[2:6])[0]
            data_size = struct.unpack('<I', entry[10:14])[0]
            flags = entry[25]
            name_len = entry[32]
            name_bytes = entry[33:33+name_len]

            # Decode name (ISO 9660 Level 1: 8.3 uppercase)
            name = name_bytes.decode('ascii', errors='ignore').rstrip()

            # Skip . and ..
            if name and name not in ('.', '..'):
                is_dir = bool(flags & 0x02)
                ext = Path(name).suffix.lower()

                if not is_dir and ext in IMAGE_EXTENSIONS:
                    # Extract file
                    f.seek(data_lba * 2048)
                    file_data = f.read(data_size)
                    out_path = output_dir / name
                    out_path.write_bytes(file_data)
                    extracted += 1
                    if extracted <= 20:
                        print(f"  Extracted: {name} ({data_size} bytes)")
                elif is_dir and data_size > 0:
                    # Recurse into subdirectory
                    sub_files = extract_subdir(f, data_lba, data_size, output_dir, name)
                    extracted += sub_files

            pos += entry_len

    print(f"\nTotal extracted: {extracted} images")
    return extracted


def extract_subdir(f, lba, size, output_dir, prefix):
    """Extract files from a subdirectory."""
    f.seek(lba * 2048)
    dir_data = f.read(size)
    extracted = 0
    pos = 0

    while pos < len(dir_data):
        entry_len = dir_data[pos]
        if entry_len == 0:
            pos += 1
            continue

        entry = dir_data[pos:pos+entry_len]
        data_lba = struct.unpack('<I', entry[2:6])[0]
        data_size = struct.unpack('<I', entry[10:14])[0]
        flags = entry[25]
        name_len = entry[32]
        name_bytes = entry[33:33+name_len]
        name = name_bytes.decode('ascii', errors='ignore').rstrip()

        if name and name not in ('.', '..'):
            is_dir = bool(flags & 0x02)
            ext = Path(name).suffix.lower()

            if not is_dir and ext in IMAGE_EXTENSIONS:
                f.seek(data_lba * 2048)
                file_data = f.read(data_size)
                out_path = output_dir / f"{prefix}_{name}"
                out_path.write_bytes(file_data)
                extracted += 1

        pos += entry_len

    return extracted


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <iso_file> <output_dir>")
        sys.exit(1)

    read_iso9660_images(sys.argv[1], sys.argv[2])
