#!/bin/bash
# Download all models for Seymour project
# Run with: bash download-models.sh

set -euo pipefail

MODEL_DIR="/home/wubu/seymour-project/models"
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

echo "=== Seymour Model Downloader ==="
echo "Target directory: $MODEL_DIR"
echo "Available space: $(df -h /home/wubu | tail -n 1 | awk '{print $4}')"
echo ""

# --- Gemma 4 12B QAT (UD-Q4_K_XL = 6.72GB) ---
echo "--- Downloading Gemma 4 12B QAT (UD-Q4_K_XL) ---"
if [ ! -f "gemma-4-12B-it-qat-UD-Q4_K_XL.gguf" ]; then
    wget -q --show-progress \
        "https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF/resolve/main/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf" \
        -O gemma-4-12B-it-qat-UD-Q4_K_XL.gguf 2>&1 | tail -n 3
    echo "  ✓ Gemma 4 12B QAT downloaded"
else
    echo "  ✓ Already exists: gemma-4-12B-it-qat-UD-Q4_K_XL.gguf"
fi

# --- Gemma 4 12B MTP Header (for speculative decoding) ---
echo ""
echo "--- Downloading Gemma 4 12B MTP drafter ---"
if [ ! -f "gemma-4-12B-it-MTP.gguf" ]; then
    wget -q --show-progress \
        "https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF/resolve/main/MTP/gemma-4-12B-it-BF16-MTP.gguf" \
        -O gemma-4-12B-it-MTP.gguf 2>&1 | tail -n 3
    echo "  ✓ MTP drafter downloaded"
else
    echo "  ✓ Already exists: gemma-4-12B-it-MTP.gguf"
fi

# --- Gemma 4 12B mmproj (vision projector) ---
echo ""
echo "--- Downloading Gemma 4 12B mmproj (vision) ---"
if [ ! -f "gemma-4-12B-it-mmproj-F16.gguf" ]; then
    wget -q --show-progress \
        "https://huggingface.co/unsloth/gemma-4-12B-it-qat-GGUF/resolve/main/mmproj-F16.gguf" \
        -O gemma-4-12B-it-mmproj-F16.gguf 2>&1 | tail -n 3
    echo "  ✓ mmproj downloaded"
else
    echo "  ✓ Already exists: gemma-4-12B-it-mmproj-F16.gguf"
fi

echo ""
echo "=== Downloads Complete ==="
ls -lh "$MODEL_DIR/"
echo ""
echo "Total model storage: $(du -sh "$MODEL_DIR" | cut -f1)"
