param(
    [string]$HarnessRoot = "D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AuditDir = $PSScriptRoot
$RunScript = Join-Path $AuditDir "run_exact_scaling_lifecycle_surface.py"
$ValidateScript = Join-Path $AuditDir "validate_strict_scaling_lifecycle_result.py"

if (-not (Test-Path $HarnessRoot)) {
    $Alt = Join-Path $HOME "mnt\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1"
    if (Test-Path $Alt) {
        $HarnessRoot = $Alt
    } else {
        throw "Frozen harness not found. Checked: $HarnessRoot and $Alt"
    }
}

$HarnessCore = Join-Path $HarnessRoot "harness_core.py"
$CanonicalRun = Join-Path $HarnessRoot "outputs\nh3_final_20260905T134204Z"
if (-not (Test-Path $HarnessCore)) { throw "Missing $HarnessCore" }
if (-not (Test-Path $CanonicalRun)) { throw "Missing $CanonicalRun" }

Write-Host "Repo:    $RepoRoot"
Write-Host "Harness: $HarnessRoot"
Write-Host "Running exact strict-scaling x lifecycle audit (no DFT; cached response required)..."

& $PythonExe $RunScript $HarnessRoot
if ($LASTEXITCODE -ne 0) { throw "Exact audit failed." }

& $PythonExe $ValidateScript
if ($LASTEXITCODE -ne 0) { throw "Result validation failed." }

Write-Host ""
Write-Host "PASS. Generated:"
Write-Host "  scaling_lifecycle_exact_boundary.csv"
Write-Host "  scaling_lifecycle_exact_keypoints.csv"
Write-Host "  scaling_lifecycle_exact_summary.json"
Write-Host ""
Write-Host "Next: review the summary, then commit these three outputs. The GitHub result gate will validate them again."
