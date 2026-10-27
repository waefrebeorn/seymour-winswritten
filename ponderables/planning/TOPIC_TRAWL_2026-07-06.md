# Trawl Results — Stream Transcript Topic Mining

**Date:** 2026-07-06
**Corpus:** 592 normalized transcript files (`ponderables/normalized_transcripts/`), 408 indexed videos (`pre_seymour/index_with_topics.json`)
**Method:** Regex motif scan on cleaned transcripts (timestamps/music/applause stripped), topic-frequency from index

---

## Slop-Score Filter (what we KILL)

**Gaming noise (excluded from topic pool):**
Gaming (48 vids), Video Games (34), Marvel Rivals (26+17), Let's Play (29), Horror Games (13+6), Death Stranding (12+3), Red Dead 2 (7), RoboCop (5), Schedule I (4), FNAF (4), Fortnite/Minecraft/Roblox/CoD/TF2 (4 each), Apex, Smash, Battle Royale, Poppy Playtime, Dark Deception, Tomodachi Life, Secret of the Mimic.

→ These dominate the index (870 unique topics, ~50% gaming) but are NOT Ponderables material. Filter them.

**Noise topic patterns:** gaming|video game|marvel rivals|let's play|gameplay|fortnite|minecraft|roblox|call of duty|team fortress|pokemon|fnaf|five nights|horror game|action-adventure|red dead|death stranding|robo|schedule i|apex|smash|esports|ranked|battle royale|poppy playtime|dark deception|tomodachi|superhero|secret of the mimic

---

## Candidate Topic Pool (ranked by file coverage)

| Rank | Theme | Files | Matches | Bathroom Potential |
|------|-------|-------|---------|-------------------|
| 1 | God/Tech Agnosticism | 486 | 29494 | 🟡 High freq but mostly "oh my god" filler — need real theology snippets |
| 2 | Dogs/Pets | 380 | 8979 | 🟢 Strong — pet stories, Taco Bell dogs motif exists |
| 3 | Alcohol/Bar | 345 | 7245 | 🟢 "I don't drink but I go to bars" — contradiction angle |
| 4 | Real Estate/Housing | 342 | 5709 | 🟢 Mom's house, renting, property — class anxiety |
| 5 | Music/Making | 341 | 5235 | 🟢 Guitar/piano/song — creative process |
| 6 | Smoking/Vaping | 306 | 4839 | 🟢 "autistically staring at screen smoking" — self-awareness |
| 7 | Penny/Coin Obsession | 303 | 4128 | 🟢 ALREADY DONE (Vol 1) — sequel potential |
| 8 | Postal/Mail | 287 | 3798 | 🟢 Package/FedEx/letter — mundane obsession |
| 9 | Mom Stories | 262 | 2553 | 🟢 ALREADY SEEN in Vol 1 drafts — rich |
| 10 | Garden/Growing | 258 | 2721 | 🟡 "grow your vector region by 27" — mixed signal |
| 11 | AI/GPU | 143 | 1581 | 🟢 ALREADY DONE (CUDA) — expand to LLM/AGI takes |
| 12 | Grandma Stories | 115 | 867 | 🟢 Heritage, recipes, funeral — generational |
| 13 | Neighbor Drama | 109 | 648 | 🟢 "neighbor who went to jail" — slice of life |
| 14 | Coffee Rituals | 108 | 1050 | 🟢 "80% sweet cream 2% coffee" — ritual comedy |
| 15 | Childhood Memories | 105 | 522 | 🟢 Grew up / elementary school — nostalgia |
| 16 | Prepper/Bunker | 78 | 405 | 🟢 Survival/zombie/supercapacitor link — ALREADY DONE (supercap) |
| 17 | Crypto Brain Rot | 77 | 615 | 🟢 "Dogecoin", "web 3 man" — skepticism angle |
| 18 | Old Tech Nostalgia | 50 | 288 | 🟢 VHS cleaning kits, Windows XP, CD-ROM — GEN X nostalgia |
| 19 | Taco Bell Theology | 39 | 186 | 🟢 ALREADY IN Vol 1 drafts — "who will survive: my body or Taco Bell" |
| 20 | Conspiracy | 33 | 183 | 🟡 Low signal, mostly jokes |

---

## Top 10 Next Topics to Draft (Vol 2 candidates)

1. **The Dog That Ate Taco Bell** — Pets + food crossover. "Taco Bell dogs" motif.
2. **I Don't Drink But I Live at the Bar** — Alcohol contradiction, social anxiety.
3. **Mom's House, Forever** — Real estate, dependency, FedEx shipments.
4. **The Guitar I Bought and Never Played** — Music, aspiration vs reality.
5. **VHS Cleaning Kits in the Year 2025** — Old tech nostalgia, Gen X time warp.
6. **Grandma's Recipe for Everything (Including War Crimes)** — Heritage, food, irony.
7. **The Neighbor Who Went to Jail** — Slice of life, landlord drama.
8. **80% Sweet Cream, 2% Coffee** — Coffee rituals, ADHD fuel.
9. **Dogecoin and the Death of Money** — Crypto skepticism, "web 3 man."
10. **The Package That Never Came** — Postal/mail obsession, waiting as lifestyle.

---

## Verification Notes

- "Supercapacitor" = 0 transcript hits (confirmed speculation, as flagged in TDA audit)
- "Hatchet/Paulsen" = 6 files (low but real — confirms book is a motif, not frequent)
- "Versa" = 5 files (mostly gaming chatter false-positive; need manual confirm)
- "CUDA/GPU" = 70 files (strong — real technical content)

## Next Action

For each candidate: pull 3-5 representative transcript snippets, run TDA audit, generate 25 perspectives, convert to Uncle John entry. Target: 10 entries for Vol 2.
