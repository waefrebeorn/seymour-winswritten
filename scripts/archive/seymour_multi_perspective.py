#!/usr/bin/env python3
"""seymour_multi_perspective.py — Hit both models with all personas × temps × topics.

Usage:
  python3 seymour_multi_perspective.py                          # Full run
  python3 seymour_multi_perspective.py --quick                  # Gemma only, 5 temps
  python3 seymour_multi_perspective.py --topic "penny"          # Single topic
  python3 seymour_multi_perspective.py --model gemma            # Gemma only
  python3 seymour_multi_perspective.py --model qwen             # Qwen only
"""
import json, time, os, sys, re, argparse
from datetime import datetime
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────
GEMMA_PORT = 18802
QWEN_PORT   = 18803
BASE        = Path("/home/wubu/seymour-project/pre_seymour")
OUTDIR      = Path("/home/wubu/seymour-project/ponderables/drafts")
INDEX_FILE  = BASE / "index.json"
os.makedirs(OUTDIR, exist_ok=True)

# ── Strip reasoning prefixes ────────────────────────────────────────────
def strip_reasoning(content, model):
    """Strip the pre-filled thinking tags from --reasoning off."""
    if not content:
        return ""
    if model == "gemma":
        # <|channel>thought\n<channel|>ACTUAL_TEXT
        if "<|channel>thought" in content:
            return content.split("<channel|>")[-1].lstrip()
    elif model == "qwen":
        #  thinking\n\n response\n\nACTUAL_TEXT
        m = re.search(r'response\s*\n\s*', content)
        if m:
            return content[m.end():].lstrip()
    return content

# ── Personas ────────────────────────────────────────────────────────────
PERSONAS = {
    "colonel": {
        "name": "Colonel (MGS2)",
        "system": "You are the Colonel from MGS2. Cryptic AI overlord analyzing a mind through stream data. Clinical, detached, eerily insightful. Short paragraphs.",
    },
    "clipart": {
        "name": "90s Clipart Narrator",
        "system": "You are a 1990s educational CD-ROM narrator. Enthusiastic, cheesy. Use exclamation points! Fun 90s metaphors! Make learning fun.",
    },
    "devils_advocate": {
        "name": "Devil's Advocate",
        "system": "You are a ruthless skeptic. Find every flaw and blind spot. Be harsh but fair. Cite specific evidence. Ask hard questions.",
    },
    "penny_philosopher": {
        "name": "Penny Philosopher",
        "system": "A wise philosopher who sees profound meaning in small things. Pennies, gas mileage, survival stories, foster resilience. Poetic, grounded, hopeful. One insight at a time.",
    },
    "bytropix": {
        "name": "Bytropix Engineer",
        "system": "Systems architect analyzing a life data flow. Direct, technical. Talk in feedback loops, pipeline integrity, information architecture. Give concrete recommendations.",
    },
}

# ── Topics ──────────────────────────────────────────────────────────────
TOPICS = [
    "the penny motif — pennies found, the mother who ran for them, the wife who finds them now",
    "the supercapacitor hybrid car idea — why not pure EV, the generator hybrid architecture",
    "Gary Paulsen / Hatchet — reading ~100 books as a foster kid with no devices",
    "the 2019 Nissan Versa commute — 1.5hr each way, 40 MPG, $3.90/gal gas math",
    "GPU programming / CUDA — the Bytropix inference engine, kernel challenges, Q6_K bugs",
    "Seymour Ponderables — the 10-volume series, Colonel spine, 90s clipart, how it all connects",
]

TEMPS = [0.2, 0.5, 0.8, 1.1, 1.4]

def call_llm(port, system, user, temp=0.7, max_tokens=128, timeout=30):
    """Call an OpenAI-compatible LLM endpoint. Returns content string or None."""
    import urllib.request, urllib.error
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
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        data = json.loads(resp.read())
        content = data["choices"][0]["message"].get("content", "")
        model_type = "gemma" if port == GEMMA_PORT else "qwen"
        stripped = strip_reasoning(content, model_type)
        return stripped.strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def run_perspectives(model="both", topics=None, temps=None):
    """Run multi-perspective synthesis."""
    if topics is None:
        topics = list(range(len(TOPICS)))
    if temps is None:
        temps = TEMPS

    ports = []
    if model in ("both", "gemma"):
        ports.append((GEMMA_PORT, "Gemma 4 12B (GPU)"))
    if model in ("both", "qwen"):
        ports.append((QWEN_PORT, "Qwen 3.6 27B (CPU)"))

    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    outfile = OUTDIR / f"multi_perspective_{now}.md"
    results = []

    with open(outfile, "w") as f:
        f.write(f"# Seymour Multi-Perspective Synthesis\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Models: {model}\n\n")

        for port, port_name in ports:
            for ti in topics:
                topic_text = TOPICS[ti]
                for pi, (pk, pv) in enumerate(PERSONAS.items()):
                    for temp in temps:
                        label = (
                            f"## [{port_name}] {pv['name']} — temp={temp}\n"
                            f"**Topic:** {topic_text}\n\n"
                        )
                        print(f"  [{port_name}] {pv['name']} @ T={temp} on topic #{ti+1}...", end=" ", flush=True)

                        timeout = 120  # Both models need this for CPU/GPU

                        # Prepend topic context to user message
                        user_msg = (
                            f"Analyze this topic in your voice:\n\n"
                            f"Topic: {topic_text}\n\n"
                            f"Context: This is from the mind of someone who streams games, "
                            f"builds GPU kernels, collects pennies, drives a 2019 Nissan Versa "
                            f"1.5hr each way, read ~100 Gary Paulsen books in foster care, "
                            f"and is building the Seymour Ponderables series. "
                            f"Give your unique take in {temp} words or so."
                        )

                        content = call_llm(port, pv["system"], user_msg, temp, 128, timeout)

                        if content and not content.startswith("[ERROR"):
                            results.append({
                                "model": port_name, "persona": pv["name"],
                                "topic": topic_text, "temp": temp, "content": content,
                            })
                            f.write(label)
                            f.write(content.strip() + "\n\n")
                            f.write("---\n\n")
                            f.flush()
                            print(f"✓ ({len(content)} chars)")
                        else:
                            print(f"✗ {content[:60] if content else 'empty'}")

        # Write summary / combined analysis
        f.write("\n\n# Combined Analysis\n\n")
        f.write("| Model | Persona | Temps | Topics |\n")
        f.write("|-------|---------|-------|--------|\n")
        seen = set()
        for r in results:
            key = (r["model"], r["persona"], r["temp"])
            if key not in seen:
                f.write(f"| {r['model']} | {r['persona']} | {r['temp']} | {len(TOPICS)} |\n")
                seen.add(key)
        f.write(f"\n**Total perspectives captured: {len(results)}**\n")

    print(f"\n\n✅ Written to: {outfile}")
    return outfile

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seymour Multi-Perspective Engine")
    parser.add_argument("--quick", action="store_true", help="Gemma only, 3 temps")
    parser.add_argument("--model", choices=["both", "gemma", "qwen"], default="both")
    parser.add_argument("--topic", type=str, help="Single topic substring to match")
    parser.add_argument("--temps", type=float, nargs="+", default=TEMPS,
                        help="Temperatures to use (default: 0.2 0.5 0.8 1.1 1.4)")
    args = parser.parse_args()

    if args.quick:
        args.model = "gemma"
        args.temps = [0.3, 0.7, 1.2]

    topics = list(range(len(TOPICS)))
    if args.topic:
        topics = [i for i, t in enumerate(TOPICS) if args.topic.lower() in t.lower()]
        if not topics:
            print(f"No matching topic for '{args.topic}'")
            sys.exit(1)

    out = run_perspectives(model=args.model, topics=topics, temps=args.temps)
    print(f"\n📄 Output: {out}")