# Master Execution Script for AI Threat Intelligence Suite (Dual Layout Support)
$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  AI Threat Intelligence & Defensive Countermeasures Suite      " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Empirical benchmark execution across .NET 6.0, Python 3, and Rust`n"

$baseDir = $PSScriptRoot
$results = [ordered]@{}

# Helper function to find and run runner script
function Invoke-PillarRunner {
    param(
        [string]$PillarName,
        [string]$SubFolder
    )
    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkCyan
    Write-Host " Running $PillarName..." -ForegroundColor Green
    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkCyan

    $scriptPath = $null
    if (Test-Path "$baseDir/$SubFolder/run.ps1") {
        $scriptPath = "$baseDir/$SubFolder/run.ps1"
    } elseif (Test-Path "$baseDir/$SubFolder/experiment/run.ps1") {
        $scriptPath = "$baseDir/$SubFolder/experiment/run.ps1"
    }

    if ($scriptPath) {
        try {
            & $scriptPath
            $results[$PillarName] = "PASSED"
        } catch {
            $results[$PillarName] = "FAILED: $_"
        }
    } else {
        $results[$PillarName] = "SKIPPED (Runner not found)"
    }
}

Invoke-PillarRunner "Pillar 1: Cyber Defense" "cyber-defense"
Invoke-PillarRunner "Pillar 2: Cognitive Warfare" "influence-countermeasures"
Invoke-PillarRunner "Pillar 3: Supply Chain Defense" "supply-chain-defense"

Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "  Verification Summary" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
$allPassed = $true
foreach ($pillar in $results.Keys) {
    $status = $results[$pillar]
    if ($status -eq "PASSED") {
        Write-Host "  [OK] $pillar : PASSED" -ForegroundColor Green
    } elseif ($status -like "SKIPPED*") {
        Write-Host "  [-]  $pillar : $status" -ForegroundColor Yellow
    } else {
        Write-Host "  [FAIL] $pillar : $status" -ForegroundColor Red
        $allPassed = $false
    }
}

if ($allPassed) {
    Write-Host "`n[+] All Threat Intelligence verification suites PASSED successfully!`n" -ForegroundColor Green
} else {
    Write-Host "`n[-] Some verification suites failed. Review logs above.`n" -ForegroundColor Red
    exit 1
}
