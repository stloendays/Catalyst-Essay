param(
    [ValidateSet("1.1", "1.2")]
    [string]$Model = "1.1",
    [string]$HarnessRoot = "",
    [string]$PythonExe = "python"
)

# Strict-scaling x lifecycle closure for NH3-FINAL-1.1 (default) or NH3-FINAL-1.2 (-Model 1.2).
#   1. run_statewise_strict_scaling_lifecycle.py   promoted files (1.1: this folder; 1.2: nh3_1_2/)
#   2. validate_strict_scaling_lifecycle_result.py result gate for the same model
#   3. run_exact_scaling_lifecycle_surface.py      brute-force cross-check on the cached response surface
#                                                  (1.1: written to %TEMP%; 1.2: nh3_1_2/surface_crosscheck/)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$AuditDir = $PSScriptRoot
$StatewiseScript = Join-Path $AuditDir "run_statewise_strict_scaling_lifecycle.py"
$SurfaceScript = Join-Path $AuditDir "run_exact_scaling_lifecycle_surface.py"
$ValidateScript = Join-Path $AuditDir "validate_strict_scaling_lifecycle_result.py"

if ($Model -eq "1.1") {
    $RunName = "nh3_final_20260905T134204Z"
    if (-not $HarnessRoot) {
        $HarnessRoot = if ($env:NH3_HARNESS) { $env:NH3_HARNESS } else { "D:\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1" }
    }
    if (-not (Test-Path $HarnessRoot)) {
        $Alt = Join-Path $HOME "mnt\论文-AI4S\Catalyst_Economic_Leverage_Automation_Harness_v0.1"
        if (Test-Path $Alt) { $HarnessRoot = $Alt } else { throw "Frozen harness not found. Checked: $HarnessRoot and $Alt" }
    }
    $OutDir = $AuditDir
    $CrossCheckDir = Join-Path $env:TEMP "nh3_1_1_surface_crosscheck"
} else {
    $RunName = "nh3_final_1_2_20261013"
    if (-not $HarnessRoot) {
        $HarnessRoot = if ($env:NH3_HARNESS_1_2) { $env:NH3_HARNESS_1_2 } else { Join-Path $RepoRoot "provenance\nh3_final_1_2\source_harness" }
    }
    $OutDir = Join-Path $AuditDir "nh3_1_2"
    $CrossCheckDir = Join-Path $OutDir "surface_crosscheck"
}

$HarnessCore = Join-Path $HarnessRoot "harness_core.py"
$CanonicalRun = Join-Path $HarnessRoot "outputs\$RunName"
if (-not (Test-Path $HarnessCore)) { throw "Missing $HarnessCore" }
if (-not (Test-Path $CanonicalRun)) { throw "Missing $CanonicalRun" }

$env:NH3_MODEL = $Model
Write-Host "Model:   NH3-FINAL-$Model"
Write-Host "Repo:    $RepoRoot"
Write-Host "Harness: $HarnessRoot"
Write-Host "Running exact strict-scaling x lifecycle audit (no DFT)..."

& $PythonExe $StatewiseScript $HarnessRoot
if ($LASTEXITCODE -ne 0) { throw "Statewise closure failed." }

& $PythonExe $ValidateScript
if ($LASTEXITCODE -ne 0) { throw "Result validation failed." }

& $PythonExe $SurfaceScript $HarnessRoot --out $CrossCheckDir
if ($LASTEXITCODE -ne 0) { throw "Brute-force cross-check failed (cached response surface required)." }

Write-Host ""
Write-Host "PASS. Promoted files in ${OutDir}:"
Write-Host "  scaling_lifecycle_exact_global_boundary.csv"
Write-Host "  scaling_lifecycle_exact_keypoints.csv"
Write-Host "  scaling_lifecycle_exact_summary.json"
Write-Host "Brute-force cross-check in ${CrossCheckDir}."
Write-Host ""
Write-Host "Next: review the summary, then commit these three outputs. The GitHub result gate will validate them again."
