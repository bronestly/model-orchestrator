# Install all model-router host adapters from this repository (Windows PowerShell).
# Global skill directories are build artifacts; edit this repository, then run:
#   .\sync.ps1
$ErrorActionPreference = "Stop"

$RepoRoot = $PSScriptRoot
$ClaudeSrc = Join-Path $RepoRoot ".claude\skills\model-router"
$CodexAdapter = Join-Path $ClaudeSrc "adapters\codex.md"
$GrokAdapter = Join-Path $ClaudeSrc "adapters\grok.md"

$UserHome = if ($HOME) { $HOME } else { $env:USERPROFILE }
$ClaudeDest = Join-Path $UserHome ".claude\skills\model-router"
$CodexDest  = Join-Path $UserHome ".agents\skills\model-router"
$GrokDest   = Join-Path $UserHome ".grok\skills\model-router"
$LogDir     = Join-Path $UserHome ".claude\model-router"

if (-not (Test-Path (Join-Path $ClaudeSrc "SKILL.md")) -or -not (Test-Path $CodexAdapter) -or -not (Test-Path $GrokAdapter)) {
    Write-Error "Missing a required model-router adapter under $ClaudeSrc"
    exit 1
}

# Registry <-> allowlist posture guard (mirrors sync.sh).
# The capability registry in references/routing-reference.md owns every CLI command
# the skill prescribes and, per command, the prefix the owner pre-authorized. The
# Claude adapter's allowed-tools must list exactly those prefixes (Bash entries with
# PowerShell twins), and each prefix must start its own command. A missing entry
# means the skill prescribes a call it cannot make; an extra or shortened entry
# silently widens the permission posture. Refuse to install in either case.
$SkillPath = Join-Path $ClaudeSrc "SKILL.md"
$RegistryPath = Join-Path $ClaudeSrc "references\routing-reference.md"

# Rows of the "Invocation shapes" table: the first and second backticked spans.
$RegistryRows = @()
$InBlock = $false
foreach ($Line in Get-Content $RegistryPath) {
    if ($Line -match '^### Invocation shapes') { $InBlock = $true; continue }
    if ($InBlock -and $Line -match '^#') { $InBlock = $false }
    if ($InBlock -and $Line -match '^\|') {
        $Spans = [regex]::Matches($Line, '`([^`]+)`')
        if ($Spans.Count -ge 1) {
            $Prefix = if ($Spans.Count -ge 2) { $Spans[1].Groups[1].Value } else { "" }
            $RegistryRows += [pscustomobject]@{ Command = $Spans[0].Groups[1].Value; Prefix = $Prefix }
        }
    }
}

# Patterns: the contents of each <Kind>(...) entry, with any trailing glob removed.
# Only one "  - Bash(...)" or "  - PowerShell(...)" entry per line is understood; any
# other line in the block is returned as "unsupported: <line>" so the set comparison
# fails instead of silently skipping an entry. A bare "*" grant returns "*".
function Get-AllowPatterns([string]$Kind) {
    $Patterns = @()
    $InBlock = $false
    foreach ($Line in Get-Content $SkillPath) {
        if ($Line -match '^allowed-tools:') { $InBlock = $true; continue }
        if ($InBlock -and $Line -match '^[^ \t-]') { $InBlock = $false }
        if (-not $InBlock -or $Line -match '^[ \t]*$') { continue }
        if ($Line -cnotmatch '^  - (Bash|PowerShell)\(([^)]+)\)$') { $Patterns += "unsupported: $Line"; continue }
        if ($Matches[1] -cne $Kind) { continue }
        $Pattern = ($Matches[2] -replace '\*$', '').TrimEnd()
        $Patterns += $(if ($Pattern) { $Pattern } else { "*" })
    }
    return $Patterns
}

$Drift = $false
foreach ($Row in $RegistryRows) {
    # Trailing space on both sides keeps "agy -p" from matching "agy -print".
    if (-not $Row.Prefix -or -not ("$($Row.Command) ").StartsWith("$($Row.Prefix) ", [StringComparison]::Ordinal)) {
        Write-Host "Registry row's pre-authorized prefix does not start its command:"
        Write-Host "  command: $($Row.Command)"
        Write-Host "  prefix:  $($Row.Prefix)"
        $Drift = $true
    }
}

# The `command -v` probe is not a route, so it has no registry row.
$Expected = @(@('command -v') + @($RegistryRows | ForEach-Object { $_.Prefix } | Where-Object { $_ }) | Sort-Object -Unique -CaseSensitive)
$Sets = @{
    'Bash'       = @(Get-AllowPatterns 'Bash' | Sort-Object -Unique -CaseSensitive)
    'PowerShell' = @(Get-AllowPatterns 'PowerShell' | ForEach-Object { if ($_ -ceq 'Get-Command') { 'command -v' } else { $_ } } | Sort-Object -Unique -CaseSensitive)
}
foreach ($Kind in 'Bash', 'PowerShell') {
    $Delta = Compare-Object -ReferenceObject $Expected -DifferenceObject $Sets[$Kind] -CaseSensitive
    if ($Delta) {
        Write-Host "SKILL.md $Kind(...) allowed-tools differ from the registry's pre-authorized prefixes"
        Write-Host "  (< registry, > SKILL.md; PowerShell Get-Command shown as command -v):"
        foreach ($D in $Delta) {
            $Side = if ($D.SideIndicator -eq '<=') { '<' } else { '>' }
            Write-Host "  $Side $($D.InputObject)"
        }
        $Drift = $true
    }
}

if ($Drift) {
    Write-Host "Widening a prefix is the owner's decision; make it in the registry first."
    Write-Error "Refusing to install: routing-reference.md and SKILL.md disagree."
    exit 1
}

# Agent-definition <-> registry guard (mirrors sync.sh). Each native agent definition
# pins a model ID, which must appear in the registry's host-native table.
$AgentsSrc = Join-Path $ClaudeSrc "agents"
$AgentsDest = Join-Path $UserHome ".claude\agents"
# Model IDs: the backticked second column of the host-native table only.
$NativeModels = @()
$InNative = $false
foreach ($Line in Get-Content $RegistryPath) {
    if ($Line -cmatch '^\| Codename \| Model ID \|') { $InNative = $true; continue }
    if ($InNative -and $Line -notmatch '^\|') { break }
    if ($InNative -and $Line.Split('|')[2] -match '`([^`]+)`') { $NativeModels += $Matches[1] }
}
$AgentFiles = @(Get-ChildItem -Path $AgentsSrc -Filter "mr-*.md" -ErrorAction SilentlyContinue)
if ($AgentFiles.Count -eq 0) {
    Write-Error "Refusing to install: no mr-*.md agent definitions under $AgentsSrc."
    exit 1
}
foreach ($Agent in $AgentFiles) {
    $ModelLine = Get-Content $Agent.FullName | Where-Object { $_ -match '^model:\s*(\S+)' } | Select-Object -First 1
    $Model = if ($ModelLine -and $ModelLine -match '^model:\s*(\S+)') { $Matches[1] } else { "" }
    if (-not $Model -or $NativeModels -cnotcontains $Model) {
        Write-Host "Agent definition pins a model the registry does not list:"
        Write-Host "  agent: $($Agent.FullName)"
        Write-Host "  model: $Model"
        Write-Error "Refusing to install: add it to the host-native table or fix the definition."
        exit 1
    }
}

# 1. Install Claude adapter (excluding adapters directory and OS metadata)
if (Test-Path $ClaudeDest) {
    Remove-Item -Recurse -Force $ClaudeDest
}
New-Item -ItemType Directory -Force -Path $ClaudeDest | Out-Null

Get-ChildItem -Path $ClaudeSrc -Exclude "adapters", ".DS_Store" | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $ClaudeDest -Recurse -Force
}

# 1b. Native Claude agent definitions. Only the mr-* prefix is owned here.
New-Item -ItemType Directory -Force -Path $AgentsDest | Out-Null
Get-ChildItem -Path $AgentsDest -Filter "mr-*.md" | Remove-Item -Force
Get-ChildItem -Path $AgentsSrc -Filter "mr-*.md" | Copy-Item -Destination $AgentsDest -Force

# 2. Stage and install Codex and Grok adapters
function Install-HostAdapter {
    param(
        [string]$AdapterSrc,
        [string]$Dest,
        [string]$Label
    )
    $TempRoot = if ($env:TEMP) { $env:TEMP } else { "C:\Windows\Temp" }
    $StageDir = Join-Path $TempRoot "model-router-$Label-$([Guid]::NewGuid().ToString('N').Substring(0,8))"
    if (Test-Path $StageDir) {
        Remove-Item -Recurse -Force $StageDir
    }
    New-Item -ItemType Directory -Force -Path (Join-Path $StageDir "references") | Out-Null

    Copy-Item -Path $AdapterSrc -Destination (Join-Path $StageDir "SKILL.md") -Force
    Get-ChildItem -Path (Join-Path $ClaudeSrc "references") -Exclude ".DS_Store" | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination (Join-Path $StageDir "references") -Recurse -Force
    }

    if (Test-Path $Dest) {
        Remove-Item -Recurse -Force $Dest
    }
    New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    Get-ChildItem -Path $StageDir | ForEach-Object {
        Copy-Item -Path $_.FullName -Destination $Dest -Recurse -Force
    }
    Remove-Item -Recurse -Force $StageDir
}

Install-HostAdapter -AdapterSrc $CodexAdapter -Dest $CodexDest -Label "codex"
Install-HostAdapter -AdapterSrc $GrokAdapter -Dest $GrokDest -Label "grok"

# Post-install check (mirrors sync.sh): every installed package must match its source
# exactly, so a copy or path error fails here instead of shipping broken links.
# A manifest line is "<relative path> <sha256>" or "<relative dir>/ <dir>"; $Under prefixes each path.
function Get-TreeManifest([string]$Root, [string[]]$ExcludeTop = @(), [string]$Under = "") {
    if (-not (Test-Path $Root)) { return @() }
    $RootFull = (Resolve-Path $Root).Path.TrimEnd('\', '/')
    # Directories are listed too, so an unexpected empty directory is caught.
    Get-ChildItem -Path $Root -Recurse -Force |
        Where-Object { $_.Name -ne '.DS_Store' } |
        ForEach-Object {
            $Rel = $_.FullName.Substring($RootFull.Length + 1) -replace '\\', '/'
            if ($ExcludeTop -notcontains ($Rel -split '/')[0]) {
                if ($_.PSIsContainer) { "$Under$Rel/ <dir>" }
                else { "$Under$Rel $((Get-FileHash $_.FullName -Algorithm SHA256).Hash)" }
            }
        }
}
function Get-FileManifestLine([string]$Path, [string]$Name) {
    if (-not (Test-Path $Path -PathType Leaf)) { return "$Name <missing or not a file>" }
    return "$Name $((Get-FileHash $Path -Algorithm SHA256).Hash)"
}
$InstallMismatch = $false
function Test-SameManifest([string]$Label, [string]$Dest, [string[]]$Expected, [string[]]$Actual) {
    # Windows PowerShell 5.1's Compare-Object rejects an empty collection.
    if (-not $Actual) { $Actual = @("<nothing installed>") }
    $Delta = Compare-Object -ReferenceObject @($Expected | Sort-Object) -DifferenceObject @($Actual | Sort-Object) -CaseSensitive
    if ($Delta) {
        Write-Host "Installed $Label does not match its source: $Dest"
        foreach ($D in $Delta) { Write-Host "  $($D.SideIndicator) $($D.InputObject)" }
        $script:InstallMismatch = $true
    }
}
Test-SameManifest "Claude package" $ClaudeDest @(Get-TreeManifest $ClaudeSrc @("adapters")) @(Get-TreeManifest $ClaudeDest)
foreach ($HostPkg in @(@{ Label = "codex"; Adapter = $CodexAdapter; Dest = $CodexDest }, @{ Label = "grok"; Adapter = $GrokAdapter; Dest = $GrokDest })) {
    $Expected = @(Get-FileManifestLine $HostPkg.Adapter "SKILL.md") + @("references/ <dir>") + @(Get-TreeManifest (Join-Path $ClaudeSrc "references") @() "references/")
    Test-SameManifest "$($HostPkg.Label) package" $HostPkg.Dest $Expected @(Get-TreeManifest $HostPkg.Dest)
}
foreach ($Agent in $AgentFiles) {
    $Installed = Join-Path $AgentsDest $Agent.Name
    Test-SameManifest "agent $($Agent.Name)" $Installed @(Get-FileManifestLine $Agent.FullName $Agent.Name) @(Get-FileManifestLine $Installed $Agent.Name)
}
if ($InstallMismatch) {
    Write-Error "Install verification failed; fix sync.ps1 or the source tree and rerun."
    exit 1
}

# 3. Preserve machine-local state and source pointer. Shared state is configured
# separately with state.ps1 and is never copied into an installed package.
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
Write-Host "Installed Grok adapter:   $GrokDest"
Write-Host "Installed agents:         $AgentsDest\mr-*.md"
Write-Host "Source repo registered:   $RepoRoot"
