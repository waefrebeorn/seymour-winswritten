#!/bin/bash
# Seymour Clipart Downloader
# Run this script to download all clipart CD-ROM ISOs from Archive.org
# Usage: bash download-clipart.sh

set -euo pipefail

DOWNLOAD_DIR="/home/wubu/seymour-project/clipart/downloads"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

echo "=== Seymour Clipart Downloader ==="
echo "Download directory: $DOWNLOAD_DIR"
echo ""

# Function to download with retry
download_with_retry() {
    local url="$1"
    local output="$2"
    local max_retries=3
    local retry=0
    
    while [ $retry -lt $max_retries ]; do
        echo "Downloading: $output (attempt $((retry+1))/$max_retries)"
        if wget --timeout=60 --tries=2 -q --show-progress "$url" -O "$output" 2>&1 | tail -n 3; then
            local size=$(stat -c%s "$output" 2>/dev/null || echo 0)
            if [ "$size" -gt 1000 ]; then
                echo "  ✓ Success: $(du -h "$output" | cut -f1)"
                return 0
            fi
        fi
        retry=$((retry+1))
        echo "  ✗ Failed, retrying..."
        sleep 5
    done
    
    echo "  ✗ FAILED after $max_retries attempts: $output"
    return 1
}

echo "--- ClickArt 200,000 (1997) ---"
download_with_retry \
    "https://archive.org/download/clickart-200000/ClickArt_200K.iso" \
    "clickart-200k.iso" || true

echo ""
echo "--- Web Clipart 1 ---"
download_with_retry \
    "https://archive.org/download/web-clipart-1/Web_Clipart_1.iso" \
    "web-clipart-1.iso" || true

echo ""
echo "--- 115,000 Clip Art Images ---"
download_with_retry \
    "https://archive.org/download/115-000-clip-art-images/115000_ClipArt_Images.iso" \
    "115k-clipart.iso" || true

echo ""
echo "--- Clipart Etc ---"
download_with_retry \
    "https://archive.org/download/weirdwithit.clipartetc/Clipart_etc.iso" \
    "clipart-etc.iso" || true

echo ""
echo "=== Download Summary ==="
ls -lh "$DOWNLOAD_DIR/" 2>/dev/null
echo ""
echo "Total size: $(du -sh "$DOWNLOAD_DIR" 2>/dev/null | cut -f1)"
