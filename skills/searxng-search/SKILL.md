---
name: searxng-search
description: Free keyless meta-search aggregating 70+ engines.
version: 1.0.1
author: hermes-agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [search, searxng, meta-search, self-hosted, free, fallback]
    related_skills: [duckduckgo-search, domain-intel]
    fallback_for_toolsets: [web]
---

# SearXNG Search

Free meta-search using [SearXNG](https://searxng.org/) — a privacy-respecting, self-hosted search aggregator that queries 70+ search engines simultaneously.

**No API key required** when using a public instance. Can also be self-hosted for full control. Automatically appears as a fallback when the main web search toolset (`FIRECRAWL_API_KEY`) is not configured.

## Configuration

`scripts/searxng.py` needs no bash and no third-party packages, and tries instances in
this order: `$SEARXNG_URL` (if set), the **local** instance `http://127.0.0.1:8888`,
then a couple of public ones.

```powershell
# Local instance (recommended): self-hosted SearXNG on 127.0.0.1:8888 with the JSON API enabled
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\searxng\start-searxng.ps1"

# Optional: pin another instance
SEARXNG_URL=http://other-instance:8888
```

**Heads-up about public instances**: they are no longer usable for automation. We
probed ~28 of them (searx.be, search.inetol.net, baresearch.org, searx.tiekoetter.com,
priv.au, opnxng.com, ...) and every single one answers 200 with an anti-bot page —
Cloudflare "Verifying your browser", Anubis (proof-of-work) or Substation — instead of
results. `format=json` is disabled on almost all of them, and a headless browser does
not get through either. That is why the practical path is a self-hosted instance; see
the `searxng-windows/` setup that ships with this port.

## Detection Flow

Check what is actually available before choosing an approach:

```bash
# Windows / linux / macOS — one call; prints which instance answered
python scripts/searxng.py "test" 2
```

Decision tree:
1. An instance (local or `$SEARXNG_URL`) answers JSON with results → use SearXNG
2. The local instance is not running → start it with `start-searxng.ps1`
3. Only public instances available → do not insist over HTTP: use the `web`/`browser`
   toolset or the `duckduckgo-search` skill instead

## Method 1: Python client (preferred — works on Windows, linux and macOS)

No bash, no dependencies beyond the standard library. This is the Windows replacement
for the original `searxng.sh`.

```bash
python scripts/searxng.py "python async programming" 10 google,bing
python scripts/searxng.py "insforge rls" 5 "" --url http://127.0.0.1:8888
python scripts/searxng.py "AI news" --json                        # raw JSON
```

It prints numbered results (title, URL, engine, snippet) and exits non-zero with the
per-instance error list plus the start hint when every instance fails. Rate-limit
yourself: one call per distinct query, no loops hammering an instance.

### curl alternative (any OS with curl)

```bash
curl -s --max-time 10 \
  "http://127.0.0.1:8888/search?q=python+async+programming&format=json&engines=google,bing&limit=10"
```

### Common CLI Flags

| Flag | Description | Example |
|------|-------------|---------|
| `q` | Query string (URL-encoded) | `q=python+async` |
| `format` | Output format: `json`, `csv`, `rss` | `format=json` |
| `engines` | Comma-separated engine names | `engines=google,bing,ddg` |
| `limit` | Max results per engine (default 10) | `limit=5` |
| `categories` | Filter by category | `categories=news,science` |
| `safesearch` | 0=none, 1=moderate, 2=strict | `safesearch=0` |
| `time_range` | Filter: `day`, `week`, `month`, `year` | `time_range=week` |

### Parsing JSON Results

```bash
# Extract titles and URLs from JSON
curl -s --max-time 10 "${SEARXNG_URL}/search?q=fastapi&format=json&limit=5" \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for r in data.get('results', []):
    print(r.get('title',''))
    print(r.get('url',''))
    print(r.get('content','')[:200])
    print()
"
```

Returns per result: `title`, `url`, `content` (snippet), `engine`, `parsed_url`, `img_src`, `thumbnail`, `author`, `published_date`

## Method 2: Python API via `requests`

Use the SearXNG REST API directly from Python with the `requests` library:

```python
import os, requests, urllib.parse

base_url = os.environ.get("SEARXNG_URL", "")
if not base_url:
    raise RuntimeError("SEARXNG_URL is not set")

query = "fastapi deployment guide"
params = {
    "q": query,
    "format": "json",
    "limit": 5,
    "engines": "google,bing",
}

resp = requests.get(f"{base_url}/search", params=params, timeout=10)
resp.raise_for_status()
data = resp.json()

for r in data.get("results", []):
    print(r["title"])
    print(r["url"])
    print(r.get("content", "")[:200])
    print()
```

## Self-Hosting SearXNG

To run your own SearXNG instance:

```bash
# Using Docker
docker run -d -p 8888:8080 \
  -v $(pwd)/searxng:/etc/searxng \
  searxng/searxng:latest

# Then set
SEARXNG_URL=http://localhost:8888
```

Or install via pip:
```bash
pip install searxng
# Edit /etc/searxng/settings.yml
searxng-run
```

Public SearXNG instances are available at:
- `https://searxng.example.com` (replace with any public instance)

## Workflow: Search then Extract

SearXNG returns titles, URLs, and snippets — not full page content. To get full page content, search first and then extract the most relevant URL with `web_extract`, browser tools, or `curl`.

```bash
# Search for relevant pages
curl -s "${SEARXNG_URL}/search?q=fastapi+deployment&format=json&limit=3"
# Output: list of results with titles and URLs

# Then extract the best URL with web_extract
```

## Limitations

- **Instance availability**: If the SearXNG instance is down or unreachable, search fails. Always check `SEARXNG_URL` is set and the instance is reachable.
- **No content extraction**: SearXNG returns snippets, not full page content. Use `web_extract`, browser tools, or `curl` for full articles.
- **Rate limiting**: Some public instances limit requests. Self-hosting avoids this.
- **Engine coverage**: Available engines depend on the SearXNG instance configuration. Some engines may be disabled.
- **Results freshness**: Meta-search aggregates external engines — result freshness depends on those engines.

## Troubleshooting

| Problem | Likely Cause | What To Do |
|---------|--------------|------------|
| `SEARXNG_URL` not set | No instance configured | Use a public SearXNG instance or set up your own |
| Connection refused | Instance not running or wrong URL | Check the URL is correct and the instance is running |
| Empty results | Instance blocks the query | Try a different instance or self-host |
| Slow responses | Public instance under load | Self-host or use a less-loaded public instance |
| `json` format not supported | Old SearXNG version | Try `format=rss` or upgrade SearXNG |

## Pitfalls

- **Always set `SEARXNG_URL`**: Without it, the skill cannot function.
- **URL-encode queries**: Spaces and special characters must be URL-encoded in curl, or use `urllib.parse.quote()` in Python.
- **Use `format=json`**: The default format may not be machine-readable. Always request JSON explicitly.
- **Set a timeout**: Always use `--max-time` or `timeout=` to avoid hanging on unreachable instances.
- **Self-hosting is best**: Public instances may go down, rate-limit, or block. A self-hosted instance is reliable.

## Instance Discovery

If `SEARXNG_URL` is not set and the user asks about SearXNG, help them either:
1. Find a public SearXNG instance (search for "public searxng instance")
2. Set up their own with Docker or pip

Public instances are listed at: https://searxng.org/
