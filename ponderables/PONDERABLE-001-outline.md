# Seymour Publication Format — First Ponderable Structure

## Book Format Spec

| Property | Value |
|----------|-------|
| **Trim size** | 4.25" × 6.875" (rack-friendly digest) |
| **Page count** | 64–96 pages per volume |
| **Interior** | B&W, cream paper |
| **Cover** | Color, 90s clipart front, minimalist back |
| **ISBN** | Per volume, Seymour imprint |
| **Price point** | $7.99–$12.99 |

## Chapter Structure (Each Ponderable)

```
[CLIPART HEADER IMAGE]
━━━━━━━━━━━━━━━━━━━━━━
PONDERABLE #[N]: [TITLE]
━━━━━━━━━━━━━━━━━━━━━━

[1–3 pages of text: essay, allegory, or fictional history]

  ┌─────────────────────────────────┐
  │  "PULL QUOTE" — Character      │
  │  (MGS2 Colonel, Solid Snake,    │
  │   or original Seymour voice)    │
  └─────────────────────────────────┘

[Cross-reference box:]
  ↳ See also: Ponderable #47, "The Doge Protocol"
  ↳ Related: _Seymour's Encyclopedia of Dead Memes_, p. 112

[Footer:]
  Seymour — [Book Title] — Pg. [N]
```

## Series Architecture

### Tier 1: Ponderables (Short Books)
- Standalone 64-page books
- Each covers one meme, concept, or allegorical history
- Numbered sequentially across the series
- Cross-reference each other

### Tier 2: Encyclopedias (Reference)
- Larger format, 200+ pages
- Compiles and expands Ponderable entries
- Alphabetical organization
- Includes "fictional bibliography"

### Tier 3: Novels (Long-form)
- Full-length allegorical fiction
- Characters from Ponderables appear
- The "Seymour Universe"

## First Ponderable: Working Title

**Ponderable #001: "The Mimetic War"**

### Outline

**Opening:** A fictional history of the first meme — not a Dawkins abstraction, but a literal story about the first human who copied another's behavior and passed it on. Set in prehistory. Allegorical.

**Section 1: The Copying Animal**
- What separates humans from other species: not tool use, but imitation
- The saddleback bird parallel (P.F. Jenkins, New Zealand)
- Cultural mutation as evolutionary accelerator

**Section 2: The Meme Pool**
- MGS2 Colonel quote: "In the current, digitized world, trivial information is accumulating every second..."
- The pre-internet era: memes died naturally. Forgetting was a feature.
- The internet changed the death rate of memes to zero.

**Section 3: The 90s Artifact**
- Why clipart? Because it's the last visual language that was *physical*
- Clipart CD-ROMs as meme libraries
- The aesthetic of abundance: 200,000 images, all equally accessible, none curated

**Section 4: The S3 Protocol**
- MGS2 Colonel: "Selection for Societal Sanity"
- Seymour as curator: choosing which memes get preserved in print
- The Ponderable as anti-algorithm

**Closing:** A fictional scene — a character in a future where all digital content has been lost, finding a Seymour Ponderable in a physical library. The only surviving record of a meme that once infected billions of brains.

**Pull quotes to include:**
1. Colonel: "What we propose to do is not to control content, but to create context."
2. Solid Snake: "There's no such thing in the world as absolute reality."
3. Raiden: "I'll pick my own name, and my own life."
4. Original Seymour voice: "Every meme wants to live forever. Most don't deserve to."

## Clipart Sourcing Plan

| Source | Archive.org ID | Size | Status |
|--------|---------------|------|--------|
| ClickArt 200,000 | clickart-200000 | 7.3GB | Downloading |
| Web Clipart 1 | web-clipart-1 | 553MB | Pending |
| Clipart Etc | weirdwithit.clipartetc | ~300MB | Pending |
| 115,000 Clip Art | 115-000-clip-art-images | 2.5GB | Pending |
| Corel WordPerfect 6.1 | corel-word-perfect-suite-6.1 | 1.8GB | Pending |

## Production Pipeline

1. **Download** ISO files from Archive.org
2. **Extract** image files from ISOs
3. **Analyze** each image with Gemma 4 12B vision
4. **Categorize** by subject, style, tone
5. **Select** for each Ponderable based on thematic fit
6. **Layout** in book format (LaTeX or Scribus)
7. **Export** print-ready PDF
8. **Publish** via KDP or IngramSpark
