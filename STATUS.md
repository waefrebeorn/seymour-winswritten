# Seymour Project — Setup & Status

## What's Done

### Research
- ✅ Meme etymology: Full Dawkins lineage documented
- ✅ MGS2 Colonel speech: Core quotes extracted and mapped to Seymour framework
- ✅ S3 Plan → "Selection for Societal Sanity" as philosophical backbone
- ✅ Publication format spec: 4.25"×6.875" digest, 64–96 pages, B&W interior
- ✅ First Ponderable outline: "The Mimetic War" (Ponderable #001)

### Infrastructure
- ✅ llama.cpp built with `llama-mtmd-cli` (vision support)
- ✅ Gemma 4 12B model downloaded (6.3GB, qat-UD-Q4_K_XL quantization)
- ✅ Gemma 4 mmproj downloaded (168MB)
- ✅ Gemma 4 MTP drafter downloaded (822MB)
- ✅ DeepSeek-OCR-2 downloaded (6.3GB safetensors) — NOTE: This is a multi-model VLM checkpoint (Qwen2 backbone + SAM ViT + projector + separate MoE LLM), NOT a simple DeepSeek text model
- ✅ Clipart analysis pipeline script created
- ✅ Project directory structure created
- ✅ GitHub repo pushed: waefrebeorn/seymour-winswritten (main branch)

## What's Pending

### Clipart Downloads (BLOCKED — archive.org timing out)
The ISO downloads from Archive.org are timing out in this session.
**Action needed:** Run the download script manually or in a background session:

```bash
bash /home/wubu/seymour-project/scripts/download-clipart.sh
```

Or download individually:
```bash
cd /home/wubu/seymour-project/clipart/downloads
wget "https://archive.org/download/clickart-200000/ClickArt_200K.iso"
wget "https://archive.org/download/web-clipart-1/Web_Clipart_1.iso"
wget "https://archive.org/download/115-000-clip-art-images/115000_ClipArt_Images.iso"
```

### Vision Pipeline Test
The Gemma 4 12B vision model loads successfully via llama-mtmd-cli.
**Action needed:** Test vision pipeline with:
```bash
echo "Describe this image." | /home/wubu/llama.cpp/build/bin/llama-mtmd-cli \
    -m /home/wubu/seymour-project/models/gemma-4-12B-it-qat-UD-Q4_K_XL.gguf \
    --mmproj /home/wubu/seymour-project/models/gemma-4-12B-it-mmproj-F16.gguf \
    --image /tmp/test-clipart.png -n 256
```

### First Ponderable Writing
**Action needed:** Write the full text of Ponderable #001 "The Mimetic War"
- 64–96 pages
- Mix of essay, allegory, and fictional history
- Include MGS2 Colonel pull quotes
- Reference 90s clipart as visual motif

## Project Structure
```
seymour-project/
├── clipart/
│   ├── downloads/     # ISO files from Archive.org
│   └── analyzed/      # Gemma-analyzed image descriptions
├── models/
│   ├── gemma-4-12B-it-qat-UD-Q4_K_XL.gguf  (6.3GB)
│   ├── gemma-4-12B-it-MTP.gguf              (822MB)
│   ├── gemma-4-12B-it-mmproj-F16.gguf       (168MB)
│   └── deepseek-ocr-2.safetensors            (6.3GB)
├── research/
│   └── seymour-framework.md
├── ponderables/
│   └── PONDERABLE-001-outline.md
└── scripts/
    ├── clipart-pipeline.sh
    └── download-clipart.sh
```

## Key Files
- `research/seymour-framework.md` — Full research document
- `ponderables/PONDERABLE-001-outline.md` — First book outline
- `scripts/clipart-pipeline.sh` — Extract ISOs → analyze with Gemma → categorize
- `scripts/download-clipart.sh` — Download all clipart ISOs
