#!/usr/bin/env python3
"""
Seymour Free Search Engine
===========================
Multi-layered search tool that avoids API key usage.

Layers:
  1. DuckDuckGo Instant Answer API (no key, instant facts)
  2. SearXNG self-hosted meta-search (no key, full web search)
  3. Direct web scraping fallback (BeautifulSoup)

Usage:
  python3 search.py "query" [--layer all|ddg|searx|scrape] [--count 10] [--json]
"""

import sys
import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import hashlib
import pathlib
from datetime import datetime

# ── Configuration ──────────────────────────────────────────────────────────────

SEARXNG_URL = os.environ.get("SEARXNG_BASE_URL", "http://localhost:8080")
DDG_API_URL = "https://api.duckduckgo.com/"
USER_AGENT = "SeymourSearch/1.0 (Hermes Agent; research project)"
CACHE_DIR = pathlib.Path("/home/wubu/seymour-project/.search-cache")
CACHE_TTL = 3600  # 1 hour

# ── Cache ──────────────────────────────────────────────────────────────────────

def cache_key(query: str, layer: str) -> str:
    return hashlib.md5(f"{layer}:{query}".encode()).hexdigest()

def cache_get(query: str, layer: str) -> dict | None:
    k = cache_key(query, layer)
    p = CACHE_DIR / f"{k}.json"
    if p.exists():
        age = time.time() - p.stat().st_mtime
        if age < CACHE_TTL:
            try:
                return json.loads(p.read_text())
            except Exception:
                pass
    return None

def cache_set(query: str, layer: str, data: dict):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    k = cache_key(query, layer)
    p = CACHE_DIR / f"{k}.json"
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False))

# ── Layer 1: DuckDuckGo Instant Answer API ─────────────────────────────────────

def ddg_search(query: str) -> dict:
    """
    DuckDuckGo Instant Answer API.
    No API key required. Returns instant answers, definitions, related topics.
    Endpoint: https://api.duckduckgo.com/?q=QUERY&format=json&no_html=1
    """
    cached = cache_get(query, "ddg")
    if cached:
        return cached

    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "no_html": "1",
        "skip_disambig": "0",
    })
    url = f"{DDG_API_URL}?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        result = {
            "layer": "ddg",
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "abstract": data.get("AbstractText", ""),
            "abstract_url": data.get("AbstractURL", ""),
            "abstract_source": data.get("AbstractSource", ""),
            "answer": data.get("Answer", ""),
            "answer_type": data.get("AnswerType", ""),
            "definition": data.get("Definition", ""),
            "definition_url": data.get("DefinitionURL", ""),
            "heading": data.get("Heading", ""),
            "type": data.get("Type", ""),  # A=article, D=disambiguation, C=category, N=nothing
            "related_topics": [],
            "results": [],
        }

        for rt in data.get("RelatedTopics", []):
            if isinstance(rt, dict):
                if "Text" in rt:
                    result["related_topics"].append({
                        "text": rt.get("Text", ""),
                        "url": rt.get("FirstURL", ""),
                    })
                elif "Topics" in rt:
                    for sub in rt["Topics"]:
                        result["related_topics"].append({
                            "text": sub.get("Text", ""),
                            "url": sub.get("FirstURL", ""),
                        })

        for r in data.get("Results", []):
            if isinstance(r, dict):
                result["results"].append({
                    "text": r.get("Text", ""),
                    "url": r.get("FirstURL", ""),
                })

        cache_set(query, "ddg", result)
        return result

    except Exception as e:
        return {"layer": "ddg", "query": query, "error": str(e)}

# ── Layer 2: SearXNG Meta-Search ───────────────────────────────────────────────

def searxng_search(query: str, count: int = 10, categories: str = "general") -> dict:
    """
    SearXNG self-hosted meta-search.
    No API key required. Aggregates Google, Bing, DuckDuckGo, etc.
    Requires SearXNG instance running at SEARXNG_BASE_URL.
    """
    cached = cache_get(query, "searxng")
    if cached:
        return cached

    params = urllib.parse.urlencode({
        "q": query,
        "format": "json",
        "pageno": 1,
        "categories": categories,
        "language": "en",
        "time_range": "",
    })
    url = f"{SEARXNG_URL}/search?{params}"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        results = []
        for r in data.get("results", [])[:count]:
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "source": r.get("engine", ""),
                "score": r.get("score", 0),
                "published": r.get("publishedDate", ""),
                "thumbnail": r.get("thumbnail", ""),
            })

        result = {
            "layer": "searxng",
            "query": query,
            "timestamp": datetime.utcnow().isoformat(),
            "total_results": data.get("number_of_results", 0),
            "results": results,
            "suggestions": data.get("suggestions", []),
            "corrections": data.get("corrections", []),
            "infoboxes": data.get("infoboxes", []),
        }

        cache_set(query, "searxng", result)
        return result

    except Exception as e:
        return {"layer": "searxng", "query": query, "error": str(e)}

# ── Layer 3: Direct Web Scraping ───────────────────────────────────────────────

def scrape_page(url: str) -> dict:
    """
    Direct web page scraping fallback.
    Uses urllib + basic HTML parsing. No external dependencies.
    """
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()

        # Try to detect encoding
        content_type = resp.headers.get("Content-Type", "")
        encoding = "utf-8"
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].strip()

        html = raw.decode(encoding, errors="replace")

        # Extract title
        title = ""
        if "<title>" in html.lower():
            start = html.lower().find("<title>") + 7
            end = html.lower().find("</title>", start)
            if end > start:
                title = html[start:end].strip()

        # Extract meta description
        description = ""
        if 'name="description"' in html.lower():
            idx = html.lower().find('name="description"')
            chunk = html[idx:idx+200]
            if 'content="' in chunk:
                cstart = chunk.find('content="') + 9
                cend = chunk.find('"', cstart)
                if cend > cstart:
                    description = chunk[cstart:cend]

        # Extract visible text (strip tags)
        import re
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()

        return {
            "layer": "scrape",
            "url": url,
            "title": title,
            "description": description,
            "text": text[:5000],  # First 5000 chars
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {"layer": "scrape", "url": url, "error": str(e)}

# ── Unified Search ─────────────────────────────────────────────────────────────

def search(query: str, layer: str = "all", count: int = 10) -> dict:
    """
    Unified search across all available layers.
    
    layer="all"     → DDG + SearXNG + scrape top result
    layer="ddg"     → DuckDuckGo Instant Answer only
    layer="searxng" → SearXNG meta-search only
    layer="scrape"  → Direct scrape of a URL (query must be a URL)
    """
    if layer == "ddg":
        return ddg_search(query)

    if layer == "searxng":
        return searxng_search(query, count=count)

    if layer == "scrape":
        if not query.startswith("http"):
            return {"error": "Scrape layer requires a URL as query"}
        return scrape_page(query)

    # Layer "all" — combine DDG + SearXNG
    result = {
        "query": query,
        "timestamp": datetime.utcnow().isoformat(),
        "layers": {},
    }

    # DDG for instant answers
    ddg = ddg_search(query)
    result["layers"]["ddg"] = ddg

    # SearXNG for full results
    searx = searxng_search(query, count=count)
    result["layers"]["searxng"] = searx

    # If SearXNG returned results, scrape the top one for full text
    if searx.get("results"):
        top_url = searx["results"][0].get("url", "")
        if top_url:
            scrape = scrape_page(top_url)
            result["layers"]["top_page"] = scrape

    return result

# ── CLI ─────────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Seymour Free Search Engine")
    parser.add_argument("query", help="Search query or URL (for scrape layer)")
    parser.add_argument("--layer", default="all", choices=["all", "ddg", "searxng", "scrape"])
    parser.add_argument("--count", type=int, default=10, help="Number of results")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--searxng-url", default=None, help="SearXNG base URL")
    args = parser.parse_args()

    if args.searxng_url:
        global SEARXNG_URL
        SEARXNG_URL = args.searxng_url

    result = search(args.query, layer=args.layer, count=args.count)

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Pretty print
        print(f"\n{'='*60}")
        print(f"  SEYMOUR SEARCH | Layer: {args.layer} | {result.get('timestamp', '')}")
        print(f"  Query: {args.query}")
        print(f"{'='*60}\n")

        if args.layer in ("all", "ddg"):
            ddg = result.get("layers", {}).get("ddg", result)
            if ddg.get("error"):
                print(f"⚠️  DDG: {ddg['error']}\n")
            else:
                if ddg.get("abstract"):
                    print(f"📖 ABSTRACT ({ddg.get('abstract_source', 'unknown')})")
                    print(f"   {ddg['abstract']}")
                    print(f"   Source: {ddg.get('abstract_url', '')}\n")
                if ddg.get("answer"):
                    print(f"💡 ANSWER: {ddg['answer']}\n")
                if ddg.get("definition"):
                    print(f"📝 DEFINITION: {ddg['definition']}\n")
                if ddg.get("type") == "D":
                    print(f"📋 DISAMBIGUATION: {ddg.get('heading', '')}\n")
                if ddg.get("related_topics"):
                    print(f"🔗 RELATED TOPICS:")
                    for rt in ddg["related_topics"][:8]:
                        text = rt['text'][:120]
                        print(f"   • {text}")
                        if rt.get("url"):
                            print(f"     {rt['url']}")
                    print()

        if args.layer in ("all", "searxng"):
            sx = result.get("layers", {}).get("searxng", result)
            if sx.get("error"):
                print(f"⚠️  SearXNG: {sx['error']}")
                print(f"    Set SEARXNG_BASE_URL or use --searxng-url\n")
            elif sx.get("results"):
                print(f"🔍 SEARCH RESULTS ({sx.get('total_results', '?')} total):")
                for i, r in enumerate(sx["results"][:args.count], 1):
                    print(f"\n  {i}. {r['title']}")
                    print(f"     {r['url']}")
                    if r.get("content"):
                        print(f"     {r['content'][:200]}")
                    if r.get("source"):
                        print(f"     [via {r['source']}]")
                print()

        if args.layer == "scrape" or (args.layer == "all" and result.get("layers", {}).get("top_page")):
            tp = result.get("layers", {}).get("top_page", result)
            if tp.get("error"):
                print(f"⚠️  Scrape: {tp['error']}\n")
            else:
                print(f"📄 TOP PAGE: {tp.get('title', '')}")
                print(f"   URL: {tp.get('url', args.query)}")
                if tp.get("description"):
                    print(f"   {tp['description']}")
                if tp.get("text"):
                    print(f"\n   {tp['text'][:1000]}...")
                print()

if __name__ == "__main__":
    main()
