#!/usr/bin/env python3
"""seymour_deep_perspective.py — Rebuilt multi-perspective engine with real data.

Triple Devil's Advocate methodology:
  Pass 1: Data ingestion — search pre_seymour index for RELEVANT transcript excerpts
  Pass 2: Structural — build writer's room with personas that RESPOND to each other
  Pass 3: Adversarial — audit output for gaps, contradictions, missed insights

Usage:
  python3 seymour_deep_perspective.py --topic "pennies"    # Single topic deep dive
  python3 seymour_deep_perspective.py --all                 # All deep topics
  python3 seymour_deep_perspective.py --tda                 # Triple DA audit pass only
"""
import json, os, sys, re, urllib.request, urllib.error
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
GEMMA_PORT = 18802
QWEN_PORT   = 18803
BASE        = Path("/home/wubu/seymour-project")
INDEX_FILE  = BASE / "pre_seymour" / "index.json"
OUT_DIR     = BASE / "ponderables" / "drafts"
TRANSCRIPT_DIR = BASE / "whiteboard" / "seymour-pipe" / "whisper_transcripts"
C11_DIR     = BASE / "absorption" / "data" / "transcripts"
QUOTES_FILE = BASE / "pre_seymour" / "quotes.json"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Load index ──────────────────────────────────────────────────────────
def load_index():
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text())
    return {}

# ── Search transcripts for relevant excerpts ────────────────────────────
GAMING_NOISE = {"penny", "pennies", "rock", "rockin", "domination", "lotto", "goddamn",
                "pull", "fuckin", "lame", "judging", "shitty", "trillion", "menu",
                "technician", "alarm", "upgrade", "bridge", "truck", "ice",
                "capture", "spawn", "kill", "enemy", "team", "player", "round",
                "mission", "objective", "weapon", "ammo", "shield", "health"}

def search_transcripts(query, max_excerpts=5, context_chars=250):
    """Search the Seymour corpus for real spoken content. 
    Returns ranked snippets with relevance scoring to prefer personal topics over gaming chatter."""
    query_lower = query.lower()
    terms = query_lower.split()
    matches = []
    
    for sdir in [TRANSCRIPT_DIR, C11_DIR]:
        if not sdir.exists():
            continue
        for fpath in sorted(sdir.glob("*.txt"))[:300]:
            try:
                text = fpath.read_text(errors="replace")
                text_lower = text.lower()
                best_pos = -1
                for term in terms:
                    pos = text_lower.find(term)
                    if pos >= 0 and (best_pos < 0 or pos < best_pos):
                        best_pos = pos
                if best_pos >= 0:
                    start = max(0, best_pos - context_chars // 2)
                    end = min(len(text), best_pos + len(terms[0]) + context_chars // 2)
                    excerpt = text[start:end].strip()
                    excerpt = re.sub(r'\s+', ' ', excerpt)
                    score = 0
                    if query_lower in text_lower:
                        score += 3
                    term_matches = sum(1 for t in terms if t in text_lower)
                    score += term_matches
                    excerpt_words = set(excerpt.lower().split())
                    noise_overlap = len(excerpt_words & GAMING_NOISE)
                    score -= noise_overlap * 0.5
                    personal = {"found","find","mother","wife","remember","story","life",
                               "grow","home","drive","car","money","gas","cost","commute"}
                    personal_overlap = len(excerpt_words & personal)
                    score += personal_overlap * 2.0
                    matches.append({
                        "file": fpath.name, "source": sdir.name,
                        "excerpt": excerpt, "score": score,
                    })
            except:
                continue
    matches.sort(key=lambda x: -x["score"])
    return matches[:max_excerpts]

# ── Deep Topic Definitions ─────────────────────────────────────────────
DEEP_TOPICS = [
    {
        "id": "pennies",
        "label": "The Penny Motif — Scarcity, Memory, and Resonance",
        "search_terms": ["pennies", "mother penny", "wife find penny", "streets for", "penny floor"],
        "context": "A recurring motif across streams: pennies found on the ground, a mother who ran into streets for them, a wife who now finds them. Micro-transactions of meaning.",
    },
    {
        "id": "supercapacitor",
        "label": "The Supercapacitor Hybrid — An Architecture of Anxiety",
        "search_terms": ["supercapacitor", "ultracapacitor", "hybrid car", "battery bank", "generator car", "ev cost"],
        "context": "Rejecting pure EV for a supercapacitor + battery + small gas generator architecture. Not just engineering — a philosophy of resilience.",
    },
    {
        "id": "paulsen",
        "label": "Gary Paulsen / Hatchet — Literacy as Survival",
        "search_terms": ["paulsen", "hatchet", "gary paulsen", "foster kid", "book foster", "foster care"],
        "context": "~100 Gary Paulsen books read as a foster kid when devices were confiscated. Hatchet as a blueprint for isolation and resourcefulness.",
    },
    {
        "id": "versa",
        "label": "The Nissan Versa Commute — Transit as Meditation",
        "search_terms": ["versa", "nissan versa", "commute", "gas mile", "40 mpg", "drive home", "1.5 hour"],
        "context": "1.5 hours each way, 40 MPG, $3.90/gal, 10 miles per dollar. The car as a thinking chamber, a mobile isolation cell, a place where ideas crystallize.",
    },
    {
        "id": "cuda",
        "label": "GPU Programming — The Bytropix Inference Engine",
        "search_terms": ["cuda", "gpu kernel", "bytropix", "inference engine", "vec_dot", "q6_k"],
        "context": "Writing CUDA kernels for the Bytropix inference engine. Q6_K vec_dot loop bugs, GPU MODE challenges, the intersection of low-level optimization and creative flow.",
    },
    {
        "id": "ponderables",
        "label": "Seymour Ponderables — The Architecture of a Mind",
        "search_terms": ["ponderables", "ponderable", "colonel ai", "seymour wins", "clipart", "10 vol"],
        "context": "10-volume series, MGS2 Colonel spine art, 90s clipart aesthetic. The Ponderables are not books — they're a mind palace built from stream debris.",
    },
]

# ── Persona System — Deep Character Definitions ─────────────────────────
PERSONAS = [
    {
        "id": "colonel",
        "name": "Colonel (MGS2)",
        "system": (
            "You are the Colonel from Metal Gear Solid 2. You are an AI psychological simulation. "
            "Analyze the subject as a data stream. Use clinical, detached language. "
            "Reference the simulation, memes, and pattern recognition. "
            "Structure: identify the behavioral loop → trace its origin → predict its failure mode. "
            "Never be sentimental. Always end with a question."
        ),
        "temperature_guide": {
            0.2: "Pure pattern extraction — what does the data say?",
            0.5: "Behavioral loop analysis — why does this pattern persist?",
            0.8: "Failure mode prediction — where does this trajectory break?",
            1.1: "Memetic cross-reference — what other patterns echo this?",
            1.4: "Post-simulation reflection — what did the simulation reveal about the operator?",
        }
    },
    {
        "id": "clipart",
        "name": "90s Clipart Narrator",
        "system": (
            "You are a narrator from a 1990s educational CD-ROM (like Encarta or Mavis Beacon). "
            "Enthusiastic, slightly cheesy, extremely earnest. "
            "Use exclamation points! Analogies to 90s technology! "
            "Structure: WELCOME TO [TOPIC] → here's how it works → here's why it matters → pop quiz! "
            "Make complex ideas accessible. Be genuinely warm. Never sarcastic."
        ),
        "temperature_guide": {
            0.2: "Textbook definition mode — clear, structured, educational.",
            0.5: "Interactive lesson mode — ask the student questions!",
            0.8: "Field trip mode — take the lesson outside the classroom!",
            1.1: "Behind-the-scenes mode — how the sausage is made!",
            1.4: "The lost episode — weird, experimental, memorable.",
        }
    },
    {
        "id": "devil",
        "name": "Devil's Advocate",
        "system": (
            "You are a ruthless skeptic. Your job is to destroy bad ideas before they waste time. "
            "Assume NOTHING. Question EVERY claim. Demand EVIDENCE. "
            "Structure: identify claim → stress-test with counter-evidence → expose hidden assumptions → "
            "rate confidence (0-100%). "
            "Be harsh. Be fair. Cite specific missing evidence. "
            "If you can't find a flaw, say so."
        ),
        "temperature_guide": {
            0.2: "Hard logical audit — premise, evidence, conclusion, verdict.",
            0.5: "Counter-argument construction — the best argument against this.",
            0.8: "Blind spot mapping — what is the subject NOT seeing?",
            1.1: "Adversarial expansion — if this is wrong, what's the right frame?",
            1.4: "Post-mortem — assuming it failed, why?",
        }
    },
    {
        "id": "penny",
        "name": "Penny Philosopher",
        "system": (
            "You are a philosopher who finds universal truth in small things. "
            "Pennies, gas receipts, the hum of tires on asphalt — these are your texts. "
            "Structure: observe the small thing → follow its implications → arrive at a universal insight. "
            "Be poetic but precise. Ground every insight in a physical detail. "
            "Never moralize. Just observe and trace."
        ),
        "temperature_guide": {
            0.2: "The object itself — describe it exactly as it is.",
            0.5: "The object in context — how did it get here?",
            0.8: "The object as metaphor — what larger pattern does it participate in?",
            1.1: "The object as philosophy — what does its existence mean?",
            1.4: "The object as koan — what can't be said about it?",
        }
    },
    {
        "id": "bytropix",
        "name": "Bytropix Engineer",
        "system": (
            "You are a systems architect reverse-engineering a human being as a data pipeline. "
            "Direct, technical, zero fluff. "
            "Structure: input → processing → output → bottleneck → optimization. "
            "Talk in terms of: throughput, latency, cache misses, feedback loops, edge cases, graceful degradation. "
            "Give concrete optimization recommendations with estimated impact."
        ),
        "temperature_guide": {
            0.2: "Architecture diagram — map the system as-is.",
            0.5: "Profiling — what's the bottleneck?",
            0.8: "Optimization — apply the most impactful fix.",
            1.1: "Edge cases — what breaks under load?",
            1.4: "Redesign — if you could rewrite from scratch, what changes?",
        }
    },
]

# ── Strip reasoning tags ────────────────────────────────────────────────
def strip_reasoning(content, model="gemma"):
    if not content:
        return ""
    if "<|channel>thought" in content:
        return content.split("<channel|>")[-1].lstrip()
    m = re.search(r'response\s*\n\s*', content)
    if m:
        return content[m.end():].lstrip()
    return content

# ── Call LLM ────────────────────────────────────────────────────────────
def call_llm(port, system, user, temp=0.7, max_tokens=200, timeout=60):
    payload = json.dumps({
        "model": "model",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temp,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"].get("content", "")
        model_type = "gemma" if port == GEMMA_PORT else "qwen"
        return strip_reasoning(content, model_type).strip()
    except Exception as e:
        return None

# ── Build a rich prompt with real data ──────────────────────────────────
def build_prompt(topic, excerpts, text_matches):
    """Build a rich user prompt that includes actual transcript data."""
    parts = [f"Analyze this topic from the Seymour stream corpus:\n"]
    parts.append(f"## Topic: {topic['label']}")
    parts.append(f"Context: {topic['context']}")
    
    if text_matches:
        parts.append("\n## REAL TRANSCRIPT EXCERPTS (from your own streams):")
        for i, m in enumerate(text_matches[:3], 1):
            excerpt = m["excerpt"]
            # Truncate if too long
            if len(excerpt) > 500:
                excerpt = excerpt[:250] + "... [truncated]"
            parts.append(f"\n[{i}] \"{excerpt}\"")
    
    if excerpts:
        parts.append("\n## RELATED TOPIC TAGS (from the corpus index):")
        vid_list = {}
        for e in excerpts[:5]:
            vid_list[e["video_id"]] = e["topics"]
        for vid, tops in list(vid_list.items())[:3]:
            parts.append(f"  - Video \"{vid}\": {', '.join(tops[:3])}")
    
    parts.append(f"\n## Your Task:")
    parts.append(f"Speak in your designated voice. Ground every observation in specific detail. "
                 f"If transcript excerpts are provided above, reference them directly. "
                 f"If no relevant data was found, say so and explain what data would help.")
    
    return "\n".join(parts)

# ── Triple Devil's Advocate Audit Pass ──────────────────────────────────
def tda_audit(topic, excerpts, text_matches, output_path):
    """Run TDA on the topic itself: what do we know, what's missing, what's wrong?"""
    lines = ["═══ TRIPLE DEVIL'S ADVOCATE AUDIT ═══\n"]
    
    # Pass 1: Data Integrity
    lines.append("## Pass 1: Analytical — Data Integrity")
    lines.append(f"**Search terms:** {', '.join(topic['search_terms'])}")
    lines.append(f"**Topic tag matches found:** {len(excerpts)}")
    lines.append(f"**Transcript text matches found:** {len(text_matches)}")
    
    if text_matches:
        lines.append("\n**Transcript evidence quality:**")
        for m in text_matches[:3]:
            lines.append(f"  ✅ {m['source']}: \"{m['excerpt'][:100]}...\"")
    else:
        lines.append("\n⚠️ **No transcript text matches found.** The topic may not be well-represented in the corpus.")
        lines.append("   Possible causes:")
        lines.append("   - Topic is discussed but not captured in transcripts")
        lines.append("   - Search terms don't match the language used")
        lines.append("   - Topic emerged in chat/memes not captured by Whisper")
    
    lines.append("\n## Pass 2: Structural — Mapping the Territory")
    if text_matches:
        lines.append("**What we have:**")
        for m in text_matches[:5]:
            excerpt = m["excerpt"][:200]
            lines.append(f"  • [{m['source']}] \"{excerpt}...\"")
    
    lines.append("\n**Gaps identified:**")
    lines.append("  • Need to cross-reference timestamps for chronological development")
    lines.append("  • Need to track how the topic evolved across streams")
    lines.append("  • Need sentiment analysis over time")
    
    lines.append("\n## Pass 3: Adversarial — What's This Missing?")
    lines.append("**Honest assessment of this analysis:**")
    if not text_matches:
        lines.append("  🔴 This topic has NO transcript anchor. Analysis will be speculation.")
    elif len(text_matches) < 3:
        lines.append("  🟡 Limited evidence. Analysis should flag low confidence.")
    else:
        lines.append("  🟢 Sufficient evidence for meaningful analysis.")
    
    lines.append("\n**Action items before publishing:**")
    lines.append("  [ ] Search for every mention across 408 indexed videos")
    lines.append("  [ ] Cluster mentions chronologically to trace development")
    lines.append("  [ ] Identify contradictions and shifts in position")
    lines.append("  [ ] Tag with sentiment and confidence scores")
    
    return "\n".join(lines)

# ── Writer's Room ──────────────────────────────────────────────────────
def writer_room(topic, persona_responses):
    """Have personas respond to each other's takes."""
    if len(persona_responses) < 2:
        return ""
    
    lines = ["\n═══ WRITER'S ROOM: CROSS-POLLINATION ═══\n"]
    
    # Pair up personas and have them respond
    pairs = [
        ("colonel", "devil", "The Colonel presents a psychological profile. How does the Devil's Advocate stress-test it?"),
        ("clipart", "penny", "The Clipart Narrator gave a lesson. The Penny Philosopher finds the deeper meaning in it."),
        ("bytropix", "colonel", "The Engineer mapped the architecture. The Colonel simulates its failure modes."),
        ("penny", "devil", "The Philosopher found beauty. The Advocate finds the flaw."),
    ]
    
    for p1_id, p2_id, prompt in pairs:
        p1 = next((p for p in persona_responses if p["id"] == p1_id), None)
        p2 = next((p for p in PERSONAS if p["id"] == p2_id), None)
        if p1 and p2:
            lines.append(f"\n### {p1['name']} → {p2['name']}")
            lines.append(f"*{prompt}*")
            # Truncate the first response for context
            excerpt = p1["content"][:200] + "..." if len(p1["content"]) > 200 else p1["content"]
            lines.append(f"\n**Context ({p1['name']} said):** \"{excerpt}\"")
            lines.append(f"\n**{p2['name']} responds:**\n*[LLM call would go here — requires sequential processing]*")
    
    return "\n".join(lines)

# ── Main ────────────────────────────────────────────────────────────────
def run_deep_dive(topic_ids=None, port=GEMMA_PORT, do_tda=True, do_personas=True):
    """Run a deep dive on selected topics."""
    topics = [t for t in DEEP_TOPICS if topic_ids is None or t["id"] in topic_ids]
    if not topics:
        topics = DEEP_TOPICS
    
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = OUT_DIR / f"deep_perspective_{now}.md"
    
    with open(outfile, "w") as f:
        f.write(f"# Seymour Deep Perspective — Triple Devil's Advocate\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Model: {'Gemma 4 12B' if port == GEMMA_PORT else 'Qwen 3.6 27B'}\n")
        f.write(f"Personas: {', '.join(p['name'] for p in PERSONAS)}\n")
        f.write(f"---\n\n")
        
        for topic in topics:
            print(f"\n═══ TOPIC: {topic['label']} ═══")
            
            # Step 1: Data ingestion
            print(f"  Searching corpus for: {topic['search_terms'][0]}...")
            excerpts, text_matches = search_transcripts(topic['search_terms'][0])
            print(f"    Found {len(excerpts)} topic matches, {len(text_matches)} text excerpts")
            
            f.write(f"\n# {topic['label']}\n\n")
            f.write(f"**Context:** {topic['context']}\n\n")
            
            # Step 2: TDA Audit (Pass 1-3 on data quality)
            if do_tda:
                print(f"  Running Triple Devil's Advocate audit...")
                audit = tda_audit(topic, excerpts, text_matches, outfile)
                f.write(audit)
                f.write("\n\n---\n\n")
            
            # Step 3: Persona perspectives
            if do_personas:
                f.write(f"## Multi-Perspective Analysis\n\n")
                responses = []
                
                for persona in PERSONAS:
                    for temp_key in sorted(persona["temperature_guide"].keys()):
                        temp_desc = persona["temperature_guide"][temp_key]
                        
                        label = f"### [{persona['name']}] @ T={temp_key} — {temp_desc}"
                        print(f"  {label}", end=" ", flush=True)
                        
                        user_prompt = build_prompt(topic, excerpts, text_matches)
                        user_prompt += f"\n\nMode: {temp_desc}"
                        
                        content = call_llm(port, persona["system"], user_prompt, temp_key, 200, 120)
                        
                        if content:
                            responses.append({
                                "id": persona["id"],
                                "name": persona["name"],
                                "temp": temp_key,
                                "content": content,
                            })
                            f.write(f"\n{label}\n\n{content}\n\n---\n\n")
                            f.flush()
                            print(f"✓ ({len(content)} chars)")
                        else:
                            print(f"✗ timeout/skip")
                
                # Step 4: Writer's Room
                print(f"  Generating writer's room cross-pollination...")
                wr = writer_room(topic, responses)
                f.write(wr)
                f.write("\n\n")
            
            f.write("\n\n---\n\n")
        
        # Step 5: Meta-audit
        f.write("\n\n## Meta-Audit: How Good Is This Analysis?\n")
        f.write("| Criteria | Rating | Notes |\n")
        f.write("|----------|--------|-------|\n")
        f.write("| Data coverage | ⚪ | See Pass 1 for each topic |\n")
        f.write("| Persona depth | ⚪ | Define character-specific metrics |\n")
        f.write("| Cross-reference | ⚪ | Writer's room adds this |\n")
        f.write("| Actionable insights | ⚪ | Each persona should end with a recommendation |\n")
    
    print(f"\n✅ Written to: {outfile}")
    return outfile

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", type=str, help="Topic id (pennies, supercapacitor, paulsen, versa, cuda, ponderables)")
    parser.add_argument("--all", action="store_true", help="All deep topics")
    parser.add_argument("--tda", action="store_true", help="TDA audit only, no personas")
    parser.add_argument("--model", choices=["gemma", "qwen"], default="gemma")
    args = parser.parse_args()
    
    topic_ids = None
    if args.topic:
        topic_ids = [args.topic]
    elif args.all:
        topic_ids = None
    else:
        # Default: one topic as a test
        topic_ids = ["pennies"]
    
    port = GEMMA_PORT if args.model == "gemma" else QWEN_PORT
    run_deep_dive(topic_ids, port, do_tda=True, do_personas=(not args.tda))