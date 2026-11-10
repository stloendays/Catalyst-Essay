# One-click download of the new-reaction papers through nus-fetch.
# Usage (PowerShell):  & "D:\论文-AI4S\wt-newrxn\agent\new_reactions\downloads\run_downloads.ps1"
#                      & "...\run_downloads.ps1" -Reactions rwgs          (one reaction only)
# Per reaction: 1) automatic download (open access + NUS proxy, no window needed);
#               2) assist: the papers still missing open one by one in nus-fetch's own Chrome window -
#                  you only pass the human check (Elsevier etc.); the PDF is found, DOI-checked and filed for you;
#               3) the check at the end lists what is still missing.
param(
    [string[]]$Reactions = @("nh3dec", "rwgs", "etoh"),
    [int]$CheckTimeout = 600
)
$ErrorActionPreference = "Continue"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $here
$nf = "D:\Tools\nus-fetch\nus-fetch.cmd"
$py = "D:\Research\CatalystForge\.venv\Scripts\python.exe"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "== NUS login check" -ForegroundColor Cyan
$st = & $nf status 2>&1 | Out-String
if ($st -notmatch "有效|valid") {
    Write-Host "Session expired: logging in (confirm MFA on your phone)..." -ForegroundColor Yellow
    & $nf login --timeout 600
}

foreach ($r in $Reactions) {
    $list = Join-Path $here "${r}_dois.txt"
    $out = Join-Path $root "pdf\$r"
    if (-not (Test-Path $list)) { Write-Host "missing $list" -ForegroundColor Red; continue }
    New-Item -ItemType Directory -Force $out | Out-Null
    Write-Host "`n== $r : automatic download -> $out" -ForegroundColor Cyan
    & $nf fetch -f $list -o $out
    & $py (Join-Path $root "check_downloads.py") $r | Out-Null
    $missing = Join-Path $here "${r}_missing.txt"
    if ((Get-Content $missing | Where-Object { $_.Trim() }).Count -gt 0) {
        Write-Host "`n== $r : assist (pass the human check in the nus-fetch Chrome window when it comes to the front)" -ForegroundColor Cyan
        & $nf assist -f $missing -o $out --check-timeout $CheckTimeout
    }
}

Write-Host "`n== check" -ForegroundColor Cyan
& $py (Join-Path $root "check_downloads.py") @Reactions
