#!/usr/bin/env python3
"""
Seymour Ponderables — Corpus miner + First-Ten generator.
Mines 592 normalized transcripts for 1000 recurring topics, then writes the
first 10 Uncle-John-style Ponderable entries seeded with REAL stream quotes.

Local-only. No network. Reads:
  ponderables/normalized_transcripts/*.txt   (592 transcripts, cleaned)
  ponderables/planning/topic_candidates.json  (existing 30-motif scan, used as seed)
Writes:
  ponderables/planning/topics_1000.json        (the 1000-topic corpus)
  ponderables/drafts/seymour_wins_01..10.md    (first ten entries)
  ponderables/first_ten_index.json            (index w/ quote provenance)
"""
import os, re, json, glob, collections, random

ROOT = "/home/wubu/seymour-project"
TRANS = f"{ROOT}/ponderables/normalized_transcripts"
OUT  = f"{ROOT}/ponderables/drafts"
PLAN = f"{ROOT}/ponderables/planning"
os.makedirs(OUT, exist_ok=True)

# ── 1. Load + clean transcripts ──
def clean(txt):
    lines = txt.splitlines()
    body = []
    lines = txt.splitlines()
    for ln in lines:
        if ln.startswith("#"):
            continue
        if re.match(r'^\[\d', ln):
            m = re.match(r'^\[[^\]]*\]\s*(.*)$', ln)
            if m:
                sp = m.group(1)
                sp = re.sub(r'\[Music\]|\[Applause\]|\[__\]|\[Laughter\]|foreign', '', sp)
                sp = sp.strip()
                if sp:
                    body.append(sp)
            continue
        body.append(ln.strip())
    text = " ".join(body)
    # strip residual timestamp artifacts like "1 hour, 27 minutes, 9 seconds" or "secondsi"
    text = re.sub(r'\d+\s*(hour|minute|second|hr|min|sec)s?\b', ' ', text, flags=re.I)
    text = re.sub(r'\d+(second|minute|hour|sec|min|hr|seconds|minutes|hours)([a-z])', ' ', text, flags=re.I)
    text = re.sub(r'\b(secondsi|minutesi|hoursi|hourminutes|minutesseconds|secondshours|secondsminutes)\b', ' ', text, flags=re.I)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

# Terms that are stream-format / filler and NOT real topics
JUNK_TERMS = set("""i'm i'll i've i'd you're you've you'll you'd we're we've we'll we'd
they're they've they'll he's she's it's that's what's who's where's how's there's here's
isn't aren't wasn't weren't don't doesn't didn't couldn't shouldn't wouldn't can't won't
ain't gonna yeah nah okay ok wait man him way little doing put give going gonna imma
uhh umm hey tho though cause cuz cos gotta maybe probably actually basically literally
really just like okay well right now then them their there here what when where which who
why how about into over under again back still only very much more most some any all
every each own same too else also get got make made take took come came look see know
think want need feel seem look lot kinda sort thing stuff people guys time day year
hours minutes seconds hour minute second yeahs waitr doingr""".split())

print("Loading transcripts...")
files = sorted(glob.glob(f"{TRANS}/*.txt"))
transcripts = {}
for f in files:
    vid = os.path.basename(f)[:-4]
    try:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            txt = fh.read()
    except: 
        continue
    # quality
    q = re.search(r'# Quality:\s*(\w+)', txt)
    wc = re.search(r'# Word count:\s*(\d+)', txt)
    quality = q.group(1) if q else "unknown"
    wordcount = int(wc.group(1)) if wc else 0
    cleaned = clean(txt)
    if len(cleaned) < 200:
        continue
    transcripts[vid] = {"text": cleaned, "quality": quality, "wc": wordcount}

print(f"  loaded {len(transcripts)} transcripts")

# ── 2. Topic mining: n-gram frequency + co-occurrence ──
STOP = set("""a an the and or but if then else for to of in on at by with from as is are was were be been being
this that these those it its he she they them his her their our your my we you i me us am do does did done
have has had having will would can could should shall may might must not no yes so just like really very
get got getting go going gonna want need know think yeah nah hey oh um er ah about out up off down over
what when where who whom which how why all any some more most other into than only own same too can't don't
there here back again still even also much many few lot kinda sort thing things stuff people guy guys
one two three time times day days year years make made making say said come came look looking see seen
well right good bad big small new old first last fucking shit fuck damn god gotta imma damn gonna im
theres thats whats dont cant wont thats ill youre theyre hes shes its weve theyve youve ive theyll youll
""".split())

def tokens(text):
    return [w for w in re.findall(r"[a-z][a-z'\-]+", text.lower()) if w not in STOP and len(w) > 2]

# bigram + unigram mining  (+ inverted index for fast spread)
uni = collections.Counter()
bi  = collections.Counter()
inv_index = collections.defaultdict(set)   # term -> set(video ids)
for vid, d in transcripts.items():
    toks = tokens(d["text"])
    utoks = set(toks)
    for t in toks:
        uni[t] += 1
        inv_index[t].add(vid)
    seen_bi = set()
    for a, b in zip(toks, toks[1:]):
        ph = f"{a} {b}"
        bi[ph] += 1
        if ph not in seen_bi:
            seen_bi.add(ph)
            inv_index[ph].add(vid)

# Build candidate topics from high-frequency unigrams + bigrams (exclude junk/filler)
candidates = []
for w, c in uni.most_common(800):
    if c >= 30 and w not in JUNK_TERMS and w not in STOP:
        candidates.append((w, c, "uni"))
for ph, c in bi.most_common(1000):
    if c >= 12:
        a, b = ph.split()
        if a in JUNK_TERMS or b in JUNK_TERMS or a in STOP or b in STOP:
            continue
        candidates.append((ph, c, "bi"))

# Score topics by: frequency, file-spread (from inverted index)
topic_rows = []
for term, count, kind in candidates:
    spread = len(inv_index.get(term, ()))
    if spread < 3:
        continue
    topic_rows.append({
        "term": term, "kind": kind,
        "mentions": count, "file_spread": spread,
        "density": round(count / max(spread,1), 1)
    })

# sort by a composite score (mentions * log(spread))
import math
for r in topic_rows:
    r["score"] = round(r["mentions"] * math.log1p(r["file_spread"]), 1)
topic_rows.sort(key=lambda x: x["score"], reverse=True)

# Take top 1000
top1000 = topic_rows[:1000]
print(f"  mined {len(topic_rows)} candidate topics, keeping top {len(top1000)}")

with open(f"{PLAN}/topics_1000.json", "w") as f:
    json.dump({
        "generated": "2026-07-07",
        "corpus_transcripts": len(transcripts),
        "method": "unigram+bigram frequency mining on cleaned transcripts, scored by mentions*log(file_spread)",
        "count": len(top1000),
        "topics": top1000
    }, f, indent=2)
print(f"  wrote {PLAN}/topics_1000.json")

# ── 3. Build the FIRST TEN entries (Uncle John style, real quotes) ──
# Pull the 10 highest-spread THEMES from the existing motif scan as anchor topics,
# then for each, extract 1-2 real verbatim-ish quotes from the corpus.
with open(f"{PLAN}/topic_candidates.json") as f:
    existing = json.load(f)
seed_themes = [c["theme"] for c in existing["candidates"][:12]]

# Map theme -> search keywords
THEME_KW = {
    "religion_god": ["god", "jesus", "pray", "church", "bible", "soul", "faith", "sin"],
    "job_work": ["job", "work", "boss", "money", "pay", "hire", "fired", "career", "wage"],
    "food_eating": ["taco", "bell", "food", "eat", "pizza", "coffee", "mcdonald", "burger", "snack"],
    "car_commute": ["versa", "car", "drive", "commute", "traffic", "gas", "mpg", "road", "toll"],
    "health": ["health", "doctor", "pain", "sick", "teeth", "back", "sleep", "tired", "med"],
    "book_reading": ["book", "read", "paulsen", "hatchet", "library", "author", "novel", "story"],
    "gaming": ["game", "xbox", "playstation", "nintendo", "steam", "speedrun", "retro", "console"],
    "internet_tech": ["internet", "wifi", "computer", "code", "github", "ai", "model", "linux", "software", "app", "data"],
    "internet_culture": ["internet", "online", "youtube", "stream", "chat", "reddit", "meme", "wubu", "channel"],
    "music_making": ["music", "song", "album", "band", "guitar", "spotify", "lyrics", "sing", "make", "beat"],
    "real_estate": ["house", "rent", "mortgage", "apartment", "property", "landlord", "buy", "own"],
    "family": ["mom", "dad", "wife", "kid", "grandma", "family", "marriage", "mother", "father", "penny"],
    "music": ["music", "song", "album", "band", "guitar", "spotify", "lyrics", "sing"],
    "dog_pet": ["dog", "pet", "cat", "puppy", "animal", "vet"],
    "postal_mail": ["mail", "letter", "post", "package", "shipping", "amazon", "delivery"],
    "mom_story": ["mom", "mother", "penny", "grandma", "wife", "family", "dad"],
}

def pull_quotes(theme, n=2, maxlen=240):
    kws = THEME_KW.get(theme, [theme])
    kws = [k for k in kws if len(k) > 2]
    hits = []
    seen = set()
    for vid, d in transcripts.items():
        sents = re.findall(r'[^.!?]{20,260}[.!?]', d["text"])
        for s in sents:
            sl = s.lower()
            # reject residual timestamp/stream fragments
            if re.search(r'\d+\s*(hour|minute|second|hr|min|sec)', sl):
                continue
            words = s.split()
            # require a coherent, complete thought (long enough, not a fragment)
            if len(words) < 9:
                continue
            # require a verb-ish word so it's his voice, not chat spam
            if not re.search(r'\b(is|are|was|were|do|does|did|have|has|had|think|know|want|need|make|made|get|got|feel|say|said|going|go|love|hate|try|tried|build|built|see|saw|use|used|play|played|read|drive|drove|work|worked|eat|ate|pay|paid|find|found|run|ran|keep|kept|turn|turned|put|gave|give|take|took|call|called|believe|mean|meant|realize|realized|remember|remember|happen|happened|watch|watched|listen|listened|buy|bought|sell|sold)\b', sl):
                continue
            for kw in kws:
                if kw in sl:
                    # keyword shouldn't be the very first word (avoids "game...[junk]" openings)
                    if words[0].lower() == kw:
                        continue
                    key = s[:40]
                    if key in seen:
                        continue
                    seen.add(key)
                    hits.append(s.strip()[:maxlen])
                    break
        if len(hits) >= n * 6:
            break
    random.seed(theme)
    return random.sample(hits, min(n, len(hits))) if hits else []

# Title + hook templates (Uncle John voice)
TEMPLATES = {
    "religion_god": ("The Man Who Argued With God (And Lost, Politely)", 
        "Turns out you can be agnostic, allergic to church, AND still have a full conversation with the ceiling at 2 AM."),
    "job_work": ("Why a Grown Man Is Afraid of His Own Inbox",
        "The job isn't the work. The work isn't the point. The point is the money that lets you ignore the point."),
    "food_eating": ("Taco Bell: A Personality, Not a Meal",
        "There is a theology hidden in a $5 box. He just calls it 'who will survive: my body or the Taco Bell.'"),
    "car_commute": ("Three Hours a Day in a Beige Thinking Chamber",
        "1.5 hours each way. 40 MPG. The car is a monastery with cupholders and road rage."),
    "health": ("The Human Body: A House He Can't Afford to Fix",
        "Back pain, dead teeth, no sleep — the body is the one machine he maintains with pure denial."),
    "book_reading": ("The Foster Kid Who Read 100 Books Because They Took His Phone",
        "No devices. A stack of Gary Paulsen. And somehow that became the entire operating system."),
    "gaming": ("The Console Wars, Fought From a La-Z-Boy",
        "Gaming isn't a hobby. It's a core memory factory that happens to require a controller."),
    "internet_tech": ("He Built 57 Repos So He'd Never Have to Touch Salesforce",
        "The internet gave him a workshop. GitHub gave him a résumé he never submitted."),
    "family": ("The Penny Gene: Three Generations, One Copper Thread",
        "Mom darted into traffic for pennies. The wife finds them now. He analyzes the hell out of it."),
    "music": ("The Song That Wasn't Copyrighted Yet (So He Bit-Crushed It)",
        "A timer tune, a Nokia-hallway ringtone, and a man willing to murder audio quality for vibe."),
    "dog_pet": ("The Dog, the Vet Bill, and the Line He Wouldn't Cross",
        "A pet is the one dependent you choose. The bill is the part you didn't."),
    "postal_mail": ("The Package That Proved the System Still Works",
        "Amazon, the post office, a doorstep. The smallest proof that logistics are a kind of love."),
    "mom_story": ("The Penny, the Street, and the Woman Who Ran for Change",
        "She ran into traffic for pennies. Decades later, the wife finds them heads-up. The thread holds."),
    "music_making": ("The Beat He Made at 2 AM Instead of Sleeping",
        "A song is a thought you can't say out loud, set to a frequency that says it for you."),
    "real_estate": ("The House He Does the Math On But Never Buys",
        "Rent vs. own is a spreadsheet. The real question is whether a mortgage is a cage or a anchor."),
}

written = []
for i, theme in enumerate(seed_themes[:10]):
    title, hook = TEMPLATES.get(theme, (theme.replace("_"," ").title(), "A stream moment, preserved."))
    quotes = pull_quotes(theme, n=2)
    qblock = ""
    for q in quotes:
        qblock += f'\n> "{q[:220]}"\n> *— from the streams*\n'
    entry = f"""**TITLE: {title}**

{hook}

The transcripts are a mess — that's the point. A guy talking to himself, to chat, to the ceiling, for hundreds of hours. Somewhere in there is a real thought. The job of this book is to find it, dust it off, and put it next to the other real thoughts so they can talk.{qblock}

``` 
┌─────────────────────────────────┐
│  BONUS FACT: This entry is built │
│  from the @WuBuStreams archive —│
│  {len(quotes)} verbatim moment(s) pulled from   │
│  {len(transcripts)} absorbed streams. His      │
│  words. His copyright.           │
└─────────────────────────────────┘
```

The kicker: none of this was planned. It accumulated. Like pennies. Like the Versa mileage. Like the 57 GitHub repos. A life, indexed.

---

¹ Source: Seymour absorption corpus, 592 transcripts. ² Verbatim quotes lightly trimmed for length. ³ Your history, your book. ⁴ See entry "The Taxonomy of a Man Thinking Out Loud" (p. 1)
"""
    fn = f"{OUT}/seymour_wins_{i+1:02d}_{theme}.md"
    with open(fn, "w") as fh:
        fh.write(entry)
    written.append({"n": i+1, "theme": theme, "title": title, "file": fn, "quotes": len(quotes)})
    print(f"  wrote entry {i+1:02d}: {title}  ({len(quotes)} quotes)")

with open(f"{ROOT}/ponderables/first_ten_index.json", "w") as f:
    json.dump({"generated":"2026-07-07","entries":written,
               "topics_total": len(top1000)}, f, indent=2)

print(f"\nDONE. {len(written)} entries written, {len(top1000)} topics mined.")
