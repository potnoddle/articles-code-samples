# PowerShell Test Runner for Part 2: Autonomous Synthetic DPO & Inversion Pipeline
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Pillar 2: Synthetic DPO Poisoning & $5 LoRA Inversion Suite   " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$scriptPath = Join-Path $PSScriptRoot "synthetic_dpo_pipeline.py"
& python $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[PASS] Part 2 Verification Suite completed successfully.`n" -ForegroundColor Green
} else {
    Write-Host "`n[FAIL] Part 2 Verification Suite failed with exit code $LASTEXITCODE.`n" -ForegroundColor Red
    exit 1
}
