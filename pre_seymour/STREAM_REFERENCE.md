# Seymour Wins Written — Streamer's Reference
*Generated from Pre-Seymour Era (297 videos, 2.55M words)*

---

## QUICK CALLBACKS (Top 20)

| Topic | Quote | Video |
|-------|-------|-------|
| **bytropix** | *Search: `seymour-pre bytropix -n 1`* | — |
| **Nissan Versa / EV hybrid** | *Search: `seymour-pre "nissan versa" -n 1`* | — |
| **Gary Paulsen / Hatchet** | *Search: `seymour-pre "gary paulsen" -n 1`* | — |
| **Pennies (mom/wife)** | *Search: `seymour-pre pennies -n 1`* | — |
| **Foster childhood** | *Search: `seymour-pre foster -n 1`* | — |
| **RTX 4050 / GPU MODE** | *Search: `seymour-pre "4050" -n 1`* | — |
| **Godot engine** | *Search: `seymour-pre godot -n 1`* | — |
| **CUDA kernels** | *Search: `seymour-pre cuda -n 1`* | — |
| **WuBu Nesting / hyperbolic** | *Search: `seymour-pre wubu -n 1`* | — |
| **Seymour Ponderables** | *Search: `seymour-pre ponderable -n 1`* | — |

---

## ERA BREAKDOWN

| Era | Videos | Years | Key Themes |
|-----|--------|-------|------------|
| **Foundations** | 67 | 2023 | Strongbad, Trogdor, early streams, DNSL, Mario Movie, Roblox announcements |
| **Deep Dives** | 30 | 2024 | Death Stranding, Poppy Playtime, Subnautica, Marvel Rivals S1-4, TABLE TIME |
| **Hiatus Prep** | 153 | 2025 | Marvel Rivals S5-S25, Death Stranding 2, Poppy Playtime Ch3-5, TF2 MvM, FNAF, Red Dead 2, RoboCop, Killer Frequency, Homestar Runner |
| **Absorption** | 8 | 2026 | C11 pipeline, whisper absorption, Seymour project build |

**Total: 297 videos | 2.55M words**

---

## STREAMING WORKFLOW

### During "Seymour Wins Written" streams:

```bash
# Quick callback for any topic
seymour-pre "topic" -n 1

# Era-filtered search
seymour-pre "cuda" --era 2025

# Source-filtered (c11 = cleaner timestamps, whisper = full coverage)
seymour-pre "godot" --source c11

# Random callback for filler
seymour-pre --random -n 1

# Stats overview
seymour-pre --stats

# List all eras
seymour-pre --eras
```

---

## QUOTE BANK (quotes.md — 200 quotes)

Categories by keyword:
- **None** (79) — raw/unclassified
- **pret** (47) — pretentious/philosophical
- **fal** (14) — Fallout/failure
- **attention** (10) — meta commentary
- **mother** (10) — family/mother references
- **lora** (8) — LoRA/training
- **memory** (5) — memory/recall

---

## KEY VIDEO SERIES (by frequency)

| Series | Videos | Era |
|--------|--------|-----|
| Marvel Rivals | ~40+ | 2024-2026 |
| Death Stranding | ~20+ | 2024-2025 |
| Poppy Playtime | ~15+ | 2024-2025 |
| TABLE TIME | ~10+ | 2024-2025 |
| FNAF Security Breach | ~8+ | 2026 |
| Red Dead Redemption 2 | ~8+ | 2025 |
| RoboCop Rogue City | ~6+ | 2025 |
| TF2 MvM | ~5+ | 2022/2025 |
| Homestar Runner | ~5+ | 2023/2025 |

---

## PERSONAL LORE (for callbacks)

- **Commute:** 1.5hr each way, 2019 Nissan Versa, 40 MPG, gas ~$3.90/gal = ~10 mi/$
- **EV idea:** Supercapacitor + battery + small gas generator hybrid
- **Childhood:** Foster parent took devices → read ~100 Gary Paulsen books (Hatchet)
- **Mother:** Ran into streets for pennies (deceased, diabetes)
- **Wife:** Finds pennies (penny motif)
- **GPU:** RTX 4050 Laptop (6140 MiB, 5073 MiB free)
- **Models:** Gemma-4-12B qat-UD-Q4_K_XL (6.3GB), Gemma-4 mmproj (168MB)
- **Inference:** llama-server port 18802, ~7 tok/s

---

## PIPELINE STATUS (for transparency)

| Pipeline | Status | Coverage |
|----------|--------|----------|
| **C11 CDP** | ✅ Complete | 104 transcripts (engagement panel) |
| **Whisper CPU** | 🟢 Running | 150/187 done, 28 remaining, 9 failed |
| **Index** | ✅ Built | 297 videos, 2.55M words |
| **Topics** | 🔄 Ready to run | `python3 scripts/topic_tagger.py` |
| **Quote Bank** | ✅ Ready | 200 quotes in quotes.md |

---

## NEXT STEPS (when pipeline finishes)

1. **Retry failed videos** (9 videos) — create retry list and re-run whisper
2. **Re-run index builder** — `python3 build_pre_seymour_index.py`
3. **Run topic tagger** — `python3 scripts/topic_tagger.py` (adds LLM topics to index)
4. **Verify CLI** — `seymour-pre "test" -n 3`

---

*Last updated: 2026-07-04 | Whisper: 150/187 | Index: 297 vids | LLM: Gemma-4-12B local*