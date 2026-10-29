# PowerShell Test Runner for Part 3: LoRA Poisoning Verifier & Structural Matrix Analyzer
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Pillar 3: LoRA Poisoning Verifier & Matrix Spectral Analyzer  " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$scriptPath = Join-Path $PSScriptRoot "validator.py"
& python $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[PASS] Part 3 Verification Suite completed successfully.`n" -ForegroundColor Green
} else {
    Write-Host "`n[FAIL] Part 3 Verification Suite failed with exit code $LASTEXITCODE.`n" -ForegroundColor Red
    exit 1
}
