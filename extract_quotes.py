#!/usr/bin/env python3
"""
extract_quotes.py — Mine Pre-Seymour transcripts for "Seymour-isms".

Outputs:
  - pre_seymour/quotes.json  (structured)
  - pre_seymour/quotes.md    (streaming-friendly reference)
"""
import json, re, random
from pathlib import Path

INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
QUOTES_FILE = Path("/home/wubu/seymour-project/pre_seymour/quotes.json")
QUOTES_MD = Path("/home/wubu/seymour-project/pre_seymour/quotes.md")

# Patterns that catch "Seymour-isms"
PATTERNS = [
    r"(I (think|feel|believe|guess|wonder|mean|don't know|can't|won't|should|would|could|might|must|need|want|like|love|hate|got|get|go|come|see|know|understand|realize|remember|forget|try|tried|fail|succeed|win|lose|die|live|fuck|shit|damn|hell|god|jesus|christ|holy|crap|bullshit|bull)\b.{0,80})",
    r"(this (is|was|will be|would be|could be|might be|should be|must be|has been|have been|had been) .{0,80})",
    r"(you (know|see|understand|get|don't get|won't get|can't get|should|would|could|might|must|need|want|like|love|hate|fuck|shit) .{0,80})",
    r"(the (thing|problem|issue|point|idea|way|truth|reality|fact|answer|question|key|secret|trick|catch|kicker|beauty|ugly|good|bad) .{0,80})",
    r"(it (is|was|will be|would be|could be|might be|should be|has been|have been|had been|doesn't|don't|won't|can't|ain't) .{0,80})",
    r"(we (are|were|will be|would be|could be|might be|should be|have been|had been|do|did|don't|didn't|won't|can't) .{0,80})",
]

# "Seymour" proper nouns / concepts
KEYWORDS = [
    "bytropix", "byTrop", "WuBu", "WuBuNesting", "Seymour", "ponderables",
    "hyperbolic", "holographic", "soul", "echo", "boundary", "nesting",
    "gpu mode", "triton", "cuda", "llama.cpp", "ggml", "gguf",
    "godot", "gdscript", "pokemon", "pokered", "pret", "decomp",
    "absorption", "absorber", "seymour-project",
    "supercapacitor", "nissan versa", "40mpg", "commute",
    "gary paulsen", "hatchet", "foster", "pennies", "mother", "diabetes",
    "wife", "telegram", "hermes", "nous", "modal", "fal", "firecrawl",
    "mind palace", "memory", "context", "token", "embedding", "attention",
    "kv cache", "quantization", "qlora", "lora", "peft", "fsdp", "grpo",
    "optimizer", "learning rate", "gradient", "backprop", "transformer",
    "mamba", "ssm", "delta net", "chunked", "recurrent", "linear attention",
]

def load_index():
    return json.loads(INDEX_FILE.read_text())

def extract_quotes():
    index = load_index()
    all_quotes = []
    
    for vid, entry in index.items():
        if entry["source"] == "c11":
            txt_path = Path(f"/home/wubu/seymour-project/absorption/data/transcripts/{vid}.txt")
        else:
            txt_path = Path(f"/home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_transcripts/{vid}_whisper.txt")
        
        if not txt_path.exists():
            continue
        
        try:
            text = txt_path.read_text()
        except:
            continue
        
        # Split into sentences (rough)
        sentences = re.split(r'[.!?]+\s+', text)
        
        for sent in sentences:
            sent = sent.strip()
            if len(sent) < 40 or len(sent) > 500:
                continue
            
            score = 0
            matched_kw = None
            
            # Keyword bonus
            for kw in KEYWORDS:
                if kw.lower() in sent.lower():
                    score += 10
                    matched_kw = kw
            
            # Pattern match
            for pat in PATTERNS:
                if re.search(pat, sent, re.IGNORECASE):
                    score += 5
            
            # Profanity/emotional intensity
            profanity = len(re.findall(r'\b(fuck|shit|damn|hell|god|jesus|christ|bullshit|crap)\b', sent, re.I))
            score += profanity * 3
            
            # Question/realization
            if re.search(r'\b(I (realize|understand|see|get|mean|think|guess|wonder))\b', sent, re.I):
                score += 5
            
            if score >= 10:
                all_quotes.append({
                    "video_id": vid,
                    "title": entry["title"],
                    "date": entry["upload_date"],
                    "source": entry["source"],
                    "quote": sent[:400],
                    "score": score,
                    "keyword": matched_kw,
                })
    
    # Sort by score
    all_quotes.sort(key=lambda x: x["score"], reverse=True)
    return all_quotes[:200]  # Top 200

def write_outputs(quotes):
    QUOTES_FILE.write_text(json.dumps(quotes, indent=2))
    
    # Markdown for streaming reference
    lines = ["# Seymour-isms — Pre-Era Quote Bank", "",
             f"*{len(quotes)} quotes mined from {len(set(q['video_id'] for q in quotes))} videos*",
             "", "---", ""]
    
    # Group by keyword
    by_kw = {}
    for q in quotes:
        kw = q.get("keyword", "general")
        by_kw.setdefault(kw, []).append(q)
    
    for kw, qs in sorted(by_kw.items(), key=lambda x: -len(x[1])):
        lines.append(f"## {kw} ({len(qs)} quotes)")
        for q in qs[:10]:  # Top 10 per keyword
            lines.append(f"> {q['quote']}")
            lines.append(f"> — *{q['date']} | {q['title'][:60]}* ([link](https://youtu.be/{q['video_id']}))")
            lines.append("")
        lines.append("---")
        lines.append("")
    
    QUOTES_MD.write_text("\n".join(lines))
    
    print(f"✓ Quotes: {QUOTES_FILE} ({len(quotes)} quotes)")
    print(f"✓ Markdown: {QUOTES_MD}")

if __name__ == "__main__":
    quotes = extract_quotes()
    write_outputs(quotes)