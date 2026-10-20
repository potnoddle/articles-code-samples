# PowerShell Test Runner for Part 1: DNS Sandbox Egress & Bounded Heartbeat
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Pillar 1: RL Sandbox Escape & Transitive DNS Delegation Suite " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

$scriptPath = Join-Path $PSScriptRoot "dns_sandbox_sim.py"
& python $scriptPath

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[PASS] Part 1 Verification Suite completed successfully.`n" -ForegroundColor Green
} else {
    Write-Host "`n[FAIL] Part 1 Verification Suite failed with exit code $LASTEXITCODE.`n" -ForegroundColor Red
    exit 1
}
