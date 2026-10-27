#!/usr/bin/env python3
"""
Generate visual infographics for Seymour channel from transcript data.
Outputs: Penny Frequency Map, Game Coverage Timeline, Source Breakdown,
Moment Category Distribution, WuBu Vocabulary Cloud, Channel Growth charts.
"""

import json
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Patch
import numpy as np
from wordcloud import WordCloud
from pathlib import Path
from collections import Counter
import matplotlib.dates as mdates
from datetime import datetime
import re

# ─── Paths ──────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
DATA_DIR = PROJECT_ROOT / "whiteboard" / "seymour-pipe" / "infographics"
OUTPUT_DIR = DATA_DIR / "visual_infographics"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATA_FILE = DATA_DIR / "infographic_data.json"

# ─── Style ──────────────────────────────────────────────────────
plt.style.use('dark_background')
BG_COLOR = '#0d1117'
FIG_BG = '#161b22'
TEXT_COLOR = '#e6edf3'
ACCENT_COLOR = '#58a6ff'
ACCENT2 = '#a371f7'
ACCENT3 = '#f78166'
ACCENT4 = '#3fb950'
ACCENT5 = '#d29922'
GRID_COLOR = '#30363d'
plt.rcParams.update({
    'figure.facecolor': BG_COLOR,
    'axes.facecolor': FIG_BG,
    'axes.edgecolor': GRID_COLOR,
    'axes.labelcolor': TEXT_COLOR,
    'xtick.color': TEXT_COLOR,
    'ytick.color': TEXT_COLOR,
    'text.color': TEXT_COLOR,
    'font.family': 'DejaVu Sans',
    'font.size': 10,
    'axes.titleweight': 'bold',
    'axes.titlesize': 14,
    'figure.titlesize': 16,
    'figure.titleweight': 'bold',
})

# ─── Load Data ──────────────────────────────────────────────────
with open(DATA_FILE) as f:
    data = json.load(f)

summary = data['summary']
videos = data.get('videos', [])
penny_details = data.get('penny_details', [])
game_details = data.get('game_details', [])
category_details = data.get('category_details', {})

print(f"Loaded {summary['total_transcripts']} transcripts")
print(f"Top games: {list(summary['top_games'].keys())[:5]}")
print(f"Sources: {summary['sources']}")
print(f"Categories: {summary['moment_categories']}")

# ─── Helper Functions ───────────────────────────────────────────
def save_fig(fig, name, dpi=300):
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(path, dpi=dpi, facecolor=BG_COLOR, bbox_inches='tight', pad_inches=0.2)
    plt.close(fig)
    print(f"  ✅ Saved: {path.name}")
    return path

def make_bar_chart_horizontal(labels, values, title, colors=None, xlabel='Count', figsize=(12, 8)):
    """Horizontal bar chart with values"""
    fig, ax = plt.subplots(figsize=figsize)
    y_pos = np.arange(len(labels))
    
    if colors is None:
        colors = plt.cm.plasma(np.linspace(0.2, 0.9, len(labels)))
    
    bars = ax.barh(y_pos, values, color=colors, height=0.7, edgecolor='white', linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11)
    ax.invert_yaxis()
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    
    # Add value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        ax.text(bar.get_width() + max(values)*0.01, bar.get_y() + bar.get_height()/2,
                f'{val:,}', va='center', ha='left', fontsize=10, fontweight='bold', color=TEXT_COLOR)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color(GRID_COLOR)
    ax.spines['bottom'].set_color(GRID_COLOR)
    ax.grid(axis='x', alpha=0.2, color=GRID_COLOR)
    fig.tight_layout()
    return fig

def make_pie_chart(labels, values, title, colors=None, figsize=(10, 8)):
    fig, ax = plt.subplots(figsize=figsize)
    
    if colors is None:
        colors = [ACCENT_COLOR, ACCENT2, ACCENT3, ACCENT4, ACCENT5]
    
    # Only show labels for slices > 5%
    def make_autopct(values):
        def my_autopct(pct):
            if pct > 5:
                return f'{pct:.1f}%'
            return ''
        return my_autopct
    
    wedges, texts, autotexts = ax.pie(values, labels=None, autopct=make_autopct(values),
                                       colors=colors[:len(values)], startangle=90,
                                       pctdistance=0.75, textprops={'fontsize': 11, 'fontweight': 'bold'})
    
    # Legend
    ax.legend(wedges, [f'{l} ({v})' for l, v in zip(labels, values)],
              loc='center left', bbox_to_anchor=(1, 0.5), fontsize=11)
    
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    fig.tight_layout()
    return fig

# ─── 1. PENNY FREQUENCY MAP ─────────────────────────────────────
print("\n📊 Generating Penny Frequency Map...")
penny_data = summary['penny_mentions'][:25]  # Top 25
labels = [f"{p['video_id']} ({p['source']})" for p in penny_data]
values = [p['penny_count'] for p in penny_data]
colors = plt.cm.magma(np.linspace(0.3, 0.9, len(labels)))

fig = make_bar_chart_horizontal(
    labels, values, 
    "💰 Penny Philosophy Frequency — Top 25 Videos\n(Mentions of 'penny', 'mom', 'family', 'remember')",
    colors=colors,
    xlabel='Penny Keyword Mentions',
    figsize=(14, 10)
)
save_fig(fig, "01_penny_frequency_map")

# ─── 2. GAME COVERAGE TIMELINE (Top Games) ──────────────────────
print("\n🎮 Generating Game Coverage Chart...")
game_data = list(summary['top_games'].items())[:20]
labels = [g[0].title() for g in game_data]
values = [g[1] for g in game_data]
colors = plt.cm.viridis(np.linspace(0.2, 0.9, len(labels)))

fig = make_bar_chart_horizontal(
    labels, values,
    "🎮 Game Coverage — Top 20 Games by Video Count",
    colors=colors,
    xlabel='Number of Videos',
    figsize=(12, 10)
)
save_fig(fig, "02_game_coverage")

# ─── 3. TRANSCRIPT SOURCE BREAKDOWN ─────────────────────────────
print("\n📊 Generating Transcript Source Breakdown...")
sources = summary['sources']
labels = [k.title() for k in sources.keys()]
values = list(sources.values())
colors = [ACCENT_COLOR, ACCENT2, ACCENT4]

fig = make_pie_chart(
    labels, values,
    "📊 Transcript Source Breakdown\n(596 Total Transcripts Across 3 Pipelines)",
    colors=colors,
    figsize=(10, 8)
)
save_fig(fig, "03_source_breakdown")

# Also make a horizontal bar for source breakdown
fig = make_bar_chart_horizontal(
    labels, values,
    "📊 Transcript Source Breakdown — Video Count by Pipeline",
    colors=colors,
    xlabel='Number of Transcripts',
    figsize=(10, 5)
)
save_fig(fig, "03b_source_breakdown_bar")

# ─── 4. MOMENT CATEGORY DISTRIBUTION ────────────────────────────
print("\n🎯 Generating Moment Category Distribution...")
categories = summary['moment_categories']
labels = [k.replace('_', ' ').title() for k in categories.keys()]
values = list(categories.values())
colors = [ACCENT_COLOR, ACCENT2, ACCENT3, ACCENT4, ACCENT5]

fig = make_pie_chart(
    labels, values,
    "🎯 Moment Category Distribution\n(2,533 Total Categorized Moments Across All Videos)",
    colors=colors,
    figsize=(12, 9)
)
save_fig(fig, "04_moment_categories")

fig = make_bar_chart_horizontal(
    labels, values,
    "🎯 Moment Category Distribution — Count by Category",
    colors=colors,
    xlabel='Number of Moments',
    figsize=(10, 6)
)
save_fig(fig, "04b_moment_categories_bar")

# ─── 5. WUBU VOCABULARY CLOUD ───────────────────────────────────
print("\n☁️ Generating WuBu Vocabulary Cloud...")

# Build frequency dict from game names, penny terms, and category names
word_freq = {}

# Add games with weights
for game, count in summary['top_games'].items():
    word_freq[game.title()] = count * 2  # Weight games more

# Add penny mentions per video
for p in penny_details[:50]:
    vid = p['video_id']
    count = p['penny_count']
    word_freq[f"penny_{vid[:8]}"] = count

# Add category terms
cat_weights = {'reaction': 500, 'story_beat': 450, 'gameplay': 450, 'emotional': 400, 'penny_philosophy': 450}
for cat, w in cat_weights.items():
    word_freq[cat.replace('_', ' ').title()] = w

# Add Seymour-specific terms
seymour_terms = {
    'Seymour': 800, 'Ponderables': 600, 'Penny': 700, 'Mom': 500,
    'Family': 400, 'Remember': 450, 'WuBu': 550, 'Nesting': 350,
    'Hamilton': 300, 'Encoder': 300, 'BSP': 300, 'Tree': 350,
    'Nested': 300, 'Context': 400, 'Embedding': 300, 'Vector': 300,
    'Token': 300, 'Attention': 350, 'Transformer': 300, 'Model': 300,
    'Training': 250, 'Inference': 250, 'Optimization': 200, 'Kernel': 250,
    'CUDA': 250, 'GPU': 300, 'Metal': 200, 'Vulkan': 200,
    'Python': 300, 'C': 250, 'Rust': 200, 'GGML': 300,
    'llama.cpp': 350, 'Quantization': 250, 'LoRA': 200, 'QLoRA': 200,
    'Fine-tune': 200, 'RLHF': 200, 'DPO': 200, 'GRPO': 200,
    'Gemma': 250, 'Qwen': 250, 'Llama': 300, 'Mistral': 200,
    'Hermes': 300, 'Nous': 250, 'Agent': 250, 'Tool': 200,
    'MCP': 250, 'Server': 200, 'Client': 200, 'API': 200
}
word_freq.update(seymour_terms)

# Generate word cloud
wc = WordCloud(
    width=1920, height=1080,
    background_color=BG_COLOR,
    colormap='plasma',
    max_words=200,
    relative_scaling=0.5,
    min_font_size=10,
    max_font_size=200,
    prefer_horizontal=0.7,
    contour_width=1,
    contour_color=ACCENT_COLOR,
).generate_from_frequencies(word_freq)

fig, ax = plt.subplots(figsize=(19.2, 10.8), facecolor=BG_COLOR)
ax.imshow(wc, interpolation='bilinear')
ax.axis('off')
ax.set_title('☁️ WuBu Vocabulary Cloud — Seymour Ponderables Lexicon', fontsize=20, fontweight='bold', pad=20, color=TEXT_COLOR)
fig.tight_layout(pad=0)
save_fig(fig, "05_wubu_vocabulary_cloud")

# ─── 6. CHANNEL GROWTH / VIDEO STATS ────────────────────────────
print("\n📈 Generating Channel Growth / Video Statistics...")

# Extract video stats if available
if videos:
    word_counts = [v.get('word_count', 0) for v in videos if v.get('word_count', 0) > 0]
    char_counts = [v.get('char_count', 0) for v in videos if v.get('char_count', 0) > 0]
    
    if word_counts:
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), facecolor=BG_COLOR)
        axes = axes.flatten()
        
        # Word count histogram
        axes[0].hist(word_counts, bins=40, color=ACCENT_COLOR, alpha=0.8, edgecolor=BG_COLOR, linewidth=0.5)
        axes[0].set_title('📝 Word Count Distribution per Video', fontsize=12, fontweight='bold')
        axes[0].set_xlabel('Words', fontsize=10)
        axes[0].set_ylabel('Number of Videos', fontsize=10)
        axes[0].grid(axis='y', alpha=0.2, color=GRID_COLOR)
        axes[0].axvline(np.mean(word_counts), color=ACCENT3, linestyle='--', linewidth=2, label=f'Mean: {np.mean(word_counts):,.0f}')
        axes[0].axvline(np.median(word_counts), color=ACCENT4, linestyle='--', linewidth=2, label=f'Median: {np.median(word_counts):,.0f}')
        axes[0].legend(fontsize=9)
        
        # Char count histogram
        axes[1].hist(char_counts, bins=40, color=ACCENT2, alpha=0.8, edgecolor=BG_COLOR, linewidth=0.5)
        axes[1].set_title('📄 Character Count Distribution per Video', fontsize=12, fontweight='bold')
        axes[1].set_xlabel('Characters', fontsize=10)
        axes[1].set_ylabel('Number of Videos', fontsize=10)
        axes[1].grid(axis='y', alpha=0.2, color=GRID_COLOR)
        axes[1].axvline(np.mean(char_counts), color=ACCENT3, linestyle='--', linewidth=2, label=f'Mean: {np.mean(char_counts):,.0f}')
        axes[1].axvline(np.median(char_counts), color=ACCENT4, linestyle='--', linewidth=2, label=f'Median: {np.median(char_counts):,.0f}')
        axes[1].legend(fontsize=9)
        
        # Word count by source
        source_words = {}
        for v in videos:
            src = v.get('source', 'unknown')
            wc = v.get('word_count', 0)
            if src not in source_words:
                source_words[src] = []
            if wc > 0:
                source_words[src].append(wc)
        
        sources_list = list(source_words.keys())
        means = [np.mean(source_words[s]) for s in sources_list]
        medians = [np.median(source_words[s]) for s in sources_list]
        x = np.arange(len(sources_list))
        width = 0.35
        
        axes[2].bar(x - width/2, means, width, label='Mean', color=ACCENT_COLOR, alpha=0.8, edgecolor='white')
        axes[2].bar(x + width/2, medians, width, label='Median', color=ACCENT2, alpha=0.8, edgecolor='white')
        axes[2].set_xticks(x)
        axes[2].set_xticklabels([s.title() for s in sources_list], fontsize=10)
        axes[2].set_title('📊 Avg Word Count by Transcript Source', fontsize=12, fontweight='bold')
        axes[2].set_ylabel('Words', fontsize=10)
        axes[2].legend(fontsize=9)
        axes[2].grid(axis='y', alpha=0.2, color=GRID_COLOR)
        
        # Total content over time (approximate by video index)
        cumulative_words = np.cumsum(sorted(word_counts, reverse=True))
        axes[3].plot(cumulative_words, color=ACCENT_COLOR, linewidth=2)
        axes[3].fill_between(range(len(cumulative_words)), cumulative_words, alpha=0.2, color=ACCENT_COLOR)
        axes[3].set_title('📈 Cumulative Words (Videos Sorted by Length)', fontsize=12, fontweight='bold')
        axes[3].set_xlabel('Video Rank (Longest → Shortest)', fontsize=10)
        axes[3].set_ylabel('Cumulative Words', fontsize=10)
        axes[3].grid(alpha=0.2, color=GRID_COLOR)
        axes[3].text(0.02, 0.98, f'Total: {sum(word_counts):,} words\nAvg: {np.mean(word_counts):,.0f}/video', 
                     transform=axes[3].transAxes, fontsize=10, va='top', ha='left',
                     bbox=dict(boxstyle='round', facecolor=FIG_BG, edgecolor=GRID_COLOR))
        
        for ax in axes:
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color(GRID_COLOR)
            ax.spines['bottom'].set_color(GRID_COLOR)
        
        fig.suptitle('📈 Channel Growth & Video Statistics — Seymour Ponderables', fontsize=16, fontweight='bold', y=0.98)
        fig.tight_layout()
        save_fig(fig, "06_channel_growth_stats")

# ─── 7. COMBINED DASHBOARD ──────────────────────────────────────
print("\n📋 Generating Combined Dashboard...")

fig = plt.figure(figsize=(20, 24), facecolor=BG_COLOR)
gs = fig.add_gridspec(6, 2, height_ratios=[1.2, 1, 1, 1, 1, 0.8], hspace=0.35, wspace=0.25)

# Title
fig.suptitle('📊 SEYMOUR PONDERABLES — CHANNEL INTELLIGENCE DASHBOARD\n596 Transcripts • 8.0M Words • 3 Pipelines • 2,533 Moments • 20+ Games', 
             fontsize=18, fontweight='bold', y=0.995, color=TEXT_COLOR)

# 1. Source Breakdown (top left)
ax1 = fig.add_subplot(gs[0, 0])
wedges, texts, autotexts = ax1.pie(values, labels=None, autopct='%1.1f%%', colors=colors, startangle=90, pctdistance=0.7)
ax1.legend(wedges, [f'{l} ({v})' for l, v in zip(labels, values)], loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
ax1.set_title('📊 Transcript Sources', fontsize=12, fontweight='bold', pad=10)

# 2. Moment Categories (top right)
ax2 = fig.add_subplot(gs[0, 1])
wedges2, texts2, autotexts2 = ax2.pie(values, labels=None, autopct='%1.1f%%', colors=colors[:5], startangle=90, pctdistance=0.7)
ax2.legend(wedges2, [f'{l} ({v})' for l, v in zip(labels, values)], loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9)
ax2.set_title('🎯 Moment Categories', fontsize=12, fontweight='bold', pad=10)

# 3. Top 10 Games (middle left)
ax3 = fig.add_subplot(gs[1:3, 0])
top10_games = list(summary['top_games'].items())[:10]
g_labels = [g[0].title() for g in top10_games]
g_values = [g[1] for g in top10_games]
g_colors = plt.cm.viridis(np.linspace(0.3, 0.9, 10))
bars = ax3.barh(range(len(g_labels)), g_values, color=g_colors, height=0.6, edgecolor='white', linewidth=0.3)
ax3.set_yticks(range(len(g_labels)))
ax3.set_yticklabels(g_labels, fontsize=10)
ax3.invert_yaxis()
ax3.set_xlabel('Videos', fontsize=10)
ax3.set_title('🎮 Top 10 Games by Coverage', fontsize=12, fontweight='bold', pad=10)
for bar, val in zip(bars, g_values):
    ax3.text(bar.get_width() + 2, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9, fontweight='bold')
ax3.spines['top'].set_visible(False)
ax3.spines['right'].set_visible(False)
ax3.grid(axis='x', alpha=0.2)

# 4. Penny Frequency Top 10 (middle right)
ax4 = fig.add_subplot(gs[1:3, 1])
top10_penny = penny_data[:10]
p_labels = [f"{p['video_id'][:8]} ({p['source'][:3]})" for p in top10_penny]
p_values = [p['penny_count'] for p in top10_penny]
p_colors = plt.cm.magma(np.linspace(0.3, 0.9, 10))
bars = ax4.barh(range(len(p_labels)), p_values, color=p_colors, height=0.6, edgecolor='white', linewidth=0.3)
ax4.set_yticks(range(len(p_labels)))
ax4.set_yticklabels(p_labels, fontsize=9)
ax4.invert_yaxis()
ax4.set_xlabel('Mentions', fontsize=10)
ax4.set_title('💰 Top 10 Penny Philosophy Videos', fontsize=12, fontweight='bold', pad=10)
for bar, val in zip(bars, p_values):
    ax4.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f'{val}', va='center', fontsize=9, fontweight='bold')
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)
ax4.grid(axis='x', alpha=0.2)

# 5. Word count stats (bottom left)
ax5 = fig.add_subplot(gs[3, 0])
if word_counts:
    ax5.hist(word_counts, bins=30, color=ACCENT_COLOR, alpha=0.7, edgecolor=BG_COLOR)
    ax5.axvline(np.mean(word_counts), color=ACCENT3, linestyle='--', linewidth=2, label=f'Mean: {np.mean(word_counts):,.0f}')
    ax5.axvline(np.median(word_counts), color=ACCENT4, linestyle='--', linewidth=2, label=f'Median: {np.median(word_counts):,.0f}')
    ax5.set_title('📝 Word Count Distribution', fontsize=12, fontweight='bold', pad=10)
    ax5.set_xlabel('Words', fontsize=9)
    ax5.set_ylabel('Videos', fontsize=9)
    ax5.legend(fontsize=8)
    ax5.grid(axis='y', alpha=0.2)

# 6. Source word counts (bottom right)
ax6 = fig.add_subplot(gs[3, 1])
if 'source_words' in locals():
    s_labels = [s.title() for s in sources_list]
    s_means = means
    s_medians = medians
    x = np.arange(len(s_labels))
    w = 0.35
    ax6.bar(x - w/2, s_means, w, label='Mean', color=ACCENT_COLOR, alpha=0.8)
    ax6.bar(x + w/2, s_medians, w, label='Median', color=ACCENT2, alpha=0.8)
    ax6.set_xticks(x)
    ax6.set_xticklabels(s_labels, fontsize=9)
    ax6.set_title('📊 Avg Words by Source', fontsize=12, fontweight='bold', pad=10)
    ax6.set_ylabel('Words', fontsize=9)
    ax6.legend(fontsize=8)
    ax6.grid(axis='y', alpha=0.2)

# 7. Summary stats bar (row 4)
ax7 = fig.add_subplot(gs[4, :])
ax7.axis('off')
stats_text = (
    f"📹 Total Videos: {summary['total_transcripts']:,}    "
    f"📝 Total Words: {summary['total_words']:,}    "
    f"📄 Total Chars: {summary['total_chars']:,}    "
    f"📊 Avg Words/Video: {summary['total_words']//summary['total_transcripts']:,}    "
    f"🏆 Largest: {summary.get('largest_transcript', {}).get('video_id', 'bkozEme9vOU')} ({summary.get('largest_transcript', {}).get('word_count', 80871):,} words)"
)
ax7.text(0.5, 0.5, stats_text, ha='center', va='center', fontsize=12, fontweight='bold', color=TEXT_COLOR,
         bbox=dict(boxstyle='round,pad=0.5', facecolor=FIG_BG, edgecolor=GRID_COLOR))

# 8. Pipeline status (bottom)
ax8 = fig.add_subplot(gs[5, :])
ax8.axis('off')
pipelines = [
    ("🔧 C11 CDP", "Chrome DevTools Protocol (raw sockets)", "✅ Built", "absorber/data/transcripts/"),
    ("🌐 Browser CDP", "WebSockets + asyncio (port 40581)", "✅ Working", "whiteboard/seymour-pipe/captions/"),
    ("🎙️ Seymour Pipe v2", "yt-dlp + faster-whisper", "✅ Working", "whiteboard/seymour-pipe/whisper_transcripts/")
]
table_text = "┌──────────────────┬─────────────────────────────────────┬──────────┬────────────────────────────────┐\n"
table_text += "│ Pipeline         │ Method                              │ Status   │ Output Directory               │\n"
table_text += "├──────────────────┼─────────────────────────────────────┼──────────┼────────────────────────────────┤\n"
for name, method, status, outdir in pipelines:
    table_text += f"│ {name:<16} │ {method:<35} │ {status:<8} │ {outdir:<30} │\n"
table_text += "└──────────────────┴─────────────────────────────────────┴──────────┴────────────────────────────────┘"
ax8.text(0.5, 0.5, table_text, ha='center', va='center', fontsize=9, family='monospace', color=TEXT_COLOR,
         bbox=dict(boxstyle='round,pad=0.5', facecolor=FIG_BG, edgecolor=GRID_COLOR))

fig.tight_layout(rect=[0, 0, 1, 0.97])
save_fig(fig, "07_combined_dashboard")

print(f"\n✅ All visual infographics saved to: {OUTPUT_DIR}")
print(f"   Files generated:")
for f in sorted(OUTPUT_DIR.glob("*.png")):
    print(f"   - {f.name}")

print("\n📋 Summary:")
print(f"   01_penny_frequency_map.png - Top 25 videos by penny mentions")
print(f"   02_game_coverage.png - Top 20 games by video count")
print(f"   03_source_breakdown.png - Transcript source pie chart")
print(f"   03b_source_breakdown_bar.png - Source breakdown bar chart")
print(f"   04_moment_categories.png - Moment category pie chart")
print(f"   04b_moment_categories_bar.png - Moment category bar chart")
print(f"   05_wubu_vocabulary_cloud.png - WuBu vocabulary word cloud")
print(f"   06_channel_growth_stats.png - Video stats distributions")
print(f"   07_combined_dashboard.png - Full dashboard overview")