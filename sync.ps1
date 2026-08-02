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

# Registry <-> allowlist drift guard (mirrors sync.sh).
# The capability registry in references/routing-reference.md owns every CLI command
# the skill prescribes. If one is not pre-authorized in the Claude adapter's
# allowed-tools, the skill prescribes a call it cannot make. Refuse to install.
$SkillPath = Join-Path $ClaudeSrc "SKILL.md"
$RegistryPath = Join-Path $ClaudeSrc "references\routing-reference.md"

# Commands: the first backticked span of each row in the "Invocation shapes" table.
$RegistryCommands = @()
$InBlock = $false
foreach ($Line in Get-Content $RegistryPath) {
    if ($Line -match '^### Invocation shapes') { $InBlock = $true; continue }
    if ($InBlock -and $Line -match '^#') { $InBlock = $false }
    if ($InBlock -and $Line -match '^\|' -and $Line -match '`([^`]+)`') {
        $RegistryCommands += $Matches[1]
    }
}

# Patterns: the contents of each Bash(...) entry, with any trailing glob removed.
$AllowPatterns = @()
$InBlock = $false
foreach ($Line in Get-Content $SkillPath) {
    if ($Line -match '^allowed-tools:') { $InBlock = $true; continue }
    if ($InBlock -and $Line -match '^[^ \t-]') { $InBlock = $false }
    if ($InBlock -and $Line -match 'Bash\(([^)]*)\)') {
        $Pattern = $Matches[1] -replace '\*$', ''
        $Pattern = $Pattern.TrimEnd()
        if ($Pattern) { $AllowPatterns += $Pattern }
    }
}

$Drift = $false
foreach ($Command in $RegistryCommands) {
    # Compare only the concrete prefix — everything before the first <placeholder>.
    $Tokens = @()
    foreach ($Token in ($Command -split '\s+')) {
        if ($Token.Contains('<')) { break }
        $Tokens += $Token
    }
    if ($Tokens.Count -eq 0) { continue }
    $Concrete = $Tokens -join ' '

    $Authorized = $false
    foreach ($Pattern in $AllowPatterns) {
        # Trailing space on both sides keeps "agy -p" from matching "agy -print".
        if (("$Concrete ").StartsWith("$Pattern ")) { $Authorized = $true; break }
    }

    if (-not $Authorized) {
        Write-Host "Registry command is not in the Claude adapter's allowed-tools:"
        Write-Host "  registry: $Concrete"
        Write-Host "  fix:      add 'Bash($Concrete *)' to SKILL.md, with its PowerShell twin."
        Write-Host "            Any shorter prefix of that command also satisfies the guard;"
        Write-Host "            prefer the shortest one that stays unambiguous."
        $Drift = $true
    }
}

if ($Drift) {
    Write-Error "Refusing to install: routing-reference.md and SKILL.md disagree."
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
