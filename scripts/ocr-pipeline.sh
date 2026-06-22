#!/bin/bash
# DeepSeek-OCR-2 Pipeline for Seymour
# Processes clipart images through OCR to extract text and understand layout

set -euo pipefail

MODEL_DIR="/home/wubu/seymour-project/models"
CLIPART_DIR="/home/wubu/seymour-project/clipart/extracted"
OUTPUT_DIR="/home/wubu/seymour-project/clipart/ocr-results"

mkdir -p "$OUTPUT_DIR"

# Python script for OCR processing
PYTHON_SCRIPT="/home/wubu/seymour-project/scripts/ocr_process.py"

cat > "$PYTHON_SCRIPT" << 'PYEOF'
#!/usr/bin/env python3
"""DeepSeek-OCR-2 processing pipeline for Seymour clipart."""

import os
import sys
import json
import time
from pathlib import Path

def process_image(image_path, model, tokenizer, output_dir):
    """Process a single image through DeepSeek-OCR-2."""
    from PIL import Image
    
    img = Image.open(image_path)
    basename = Path(image_path).stem
    output_file = Path(output_dir) / f"{basename}.json"
    
    if output_file.exists():
        print(f"  Skip (exists): {basename}")
        return
    
    prompt = "<image>\n<|grounding|>Describe this 1990s clipart image. Extract any text visible. Identify the subject, style, and category."
    
    try:
        result = model.infer(
            tokenizer,
            prompt=prompt,
            image_file=str(image_path),
            base_size=1024,
            image_size=768,
            crop_mode=True,
            save_results=False
        )
        
        data = {
            "image": str(image_path),
            "ocr_text": result,
            "timestamp": time.time()
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"  ✓ {basename}: {len(result)} chars")
        
    except Exception as e:
        print(f"  ✗ {basename}: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: ocr_process.py <image_dir> [output_dir]")
        sys.exit(1)
    
    image_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "/home/wubu/seymour-project/clipart/ocr-results"
    
    # Load model (only once)
    print("Loading DeepSeek-OCR-2...")
    from transformers import AutoModel, AutoTokenizer
    import torch
    
    model_name = "deepseek-ai/DeepSeek-OCR-2"
    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    model = AutoModel.from_pretrained(
        model_name,
        _attn_implementation='flash_attention_2',
        trust_remote_code=True,
        use_safetensors=True
    )
    model = model.eval().cuda().to(torch.bfloat16)
    print("Model loaded.")
    
    # Process all images
    image_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tif', '.tiff', '.wmf', '.emf'}
    images = [f for f in Path(image_dir).iterdir() if f.suffix.lower() in image_exts]
    
    print(f"Processing {len(images)} images...")
    
    for i, img_path in enumerate(images):
        print(f"[{i+1}/{len(images)}]", end=" ")
        process_image(str(img_path), model, tokenizer, output_dir)
    
    print(f"\nDone. Results in {output_dir}")

if __name__ == "__main__":
    main()
PYEOF

chmod +x "$PYTHON_SCRIPT"

echo "OCR pipeline script created: $PYTHON_SCRIPT"
echo ""
echo "Usage:"
echo "  bash $0 <clipart_dir>"
echo ""
echo "Or run Python directly:"
echo "  python3 $PYTHON_SCRIPT /path/to/clipart"
