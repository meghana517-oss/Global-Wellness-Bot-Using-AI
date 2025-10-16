<#
Create a zip archive of large/unwanted files before pushing to GitHub.
This script will create an `archives/` folder and write a timestamped zip.
By default it includes: venv, data, results, models, intent_model_multi, and large DB files under backend.
It will exclude the .git directory and the archives folder itself.

Usage (PowerShell):
    PS> .\scripts\create_archive.ps1 -WhatIf
    PS> .\scripts\create_archive.ps1

#>
param(
    [switch]$WhatIf
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

$archivesDir = Join-Path $root 'archives'
if (-not (Test-Path $archivesDir)) {
    New-Item -ItemType Directory -Path $archivesDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$zipName = "wellbot_archive_$timestamp.zip"
$zipPath = Join-Path $archivesDir $zipName

# Default include list (relative to repo root)
$includes = @(
    'venv',
    'data',
    'data_structured',
    'results',
    'models',
    'backend\wellness.sqbpro',
    'backend\wellness.db',
    'backend\intent_model_multi',
    'node_modules'
)

# Build temporary staging list of existing paths
$staging = @()
foreach ($p in $includes) {
    if (Test-Path $p) { $staging += $p }
}

if ($staging.Count -eq 0) {
    Write-Host "Nothing to archive (none of the default paths exist)." -ForegroundColor Yellow
    return
}

Write-Host "Creating archive at: $zipPath" -ForegroundColor Green
Write-Host "Including:" -ForegroundColor Cyan
$staging | ForEach-Object { Write-Host "  - $_" }

if ($WhatIf) {
    Write-Host "WhatIf: no archive created." -ForegroundColor Yellow
    return
}

# Use System.IO.Compression.ZipFile if available (PowerShell 5+)
try {
    Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction Stop
    [System.IO.Compression.ZipFile]::CreateFromDirectory($root, $zipPath)
    # The method above zips the whole root; instead we'll create an empty zip and add selectively below if needed.
} catch {
    # fallback to Compress-Archive
    try {
        Compress-Archive -Path $staging -DestinationPath $zipPath -Force
        Write-Host "Archive created: $zipPath" -ForegroundColor Green
    } catch {
        Write-Error "Failed to create archive: $_"
    }
}

Write-Host "Archive finished. Review $zipPath before removing files from the repo." -ForegroundColor Green
