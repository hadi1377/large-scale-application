# PowerShell helper script to run k6 load tests

param(
    [string]$Scenario = "smoke",
    [string]$BaseUrl = "http://localhost:8050"
)

Write-Host "Running k6 load test: $Scenario" -ForegroundColor Green
Write-Host "Base URL: $BaseUrl" -ForegroundColor Yellow
Write-Host ""

# Check if k6 is installed
try {
    $k6Version = k6 version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "k6 not found"
    }
} catch {
    Write-Host "Error: k6 is not installed" -ForegroundColor Red
    Write-Host "Please install k6 from https://k6.io/docs/getting-started/installation/" -ForegroundColor Yellow
    exit 1
}

# Check if scenario file exists
$scenarioFile = "scenarios\$Scenario.js"
if (-not (Test-Path $scenarioFile)) {
    Write-Host "Error: Scenario file not found: $scenarioFile" -ForegroundColor Red
    Write-Host "Available scenarios: smoke, load, stress, spike, e2e" -ForegroundColor Yellow
    exit 1
}

# Set environment variable and run the test
$env:BASE_URL = $BaseUrl
k6 run --env BASE_URL="$BaseUrl" $scenarioFile

Write-Host "Test completed!" -ForegroundColor Green




