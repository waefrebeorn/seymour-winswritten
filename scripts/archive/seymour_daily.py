#!/usr/bin/env python3
"""
seymour_daily.py — Generate daily briefing from Pre-Seymour corpus.

Run via cron: 0 7 * * * /home/wubu/seymour-project/scripts/seymour_daily.py
Delivers to Telegram via bot API or saves to file for manual review.
"""

import json
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

INDEX_FILE = Path("/home/wubu/seymour-project/pre_seymour/index.json")
OUT_FILE = Path("/home/wubu/seymour-project/pre_seymour/daily_briefing.md")

def load_index():
    return json.loads(INDEX_FILE.read_text())

def get_recent_videos(index, days=7):
    """Get videos from the last N days."""
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for vid, entry in index.items():
        date_str = entry.get('upload_date', '')
        if date_str != 'unknown' and len(date_str) == 10:
            try:
                upload_date = datetime.strptime(date_str, '%Y-%m-%d')
                if upload_date >= cutoff:
                    recent.append((vid, entry))
            except:
                pass
    return recent

def get_untagged_sample(index, n=5):
    """Get random untagged videos for manual review."""
    untagged = [(v, e) for v, e in index.items() if not e.get('topics')]
    return random.sample(untagged, min(n, len(untagged)))

def get_top_topics(index, n=10):
    """Get most frequent topic tags."""
    from collections import Counter
    all_topics = []
    for entry in index.values():
        if entry.get('topics'):
            all_topics.extend([t.lower() for t in entry['topics']])
    return Counter(all_topics).most_common(n)

def get_random_quote(index, n=3):
    """Get random video snippets as 'quotes'."""
    with_transcript = [(v, e) for v, e in index.items() if e.get('transcript_path')]
    samples = random.sample(with_transcript, min(n, len(with_transcript)))
    quotes = []
    for vid, entry in samples:
        try:
            text = Path(entry['transcript_path']).read_text()
            # Get a random 200-char chunk
            if len(text) > 500:
                start = random.randint(0, len(text) - 500)
                snippet = text[start:start+300].replace('\n', ' ').strip()
            else:
                snippet = text[:300].replace('\n', ' ').strip()
            quotes.append((vid, entry['title'], entry['upload_date'], snippet))
        except:
            pass
    return quotes

def build_briefing():
    index = load_index()
    
    lines = [
        f"# Seymour Daily Briefing — {datetime.now():%Y-%m-%d}",
        f"*Generated: {datetime.now():%H:%M}*\n",
        "## 📊 Corpus Stats",
        f"- **Total videos**: {len(index)}",
        f"- **Tagged**: {sum(1 for e in index.values() if e.get('topics'))} / {len(index)}",
        f"- **Total words**: {sum(e.get('word_count', 0) for e in index.values()):,}",
        f"- **C11 transcripts**: {sum(1 for e in index.values() if e.get('source') == 'c11')}",
        f"- **Whisper transcripts**: {sum(1 for e in index.values() if e.get('source') == 'whisper')}\n",
    ]
    
    # Recent videos
    recent = get_recent_videos(index, 7)
    if recent:
        lines.append("## 🆕 Recent 7 Days")
        for vid, entry in sorted(recent, key=lambda x: x[1]['upload_date'], reverse=True)[:10]:
            topics = ", ".join(entry.get('topics', [])[:3]) if entry.get('topics') else "[untagged]"
            lines.append(f"- **[{entry['upload_date']}]** {entry['title'][:70]} ({vid}) — {topics}")
        lines.append("")
    
    # Top topics
    top_topics = get_top_topics(index, 10)
    if top_topics:
        lines.append("## 🏷️ Top Topics (this week)")
        for topic, count in top_topics:
            lines.append(f"- **{topic}**: {count} videos")
        lines.append("")
    
    # Untagged sample
    untagged = get_untagged_sample(index, 5)
    if untagged:
        lines.append("## ❓ Untagged — Needs Review")
        for vid, entry in untagged:
            lines.append(f"- **{vid}**: {entry['title'][:70]} ({entry['upload_date']})")
        lines.append("")
    
    # Random quotes
    quotes = get_random_quote(index, 3)
    if quotes:
        lines.append("## 💬 Resurfaced Fragments")
        for vid, title, date, snippet in quotes:
            lines.append(f"> {snippet}...\n> — *{title} ({date})* [{vid}]\n")
    
    # Footer
    lines.append("---")
    lines.append("*Seymour // penpal // archivist // 40 MPG Versa // penny motif*")
    
    return "\n".join(lines)

def main():
    briefing = build_briefing()
    OUT_FILE.write_text(briefing)
    print(f"Briefing written to {OUT_FILE}")
    
    # Also print to stdout for cron email capture
    print(briefing)

if __name__ == "__main__":
    main()