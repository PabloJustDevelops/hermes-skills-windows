<#
.SYNOPSIS
    Installs the ported skills of this repository into a Hermes Agent profile.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install.ps1 -Profile research
    powershell -ExecutionPolicy Bypass -File install.ps1 -Profile devsecops
    powershell -ExecutionPolicy Bypass -File install.ps1 -Profile default

.NOTES
    Skills are loaded per session: start a new Hermes session afterwards.
    Existing files are overwritten - the ported SKILL.md is the point of this repo.
#>
param(
    [string]$Profile = "default",
    [string]$HermesHome = "$env:LOCALAPPDATA\hermes"
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

if ($Profile -eq "default") {
    $skillsDir = Join-Path $HermesHome "skills"
} else {
    $skillsDir = Join-Path $HermesHome "profiles\$Profile\skills"
}

if (-not (Test-Path $skillsDir)) {
    throw "skills directory not found: $skillsDir (is the profile name right?)"
}

# skill name -> category folder inside the profile's skills dir
$targets = @{
    "searxng-search"        = "research"
    "web-pentest"           = "security"
    "research-paper-writing" = "research"
}

foreach ($skill in $targets.Keys) {
    $dest = Join-Path $skillsDir (Join-Path $targets[$skill] $skill)
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    Copy-Item -Path (Join-Path $root "skills\$skill\*") -Destination $dest -Recurse -Force
    Write-Host "[ok] $skill -> $dest"
}

Write-Host ""
Write-Host "Installed into profile '$Profile'. Start a new Hermes session, then check with:"
Write-Host "  hermes -p $Profile skills list --enabled-only"
