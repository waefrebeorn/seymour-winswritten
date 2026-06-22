# Seymour — Ponderables Publication Project

## What Is Seymour?

Seymour is a pen name and publishing imprint for a series of small-format books that ponder memes, their effects, and their fictional histories through allegory. The project exists to separate this creative work from the author's academic and online profile.

## The Format

- **Trim size:** 4.25" × 6.875" (rack-friendly digest)
- **Page count:** 64–96 pages per volume
- **Interior:** B&W, cream paper, 90s clipart illustrations
- **Cover:** Color, 90s clipart front
- **Price:** $7.99–$12.99
- **Distribution:** Amazon KDP, IngramSpark

## The Framework

Each Ponderable is a self-contained essay/allegory about a meme, concept, or cultural phenomenon. They cross-reference each other and build into a larger fictional universe — the Seymourverse.

The philosophical backbone comes from MGS2's Colonel AI speech:
> "What we propose to do is not to control content, but to create context."

Seymour curates. Seymour frames. Seymour doesn't censor — Seymour selects.

## The Models

| Model | File | Size | Purpose |
|-------|------|------|---------|
| Gemma 4 12B QAT | gemma-4-12B-it-qat-UD-Q4_K_XL.gguf | 6.72GB | Main inference, vision, reasoning |
| Gemma 4 MTP | gemma-4-12B-it-MTP.gguf | ~465MB | Speculative decoding drafter |
| Gemma 4 mmproj | gemma-4-12B-it-mmproj-F16.gguf | ~815MB | Vision projector |
| DeepSeek-OCR-2 | (safetensors) | ~6GB | OCR, document parsing, clipart text extraction |

## The Pipeline

1. **Source:** 90s clipart CD-ROMs from Archive.org
2. **Extract:** Mount ISOs, extract image files
3. **Understand:** Gemma 4 vision analyzes each image → subject, style, category, tone
4. **OCR:** DeepSeek-OCR-2 extracts any text from clipart
5. **Select:** Match clipart to Ponderable themes
6. **Layout:** LaTeX or Scribus for print-ready PDF
7. **Publish:** KDP

## Project Structure

```
seymour-project/
├── clipart/
│   ├── downloads/          # ISO files from Archive.org
│   ├── extracted/          # Extracted image files
│   └── analyzed/           # Gemma-analyzed descriptions (JSON)
├── models/                 # GGUF and safetensor models
├── research/
│   ├── seymour-framework.md    # Philosophy, MGS2 quotes, memetics
│   └── meme-etymology.md       # Academic foundations
├── ponderables/
│   ├── PONDERABLE-001/
│   │   ├── outline.md
│   │   ├── draft.md
│   │   └── clipart/        # Selected images for this volume
│   ├── PONDERABLE-002/
│   └── ...
├── encyclopedia/           # Cross-reference index
├── scripts/
│   ├── download-models.sh
│   ├── download-clipart.sh
│   ├── clipart-pipeline.sh
│   └── ocr-pipeline.sh
└── STATUS.md
```

## Daily Workflow

The author drives, thinks, and voice-dictates contributions via Siri → Telegram → Hermes. Each contribution is a seed for a Ponderable entry. Over time, seeds grow into full chapters.

### Contribution Format
```
[PONDERABLE # or NEW]
[TOPIC]
[TEXT — essay fragment, allegory, observation, reference]
[CLIPART REQUEST: what kind of image would fit]
[PULL QUOTE: if applicable]
```

## First Ponderable: "The Mimetic War"

**Outline:**
1. The Copying Animal — what separates humans: imitation
2. The Meme Pool — pre-internet, memes died naturally
3. The 90s Artifact — clipart as last physical visual language
4. The S3 Protocol — curation as selection for societal sanity
5. The Future Archaeologist — finding a Ponderable after digital collapse

**Key pull quotes:**
- Colonel: "What we propose to do is not to control content, but to create context."
- Colonel: "Just as in genetics, unnecessary information and memory must be filtered out to stimulate the evolution of the species."
- Solid Snake: "There's no such thing in the world as absolute reality."
- Raiden: "I'll pick my own name, and my own life. I'll find something worth passing on."
