# Cyber Defense Harness Execution Script (PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Cyber Defense: Zero-Trust Runtime Verification Suite     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Python Harness
Write-Host "`n[1/3] Executing Python 3 Reference Harness..." -ForegroundColor Yellow
if (Get-Command python -ErrorAction SilentlyContinue) {
    Push-Location "$PSScriptRoot/python-harness"
    try {
        python run_cyber_defense_tests.py
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [SKIP] Python not found in PATH." -ForegroundColor DarkGray
}

# 2. .NET 6.0 C# Harness
Write-Host "`n[2/3] Executing C# .NET 6.0 Enterprise Harness..." -ForegroundColor Yellow
if (Get-Command dotnet -ErrorAction SilentlyContinue) {
    Push-Location "$PSScriptRoot/dotnet-harness"
    try {
        dotnet run --no-restore -v q
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [SKIP] dotnet CLI not found in PATH." -ForegroundColor DarkGray
}

# 3. Rust Harness
Write-Host "`n[3/3] Executing Rust 2021 Performance Harness..." -ForegroundColor Yellow
if (Get-Command cargo -ErrorAction SilentlyContinue) {
    Push-Location "$PSScriptRoot/rust-harness"
    try {
        cargo run --quiet
    } finally {
        Pop-Location
    }
} else {
    Write-Host "  [SKIP] cargo/rustc not found in PATH (Rust code ready in rust-harness/)." -ForegroundColor DarkGray
}

Write-Host "`n[+] Cyber Defense verification run completed successfully.`n" -ForegroundColor Green
