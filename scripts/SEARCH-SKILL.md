# Seymour Free Search Engine

## Purpose
Multi-layered web search that avoids API key usage. Three layers:

1. **DuckDuckGo Instant Answer API** — No key needed. Instant facts, definitions, related topics.
2. **SearXNG** — Self-hosted meta-search aggregating Google/Bing/DDG. No key, unlimited.
3. **Direct web scraping** — Fallback for specific pages. urllib + regex, no dependencies.

## Usage

```bash
# DuckDuckGo only (works out of the box)
python3 scripts/search.py "query" --layer ddg

# Full search (requires SearXNG instance)
python3 scripts/search.py "query" --layer all

# Scrape a specific URL
python3 scripts/search.py "https://example.com" --layer scrape

# JSON output
python3 scripts/search.py "query" --layer ddg --json

# Custom SearXNG URL
python3 scripts/search.py "query" --layer searxng --searxng-url http://localhost:8080
```

## Setup

### DuckDuckGo (Layer 1)
No setup required. Works immediately.

### SearXNG (Layer 2)
```bash
# Docker (simplest)
docker run -d -p 8080:8080 searxng/searxng

# Or set environment variable
export SEARXNG_BASE_URL="http://localhost:8080"
```

### Scraping (Layer 3)
No setup required. Uses Python stdlib only.

## Caching
Results are cached for 1 hour in `.search-cache/`. Cache key is MD5 of layer+query.

## Integration with Hermes
This tool is available for research tasks. Use it instead of web_search when:
- You need to avoid API key usage
- You need full page content (scrape layer)
- You need instant facts/definitions (DDG layer)
- You need comprehensive web search (SearXNG layer)
