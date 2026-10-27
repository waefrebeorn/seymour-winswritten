# RAW INBOX

_This is the tape deck. Everything lands here first. No editing. No judgment._
_Format: [Timestamp] [ZONE] [Tags] → CONTENT_

---

## 2026-06-24 — Session Start

**[META]** Whiteboard initialized. Taper Room is live.
**[STRUCTURE]** 10-book scaffolding created (Books 1–10, all empty, waiting for captures).
**[META]** User will voice-dictate via Siri → Telegram. I log raw, organize on command.
**[META]** User will send a concept-link for organizational framework later.

---

## 2026-06-24 — Penny Philosophy & Business Model (Siri Voice Dictation)

**[SEED] #penny #book1 #book10 #meta**
"Every book — beginning AND end — I want to bug people to give me pennies."

**[CHUNK] #penny #philosophy #personal**
Wife finds pennies. Mother used to walk into the middle of the street to grab pennies. Mother had the mind of a 14-year-old almost all the time. Running into the street was dangerous. Mother died of diabetes. Now pennies are gone forever. I collect pennies. I have pennies. This gives me a recollection thought of the past — how we used to have wheat pennies, then wheat pennies stopped being a thing, now pennies are gonna stop being a thing, and eventually maybe someday nickels will stop being a thing.

**[SPARK] #penny #philosophy #grim-reaper**
This leeches into what I was really thinking. I feel like I am a Grim Reaper for a lot of technologies. I have witnessed a lot of careers: stabilize, stagnate, and die. As I get older, I feel less of a consumer of content — I have witnessed other consumers of content be recognized as creators of content.

**[STRUCTURE] #business-model #github #patreon**
GitHub = non-compiled version of the book (open source). PDF sold for $0.99 per book. OR Patreon $10/month for all books. OR $1/month = support YouTube channel + link to locked set of 25 "best of" books.

**[SPARK] #business-model #winrar #open-source**
Open source GitHub — people can compile their own books for free. Similar to WINRAR model: software that was super really good, successful. "Try before you buy" philosophy. Low barrier to entry.

**[META] #meta #siri #workflow**
NOTE: User is using Siri Text-to-Speech → dictating to me. I need to be focused on capturing Siri speech-to-text accurately. Will need to parse and clean up transcription artifacts in real-time.

**[CHUNK] #penny-philosophy #EV #battery #supercapacitor #driving #economics**
Driving to/from work: 1.5 hours, 40 MPG, 2019 Nissan Versa, gas ~$3.90-4.00/gal = ~10 miles per dollar.

Comparing this economy to: Uber, DoorDash delivery, Gopuff, myself as courier. Mindful of the economics of driving.

Didn't buy an electric car because: battery deterioration costs tens of thousands. Waiting for battery tech to catch up on: fast charging, stable charging cycle, range matching gasoline. Confusing to research: supercapacitors, charging dynamic capacitors, pre-charge problem in automotive. Why isn't supercapacitor used in tandem with battery + small gas generator?
- High mileage + low mileage situations
- Supercapacitor handles lifecycle
- Battery handles long cycle
- Emergency cycle: small generator (1-2 HP)
- Replaceable components, cheap and easy
- Sticking to "battery only" + cooling is shortsighted

**[SPARK] #transcription #speech-to-text #future-tech #workflow**
Future research: newest transcription models that use less resources + work faster → more accurate faster workflows. Effort to put in is significant.
- 10 books for Volume 1 = precedent
- Could be thousands of volumes with 10-book series
- Editorial mixture: buy one, buy a set, get one free while you poop
- Reading on phone, bathroom book, shelf book

**[CHUNK] #personal #childhood #foster-care #gary-paulsen #uncle-johns**
Childhood: read ~100 Gary Paulsen books (didn't read all, but from a challenge or being grounded — devices taken away by foster parent). Finished Uncle John's Ponderables series. Hatchet by Gary Paulsen.

Wife knows all the details about my life. Will slowly give more context. Peculiar life.

**[STRUCTURE] #infrastructure #youtube #context-pipeline**
YouTube Context Pipeline BUILT and RUN:
- `scripts/youtube-extract.py` → Pulls auto-generated captions from all channel videos
- Results: 10/12 successful, **137,766 words** of transcript context
- Games played: Poppy Playtime Ch5 (all 5 parts), Psychonauts 2 (full + part 1)
- Shorts also captured (reaction clips)
- `scripts/gemini-summarize.py` → AI summaries via Gemini 2.0 Flash
- Output: `whiteboard/youtube-context/` (raw .txt + metadata index)
- **KNOWN ISSUE:** YouTube categorization is broken — live streams are filed under "Videos" instead of "Live" tab. Channel has 470 videos total but only ~38 visible in "Videos" tab. Need to resolve the categorization issue or use browser absorbing to get all 470 IDs.
- This is now the KNOWLEDGE BASE for understanding: what games you play, your streaming
  personality, reactions, humor style, topics that come up organically

**[STRUCTURE] #infrastructure #dns #domain**
Domain: `waefrebeorn.com` — uses 501 redirect pattern by subdomain.
- `bytropix.waefrebeorn.com` → GitHub Pages (bytropix inference engine repo)
- `vod.waefrebeorn.com` → YouTube (WaefreBeorn / @WuBuStreams channel)
- Pattern: `{concept}.waefrebeorn.com` → redirect to correct platform
- Planned subdomains for Seymour: `seymour`, `shop`, `live`, `twitch`, `www`, `github`, `patreon`

---

## Instructions for Capture

When you send me something, I will:
1. Log it here in RAW INBOX with timestamp + zone + tags
2. Confirm what I logged (so you know I heard you)
3. When you say "organize" — I process captures into `whiteboard/organized/`
4. When you say "status" — I show capture counts and book fill levels
5. When you say "draft [book#]" — I compile captures into entry drafts

**Ready for input. Start talking.**