$ErrorActionPreference = "Stop"
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   AI Alignment Formal Ground Truth Suite" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

Write-Host "`n[1/2] Running Evaluator-Optimizer Process Supervision..." -ForegroundColor Yellow
python evaluator_optimizer.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[2/2] Running Formal Kernel Verification Runner..." -ForegroundColor Yellow
python verify_kernel.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "`n[PASS] All AI Alignment verification tests passed successfully!`n" -ForegroundColor Green
