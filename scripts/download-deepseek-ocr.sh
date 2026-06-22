#!/bin/bash
# DeepSeek-OCR-2 Download Script
# This model is ~6GB in safetensors format

set -euo pipefail

MODEL_DIR="/home/wubu/seymour-project/models"
mkdir -p "$MODEL_DIR/deepseek-ocr-2"
cd "$MODEL_DIR/deepseek-ocr-2"

echo "=== DeepSeek-OCR-2 Downloader ==="
echo "Target: $MODEL_DIR/deepseek-ocr-2/"
echo ""

# Check if huggingface-cli is available
if command -v huggingface-cli &>/dev/null; then
    HF_CMD="huggingface-cli"
elif [ -f "/tmp/seymour-venv/bin/huggingface-cli" ]; then
    HF_CMD="/tmp/seymour-venv/bin/huggingface-cli"
else
    echo "huggingface-cli not found. Installing..."
    python3 -m venv /tmp/seymour-venv 2>/dev/null
    /tmp/seymour-venv/bin/pip install -q huggingface-hub[cli] 2>&1 | tail -n 3
    HF_CMD="/tmp/seymour-venv/bin/huggingface-cli"
fi

echo "Using: $HF_CMD"
echo ""

# Download the model
echo "Downloading DeepSeek-OCR-2 (this is ~6GB)..."
$HF_CMD download \
    --repo-type model \
    --local-dir "$MODEL_DIR/deepseek-ocr-2" \
    --local-dir-use-symlinks False \
    "unsloth/DeepSeek-OCR-2" 2>&1 | tail -n 10

echo ""
echo "=== Download Complete ==="
ls -lh "$MODEL_DIR/deepseek-ocr-2/" 2>/dev/null
echo ""
echo "Total size: $(du -sh "$MODEL_DIR/deepseek-ocr-2" 2>/dev/null | cut -f1)"
