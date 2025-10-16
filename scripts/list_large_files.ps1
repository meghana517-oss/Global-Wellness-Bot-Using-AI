<#
Lists files larger than a threshold (default 10 MB) to help identify large artifacts before pushing.
Usage:
    .\scripts\list_large_files.ps1 -ThresholdMB 50
#>
param(
    [int]$ThresholdMB = 10
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

Write-Host "Scanning for files larger than $ThresholdMB MB..." -ForegroundColor Cyan
Get-ChildItem -Recurse -File | Where-Object { ($_.Length / 1MB) -gt $ThresholdMB } | Sort-Object Length -Descending | Select-Object FullName, @{Name='SizeMB';Expression={[math]::Round($_.Length/1MB,2)}} | Format-Table -AutoSize
