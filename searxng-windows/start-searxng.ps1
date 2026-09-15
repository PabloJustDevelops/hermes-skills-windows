# Starts a private SearXNG on 127.0.0.1:8888 with the JSON API enabled.
#
# Expected layout: this script sits in the SearXNG checkout root, next to
# settings.yml and .venv\ (see searxng-windows/README.md).
#
#   powershell -ExecutionPolicy Bypass -File start-searxng.ps1
#
$ErrorActionPreference = "Stop"

$root = $PSScriptRoot
$settings = Join-Path $root "settings.yml"
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $settings)) {
    throw "settings.yml not found in $root - copy settings.example.yml to settings.yml first."
}
if (-not (Test-Path $python)) {
    throw "venv not found: $python - create it first (uv venv --python 3.11 .venv)."
}

$env:SEARXNG_SETTINGS_PATH = $settings
Set-Location $root

# Must run as a module from the checkout root: `python searx\webapp.py` would put
# searx\ on sys.path and die with ModuleNotFoundError: No module named 'searx'.
& $python -m searx.webapp
