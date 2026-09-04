[CmdletBinding()]
param(
  [ValidateSet("start", "check", "setup", "demo")]
  [string]$Action = "start",
  [string]$BindHost = "127.0.0.1",
  [ValidateRange(1, 65535)]
  [int]$Port = 8765
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$setupScript = Join-Path $PSScriptRoot "setup-env.ps1"
$verifyScript = Join-Path $PSScriptRoot "verify-migration.ps1"

if ($Action -eq "setup") {
  if (-not (Test-Path -LiteralPath $setupScript -PathType Leaf)) {
    throw "Required platform script was not found: $setupScript"
  }
  & $setupScript
  exit $LASTEXITCODE
}

if ($Action -eq "check") {
  if (-not (Test-Path -LiteralPath $verifyScript -PathType Leaf)) {
    throw "Required platform script was not found: $verifyScript"
  }
  & $verifyScript -RunTests
  exit $LASTEXITCODE
}

if ($Action -eq "demo") {
  $demoEnvironmentReady = Test-Path -LiteralPath $venvPython -PathType Leaf
  if ($demoEnvironmentReady) {
    & $venvPython -c "import pytest" 2>$null
    $demoEnvironmentReady = $LASTEXITCODE -eq 0
  }
  if (-not $demoEnvironmentReady) {
    Write-Host "Preparing the isolated project environment for the first demo run..." -ForegroundColor Cyan
    & $setupScript -SkipPipUpgrade
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  }
  $env:AUTOTEST_DEMO_MODE = "true"
  $env:AUTOTEST_ALLOW_MUTATIONS = "false"
  $env:AUTOTEST_ALLOW_HIGH_RISK = "false"
  $env:AUTOTEST_ALLOWED_HOSTS = "127.0.0.1,localhost"
  Write-Host "DEMO MODE: synthetic data only; external writes are disabled." -ForegroundColor Yellow
  Write-Host "Allowed hosts: $env:AUTOTEST_ALLOWED_HOSTS" -ForegroundColor DarkYellow
  Push-Location $PSScriptRoot
  try {
    & $venvPython -m quality_hub_backend.demo.salary_trade
    $demoExitCode = $LASTEXITCODE
    if ($demoExitCode -eq 0) {
      $demoPytestTemp = Join-Path $PSScriptRoot (".pytest-run-demo-" + [guid]::NewGuid().ToString("N"))
      & $venvPython -m pytest -q --basetemp $demoPytestTemp tests/test_demo_salary_trade.py tests/test_jmeter_adapter.py tests/test_dependency_consistency.py
      $demoExitCode = $LASTEXITCODE
    }
  } finally {
    Pop-Location
  }
  exit $demoExitCode
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
  Write-Host "Project environment is not ready. Run this first:" -ForegroundColor Red
  Write-Host ".\platform.cmd setup" -ForegroundColor Yellow
  exit 1
}

& $venvPython -c "import fastapi, uvicorn, pydantic, yaml, sqlalchemy, httpx, redis, pymysql, pytest" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Python dependencies are incomplete. Run this first:" -ForegroundColor Red
  Write-Host ".\platform.cmd setup" -ForegroundColor Yellow
  exit 1
}

if ([string]::IsNullOrWhiteSpace($env:AUTOTEST_ALLOW_MUTATIONS)) {
  $env:AUTOTEST_ALLOW_MUTATIONS = "false"
}
if ([string]::IsNullOrWhiteSpace($env:AUTOTEST_ALLOW_HIGH_RISK)) {
  $env:AUTOTEST_ALLOW_HIGH_RISK = "false"
}
if ([string]::IsNullOrWhiteSpace($env:AUTOTEST_ALLOWED_HOSTS)) {
  $env:AUTOTEST_ALLOWED_HOSTS = "test2westarlive.gzxchate.com"
}

$platformUrl = "http://${BindHost}:$Port"
Write-Host "Starting AutoTest AI platform at $platformUrl" -ForegroundColor Green
Write-Host "Python runtime: $venvPython" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop the platform." -ForegroundColor DarkGray

Push-Location $PSScriptRoot
try {
  do {
    & $venvPython -m uvicorn quality_hub_backend.api.fastapi_app:app --host $BindHost --port $Port
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 75) {
      Write-Host "Reloading AutoTest AI..." -ForegroundColor Cyan
      Start-Sleep -Milliseconds 500
    }
  } while ($exitCode -eq 75)
} finally {
  Pop-Location
}

exit $exitCode
