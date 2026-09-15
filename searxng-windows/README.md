# SearXNG on Windows (private instance, JSON API enabled)

Why this folder exists: the `searxng-search` skill needs a SearXNG that answers
`/search?...&format=json`. Public instances stopped doing that (they serve Cloudflare /
Anubis / Substation anti-bot pages — see the root README), so the working setup is your
own instance. It also needs a **source patch** to start on Windows at all.

## 1. Clone and patch

```powershell
git clone --depth 1 https://github.com/searxng/searxng "$env:USERPROFILE\searxng"
cd "$env:USERPROFILE\searxng"
git config core.longpaths true          # some paths in the tree exceed MAX_PATH
git apply path\to\windows-port.patch    # the `pwd` fix, see below
```

`windows-port.patch` is the whole Windows port: `searx/valkeydb.py` imports the `pwd`
module at import time and uses `pwd.getpwuid(os.getuid())` for a log prefix — neither
exists on Windows. The patch makes the import optional and skips the prefix. Without it,
startup dies with `ModuleNotFoundError: No module named 'pwd'` (the module is reached
through `searx/limiter.py`, so disabling the limiter is not enough).

Re-apply the patch after every `git pull` of SearXNG.

## 2. Virtualenv and dependencies

```powershell
cd "$env:USERPROFILE\searxng"
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
uv pip install --python .venv\Scripts\python.exe tzdata   # Windows has no system tz database
```

`tzdata` matters: without it the engines that use `ZoneInfo` (bilibili, torch, …) fail
to register with `ZoneInfoNotFoundError` at startup.

## 3. Settings

Copy `settings.example.yml` to `settings.yml` in the checkout root and edit the
`secret_key`. That file is what turns the JSON API on:

```yaml
server:
  limiter: false        # no bot detection for a private, localhost-only instance
  public_instance: false
  bind_address: "127.0.0.1"
  port: 8888
search:
  formats:
    - html
    - json
```

## 4. Run it

Copy `start-searxng.ps1` and `start-searxng.vbs` next to `settings.yml` (the checkout
root) and:

```powershell
powershell -ExecutionPolicy Bypass -File start-searxng.ps1
# or silently, no console window:
wscript start-searxng.vbs
```

Note the `-m` form inside the script: `python searx\webapp.py` fails with
`ModuleNotFoundError: No module named 'searx'` because the script's own directory lands
on `sys.path` instead of the repo root. `python -m searx.webapp` from the checkout root
is the correct invocation.

Check it:

```powershell
curl.exe -s "http://127.0.0.1:8888/search?q=test&format=json&limit=2"
```

## 5. Start at login (optional)

Put a shortcut to `start-searxng.vbs` in `shell:startup` (Win+R → `shell:startup`).
A `schtasks /SC ONLOGON` task needs elevation, the Startup folder does not.

## Uninstall

Remove the Startup shortcut and the checkout directory. Nothing else is touched — no
service, no registry keys, no system-wide install.
