# Configure and explicitly synchronize a private model-router state checkout.
$ErrorActionPreference = "Stop"

$UserHome = if ($HOME) { $HOME } else { $env:USERPROFILE }
$LogDir = Join-Path $UserHome ".claude\model-router"
$Pointer = Join-Path $LogDir "state-repo"
$DeviceFile = Join-Path $LogDir "device-id"

function Show-Usage {
    Write-Error "Usage: .\state.ps1 configure <state-repo> | pull | push | status"
}

function Get-StateRepo {
    if (-not (Test-Path $Pointer)) {
        throw "Shared state is not configured; run: .\state.ps1 configure <state-repo>"
    }
    $Repo = (Get-Content -Raw $Pointer).Trim()
    if (-not (Test-Path (Join-Path $Repo ".git")) -or -not (Test-Path (Join-Path $Repo "calibration.md"))) {
        throw "Configured state checkout is invalid: $Repo"
    }
    return $Repo
}

if ($args.Count -lt 1) {
    Show-Usage
}

switch ($args[0]) {
    "configure" {
        if ($args.Count -ne 2) { Show-Usage }
        $Repo = (Resolve-Path $args[1]).Path
        if (-not (Test-Path (Join-Path $Repo ".git")) -or -not (Test-Path (Join-Path $Repo "calibration.md"))) {
            throw "State checkout must be a Git repository containing calibration.md: $Repo"
        }
        New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
        Set-Content -NoNewline -Path $Pointer -Value $Repo
        if (-not (Test-Path $DeviceFile) -or (Get-Item $DeviceFile).Length -eq 0) {
            $Device = $env:COMPUTERNAME.ToLowerInvariant() -replace "[^a-z0-9._-]+", "-"
            Set-Content -NoNewline -Path $DeviceFile -Value $Device.Trim("-")
        }
        Write-Host "Configured shared state: $Repo"
        Write-Host "Device id: $((Get-Content -Raw $DeviceFile).Trim())"
    }
    "pull" {
        if ($args.Count -ne 1) { Show-Usage }
        $Repo = Get-StateRepo
        if (git -C $Repo status --porcelain) {
            throw "State checkout has local changes; push them before pulling."
        }
        git -C $Repo pull --rebase
    }
    "push" {
        if ($args.Count -ne 1) { Show-Usage }
        $Repo = Get-StateRepo
        $Device = (Get-Content -Raw $DeviceFile).Trim()
        $Timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        git -C $Repo add -- calibration.md events archive
        git -C $Repo diff --cached --quiet
        if ($LASTEXITCODE -ne 0) {
            git -C $Repo commit -m "sync routing state: $Device $Timestamp"
        }
        git -C $Repo pull --rebase
        git -C $Repo push
    }
    "status" {
        if ($args.Count -ne 1) { Show-Usage }
        git -C (Get-StateRepo) status -sb
    }
    default {
        Show-Usage
    }
}
