#!/bin/bash
# Seymour Clipart Understanding Pipeline
# Uses Gemma 4 12B vision model via llama-mtmd-cli

set -euo pipefail

MODEL_DIR="/home/wubu/seymour-project/models"
LLAMA_BIN="/home/wubu/llama.cpp/build/bin"
CLIPART_DIR="/home/wubu/seymour-project/clipart"
OUTPUT_DIR="/home/wubu/seymour-project/clipart/analyzed"

mkdir -p "$OUTPUT_DIR"

MODEL="$MODEL_DIR/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf"
MMPROJ="$MODEL_DIR/mmproj-F16.gguf"

analyze_image() {
    local img="$1"
    local basename=$(basename "$img" | sed 's/\.[^.]*$//')
    local output="$OUTPUT_DIR/${basename}.txt"
    
    echo "Analyzing: $img"
    
    # Use llama-mtmd-cli to describe the clipart
    echo "Describe this 1990s clipart image in detail. Identify: (1) the subject/object shown, (2) the style (line art, cartoon, realistic, etc.), (3) the likely category (business, nature, people, technology, etc.), (4) any text visible, (5) the emotional tone. Format as JSON with keys: subject, style, category, text, tone, description." | \
    "$LLAMA_BIN/llama-mtmd-cli" \
        -m "$MODEL" \
        --mmproj "$MMPROJ" \
        -c 4096 \
        --temp 0.3 \
        --image "$img" \
        -n 512 \
        2>/dev/null > "$output"
    
    echo "  → $output"
}

# Process all images in clipart directory
process_directory() {
    local dir="$1"
    local count=0
    local total=$(find "$dir" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.bmp" -o -name "*.tif" -o -name "*.tiff" \) | wc -l)
    
    echo "Processing $total images from $dir"
    
    find "$dir" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.bmp" -o -name "*.tif" -o -name "*.tiff" \) | while read img; do
        count=$((count + 1))
        analyze_image "$img"
    done
    
    echo "Processed $count images"
}

# Extract and mount ISO files
extract_iso() {
    local iso="$1"
    local mount_point="/tmp/seymour-iso-$(basename "$iso" .iso)"
    
    echo "Extracting ISO: $iso"
    mkdir -p "$mount_point"
    
    # Try mounting first
    if sudo mount -o loop,ro "$iso" "$mount_point" 2>/dev/null; then
        echo "  Mounted at $mount_point"
        find "$mount_point" -type f \( -name "*.jpg" -o -name "*.jpeg" -o -name "*.png" -o -name "*.gif" -o -name "*.bmp" -o -name "*.tif" -o -name "*.tiff" -o -name "*.wmf" -o -name "*.emf" \) -exec cp {} "$CLIPART_DIR/" \;
        sudo umount "$mount_point"
    else
        echo "  Mount failed, trying 7z extraction"
        7z x "$iso" -o"$CLIPART_DIR" -y 2>/dev/null || echo "  FAILED: $iso"
    fi
    
    rmdir "$mount_point" 2>/dev/null || true
}

# Main
case "${1:-help}" in
    analyze)
        process_directory "${2:-$CLIPART_DIR}"
        ;;
    extract)
        for iso in "$CLIPART_DIR"/*.iso; do
            [ -f "$iso" ] && extract_iso "$iso"
        done
        ;;
    full)
        echo "=== Phase 1: Extract ISOs ==="
        for iso in "$CLIPART_DIR"/*.iso; do
            [ -f "$iso" ] && extract_iso "$iso"
        done
        echo "=== Phase 2: Analyze Images ==="
        process_directory "$CLIPART_DIR"
        ;;
    *)
        echo "Usage: $0 {analyze|extract|full} [directory]"
        echo ""
        echo "  analyze [dir]  - Analyze all images in directory"
        echo "  extract        - Extract all ISO files in clipart dir"
        echo "  full           - Extract then analyze"
        ;;
esac
