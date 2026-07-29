# Install both model-router host adapters from this repository (Windows PowerShell).
# Global skill directories are build artifacts; edit this repository, then run:
#   .\sync.ps1
$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
$ClaudeSrc = Join-Path $RepoRoot ".claude\skills\model-router"
$CodexAdapter = Join-Path $ClaudeSrc "adapters\codex.md"

$UserHome = if ($HOME) { $HOME } else { $env:USERPROFILE }
$ClaudeDest = Join-Path $UserHome ".claude\skills\model-router"
$CodexDest  = Join-Path $UserHome ".agents\skills\model-router"
$LogDir     = Join-Path $UserHome ".claude\model-router"

if (-not (Test-Path (Join-Path $ClaudeSrc "SKILL.md")) -or -not (Test-Path $CodexAdapter)) {
    Write-Error "Missing a required model-router adapter under $ClaudeSrc"
    exit 1
}

# 1. Install Claude adapter (excluding adapters directory and OS metadata)
if (Test-Path $ClaudeDest) {
    Remove-Item -Recurse -Force $ClaudeDest
}
New-Item -ItemType Directory -Force -Path $ClaudeDest | Out-Null

Get-ChildItem -Path $ClaudeSrc -Exclude "adapters", ".DS_Store" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $ClaudeDest -Recurse -Force
}

# 2. Stage and install Codex adapter
$StageDir = Join-Path (if ($env:TEMP) { $env:TEMP } else { "C:\Windows\Temp" }) "model-router-codex-$([Guid]::NewGuid().ToString('N').Substring(0,8))"
if (Test-Path $StageDir) {
    Remove-Item -Recurse -Force $StageDir
}
New-Item -ItemType Directory -Force -Path (Join-Path $StageDir "references") | Out-Null

Copy-Item -Path $CodexAdapter -Destination (Join-Path $StageDir "SKILL.md") -Force
Get-ChildItem -Path (Join-Path $ClaudeSrc "references") -Exclude ".DS_Store" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination (Join-Path $StageDir "references") -Recurse -Force
}

if (Test-Path $CodexDest) {
    Remove-Item -Recurse -Force $CodexDest
}
New-Item -ItemType Directory -Force -Path $CodexDest | Out-Null
Get-ChildItem -Path $StageDir | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $CodexDest -Recurse -Force
}
Remove-Item -Recurse -Force $StageDir

# 3. Preserve machine-local state and source pointer. Shared state is configured
# separately with state.ps1 and is never copied into either installed package.
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
Set-Content -Path (Join-Path $LogDir "source-repo") -Value $RepoRoot -NoNewline

$NotesPath = Join-Path $LogDir "routing-notes.local.md"
if (-not (Test-Path $NotesPath)) {
    $NotesHeader = @"
# model-router — device-local observations

Record only facts specific to this device: CLI availability, auth/tier status,
paths, or repository quirks. Never put credentials or secrets here.

## Entries
<!-- newest first -->
"@
    Set-Content -Path $NotesPath -Value $NotesHeader
    Write-Host "Seeded device-local notes at $NotesPath"
}

Write-Host "Installed Claude adapter: $ClaudeDest"
Write-Host "Installed Codex adapter:  $CodexDest"
Write-Host "Source repo registered:   $RepoRoot"
