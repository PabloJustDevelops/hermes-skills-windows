#!/usr/bin/env python3
"""Meta-search through SearXNG (a keyless aggregator over 70+ engines).

Windows port of the original `searxng.sh` (bash): no bash, no third-party packages,
and an instance order that actually works.

Usage:
    python searxng.py "query" [max_results] [engines] [--url INSTANCE] [--json]

Examples:
    python searxng.py "python async" 10
    python searxng.py "nextjs workers" 5 google,bing --url http://127.0.0.1:8888
    python searxng.py "insforge rls" --json

Instances: `$SEARXNG_URL` is used when set; otherwise the LOCAL instance
(http://127.0.0.1:8888, started with `start-searxng.ps1`) comes first, then a couple
of public ones.

Note: public SearXNG instances now sit behind anti-bot walls (Cloudflare "Verifying
your browser", Anubis proof-of-work, Substation). They answer 200 with a challenge
page instead of results — a browser user agent does not change that, and neither does
a headless browser. For real results run a self-hosted instance (JSON API enabled) or
point `SEARXNG_URL` at your own.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

LOCAL_INSTANCE = "http://127.0.0.1:8888"
PUBLIC_INSTANCES = [  # last resort only; today these serve anti-bot walls
    "https://searx.be",
    "https://search.inetol.net",
    "https://baresearch.org",
]
DEFAULT_INSTANCES = [LOCAL_INSTANCE, *PUBLIC_INSTANCES]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) hermes-searxng/1.2"
TIMEOUT = 20

START_HINT = ("start the local instance: "
              r"powershell -ExecutionPolicy Bypass -File $env:USERPROFILE\searxng\start-searxng.ps1")


def _query(instance: str, query: str, limit: int, engines: str) -> dict:
    params = {"q": query, "format": "json", "limit": str(limit)}
    if engines:
        params["engines"] = engines
    url = f"{instance.rstrip('/')}/search?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        raw = resp.read().decode("utf-8", "replace")
    data = json.loads(raw)
    if not isinstance(data, dict) or "results" not in data:
        raise ValueError("response has no 'results'")
    return data


def search(query: str, limit: int = 5, engines: str = "", instance: str = "") -> dict:
    """Return {'instance': ..., 'results': [...]}, trying each instance in order."""
    if instance:
        candidates = [instance]
    elif os.environ.get("SEARXNG_URL"):
        candidates = [os.environ["SEARXNG_URL"]]
    else:
        candidates = DEFAULT_INSTANCES
    errors = []
    for cand in candidates:
        try:
            data = _query(cand, query, limit, engines)
            results = data.get("results", [])[:limit]
            if not results:
                errors.append(f"{cand}: answered but returned no results")
                continue
            return {"instance": cand, "results": results,
                    "number_of_results": data.get("number_of_results")}
        except Exception as exc:  # instance down, anti-bot wall or JSON disabled
            errors.append(f"{cand}: {type(exc).__name__}: {exc}")
    raise RuntimeError("no SearXNG instance returned usable results:\n  "
                       + "\n  ".join(errors) + f"\n  -> {START_HINT}")


def _fmt(data: dict) -> str:
    out = [f"# {len(data['results'])} results via {data['instance']}"]
    for i, r in enumerate(data["results"], 1):
        title = (r.get("title") or "").strip()
        url = (r.get("url") or "").strip()
        content = " ".join((r.get("content") or "").split())[:280]
        engine = r.get("engine") or ""
        out.append(f"{i}. {title}\n   {url}\n   [{engine}] {content}")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    args = [a for a in argv if not a.startswith("--")]
    flags = {a for a in argv if a.startswith("--")}
    if not args:
        print(__doc__)
        return 2
    query = args[0]
    limit = int(args[1]) if len(args) > 1 else 5
    engines = args[2] if len(args) > 2 else ""
    instance = ""
    for flag in flags:
        if flag.startswith("--url="):
            instance = flag.split("=", 1)[1]
    if "--url" in argv:
        try:
            instance = argv[argv.index("--url") + 1]
        except IndexError:
            print("--url needs a value", file=sys.stderr)
            return 2
    try:
        data = search(query, limit, engines, instance)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(data, ensure_ascii=False, indent=1) if "--json" in flags else _fmt(data))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
