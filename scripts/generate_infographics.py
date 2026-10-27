#!/usr/bin/env python3
"""
Generate Infographics from Seymour Absorbed Data
===============================================
Creates visual summaries for Seymour Vol. 1 and channel branding.
"""

import json
import os
from pathlib import Path
from collections import Counter
import re

# ─── Data Paths ──────────────────────────────────────────────
CAPTIONS_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/captions")
WHISPER_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/whisper_transcripts")
absorber_DIR = Path("/home/wubu/seymour-project/absorption/data/transcripts")
OUTPUT_DIR = Path("/home/wubu/seymour-project/whiteboard/seymour-pipe/infographics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── Helper Functions ────────────────────────────────────────

def read_all_transcripts():
    """Read all transcript files from all three pipelines."""
    transcripts = []
    
    # Engagement panel transcripts (captions)
    for f in CAPTIONS_DIR.glob("*_engagement.txt"):
        try:
            content = f.read_text()
            vid = f.stem.split("_")[-2] if "_" in f.stem else f.stem
            transcripts.append({
                "video_id": vid,
                "source": "engagement",
                "content": content,
                "file": f
            })
        except:
            pass
    
    # Whisper transcripts
    for f in WHISPER_DIR.glob("*_whisper.txt"):
        try:
            content = f.read_text()
            vid = f.stem.replace("_whisper", "")
            transcripts.append({
                "video_id": vid,
                "source": "whisper",
                "content": content,
                "file": f
            })
        except:
            pass
    
    # C11 absorber transcripts
    for f in absorber_DIR.glob("*.txt"):
        try:
            content = f.read_text()
            vid = f.stem
            transcripts.append({
                "video_id": vid,
                "source": "c11_cdp",
                "content": content,
                "file": f
            })
        except:
            pass
    
    return transcripts

def count_penny_mentions(transcripts):
    """Count penny/philosophy mentions per video."""
    penny_patterns = [
        r"\bpenny\b", r"\bpennies\b", r"\bnickel\b", r"\bdime\b", 
        r"\bcoin\b", r"\bchange\b", r"\bmom\b", r"\bmother\b",
        r"\bwife\b", r"\bfamily\b", r"\bremember\b"
    ]
    
    results = []
    for t in transcripts:
        text = t["content"].lower()
        count = sum(len(re.findall(p, text)) for p in penny_patterns)
        if count > 0:
            results.append({
                "video_id": t["video_id"],
                "source": t["source"],
                "penny_count": count
            })
    return sorted(results, key=lambda x: -x["penny_count"])

def count_game_mentions(transcripts):
    """Identify games mentioned in transcripts."""
    game_keywords = [
        "mario", "zelda", "pokemon", "minecraft", "fortnite", "roblox",
        "halo", "call of duty", "warzone", "apex", "valorant",
        "elden ring", "dark souls", "sekiro", "bloodborne",
        "red dead", "gta", "grand theft auto", "cyberpunk",
        "witcher", "skyrim", "fallout", "mass effect",
        "poppy playtime", "five nights", "fnaf", "amanda",
        "hard time", "hard time 3", "mdickie",
        "marvel rivals", "rivals", "overwatch",
        "team fortress", "tf2", "counter strike", "csgo", "cs2",
        "dead space", "resident evil", "silent hill",
        "psychonauts", "death stranding", "metal gear",
        "schedule 1", "mind scan", "scanning"
    ]
    
    game_counts = Counter()
    for t in transcripts:
        text = t["content"].lower()
        for game in game_keywords:
            if re.search(rf"\b{re.escape(game)}\b", text):
                game_counts[game] += 1
    return game_counts.most_common()

def extract_moments_by_category(transcripts):
    """Extract moment categories from seymour_pipe output or infer from text."""
    categories = {
        "reaction": [r"oh my", r"wow", r"holy", r"what", r"no way", r"insane", r"lol", r"lmao", r"haha"],
        "story_beat": [r"so then", r"and then", r"but then", r"suddenly", r"finally", r"here's the thing", r"listen", r"okay so"],
        "emotional": [r"can't believe", r"never thought", r"dream", r"forget", r"remember when", r"miss", r"loved", r"lost", r"found"],
        "gameplay": [r"boss", r"final", r"beat", r"won", r"lost", r"died", r"killed", r"defeated", r"secret", r"hidden", r"easter egg", r"ending", r"twist"],
        "penny_philosophy": [r"\bpenny\b", r"\bpennies\b", r"\bmom\b", r"\bmother\b", r"\bwife\b", r"\bfamily\b", r"\bremember\b"]
    }
    
    category_counts = Counter()
    for t in transcripts:
        text = t["content"].lower()
        for cat, patterns in categories.items():
            for pat in patterns:
                if re.search(pat, text):
                    category_counts[cat] += 1
                    break
    return category_counts

def get_source_breakdown(transcripts):
    """Count transcripts by source."""
    return Counter(t["source"] for t in transcripts)

def get_video_metadata(transcripts):
    """Extract video IDs and basic stats."""
    return [{
        "video_id": t["video_id"],
        "source": t["source"],
        "word_count": len(t["content"].split()),
        "char_count": len(t["content"])
    } for t in transcripts]

# ─── Generate Outputs ────────────────────────────────────────

def generate_markdown_report(transcripts, penny_counts, game_counts, category_counts, source_counts, video_stats):
    """Generate a comprehensive markdown infographic report."""
    
    lines = []
    lines.append("# Seymour Channel Infographics")
    lines.append("")
    lines.append(f"*Generated from {len(transcripts)} transcripts across 3 pipelines*")
    lines.append("")
    
    # Source Breakdown
    lines.append("## 📊 Transcript Source Breakdown")
    lines.append("")
    for source, count in source_counts.most_common():
        pct = 100 * count / len(transcripts)
        bar = "█" * int(pct / 2)
        lines.append(f"- **{source}**: {count} ({pct:.1f}%) {bar}")
    lines.append("")
    
    # Penny Frequency
    lines.append("## 💰 Penny Philosophy Frequency")
    lines.append("")
    lines.append("*Videos where penny/mom/family/remember keywords appear*")
    lines.append("")
    for p in penny_counts[:20]:
        lines.append(f"- `{p['video_id']}` ({p['source']}): **{p['penny_count']}** mentions")
    lines.append("")
    
    # Game Coverage
    lines.append("## 🎮 Game Coverage (Top 30)")
    lines.append("")
    for game, count in game_counts[:30]:
        bar = "█" * min(count, 30)
        lines.append(f"- **{game.title()}**: {count} videos {bar}")
    lines.append("")
    
    # Moment Categories
    lines.append("## 🎯 Moment Category Distribution")
    lines.append("")
    total = sum(category_counts.values())
    for cat, count in category_counts.most_common():
        pct = 100 * count / total if total else 0
        bar = "█" * int(pct / 2)
        lines.append(f"- **{cat.replace('_', ' ').title()}**: {count} ({pct:.1f}%) {bar}")
    lines.append("")
    
    # Video Stats
    lines.append("## 📈 Video Statistics")
    lines.append("")
    if video_stats:
        total_words = sum(v["word_count"] for v in video_stats)
        total_chars = sum(v["char_count"] for v in video_stats)
        avg_words = total_words / len(video_stats)
        lines.append(f"- **Total videos**: {len(video_stats)}")
        lines.append(f"- **Total words**: {total_words:,}")
        lines.append(f"- **Total characters**: {total_chars:,}")
        lines.append(f"- **Avg words/video**: {avg_words:,.0f}")
        lines.append(f"- **Largest transcript**: {max(video_stats, key=lambda x: x['word_count'])['video_id']} ({max(v['word_count'] for v in video_stats):,} words)")
    lines.append("")
    
    # Pipeline Status
    lines.append("## ⚙️ Pipeline Status")
    lines.append("")
    lines.append("| Pipeline | Method | Status | Output Dir |")
    lines.append("|----------|--------|--------|------------|")
    lines.append("| C11 CDP | Chrome DevTools Protocol (raw sockets) | ✅ Built | `absorber/data/transcripts/` |")
    lines.append("| Browser CDP | WebSockets + asyncio (port 40581) | ✅ Working | `whiteboard/seymour-pipe/captions/` |")
    lines.append("| Seymour Pipe v2 | yt-dlp + faster-whisper | ✅ Working | `whiteboard/seymour-pipe/whisper_transcripts/` |")
    lines.append("")
    
    lines.append("---")
    lines.append("*Seymour Ponderables — Infographic Generator*")
    
    return "\n".join(lines)

def generate_json_data(transcripts, penny_counts, game_counts, category_counts, source_counts, video_stats):
    """Generate JSON for programmatic use."""
    return {
        "summary": {
            "total_transcripts": len(transcripts),
            "total_words": sum(v["word_count"] for v in video_stats),
            "total_chars": sum(v["char_count"] for v in video_stats),
            "sources": dict(source_counts),
            "top_games": dict(game_counts[:20]),
            "moment_categories": dict(category_counts),
            "penny_mentions": penny_counts[:20]
        },
        "videos": video_stats,
        "penny_details": penny_counts,
        "game_details": game_counts,
        "category_details": dict(category_counts)
    }

# ─── Main ────────────────────────────────────────────────────

def main():
    print("🔍 Reading all transcripts...")
    transcripts = read_all_transcripts()
    print(f"   Found {len(transcripts)} transcripts")
    
    print("💰 Counting penny mentions...")
    penny_counts = count_penny_mentions(transcripts)
    
    print("🎮 Identifying games...")
    game_counts = count_game_mentions(transcripts)
    
    print("🎯 Categorizing moments...")
    category_counts = extract_moments_by_category(transcripts)
    
    print("📊 Source breakdown...")
    source_counts = get_source_breakdown(transcripts)
    
    print("📈 Video statistics...")
    video_stats = get_video_metadata(transcripts)
    
    print("📝 Generating markdown report...")
    md_report = generate_markdown_report(transcripts, penny_counts, game_counts, category_counts, source_counts, video_stats)
    (OUTPUT_DIR / "infographic_report.md").write_text(md_report)
    
    print("📄 Generating JSON data...")
    json_data = generate_json_data(transcripts, penny_counts, game_counts, category_counts, source_counts, video_stats)
    (OUTPUT_DIR / "infographic_data.json").write_text(json.dumps(json_data, indent=2))
    
    print(f"✅ Done! Output in {OUTPUT_DIR}")
    print(f"   - infographic_report.md")
    print(f"   - infographic_data.json")

if __name__ == "__main__":
    main()