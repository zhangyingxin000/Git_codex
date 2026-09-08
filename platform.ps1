[CmdletBinding()]
param(
  [ValidateSet("start", "check", "setup", "setup-ci", "setup-mobile", "demo", "ci", "ci-tools", "mobile-ci")]
  [string]$Action = "start",
  [string]$BindHost = "127.0.0.1",
  [ValidateRange(1, 65535)]
  [int]$Port = 8765,
  [string]$ConfigPath = ""
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$setupScript = Join-Path $PSScriptRoot "setup-env.ps1"
$setupCiScript = Join-Path $PSScriptRoot "setup-ci.ps1"
$setupMobileScript = Join-Path $PSScriptRoot "setup-mobile.ps1"
$verifyScript = Join-Path $PSScriptRoot "verify-migration.ps1"
$ciScript = Join-Path $PSScriptRoot "scripts\run_ci.py"
$ciToolsScript = Join-Path $PSScriptRoot "scripts\run_external_ci.py"
$mobilePytestRunner = Join-Path $PSScriptRoot "mobile\pytest_runtime.py"
$mobilePytestEvidence = Join-Path $PSScriptRoot "scripts\mobile_pytest_evidence.py"

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

if ($Action -eq "setup-ci") {
  if (-not (Test-Path -LiteralPath $setupCiScript -PathType Leaf)) {
    throw "Required CI setup script was not found: $setupCiScript"
  }
  & $setupCiScript
  exit $LASTEXITCODE
}

if ($Action -eq "setup-mobile") {
  if (-not (Test-Path -LiteralPath $setupMobileScript -PathType Leaf)) {
    throw "Required mobile setup script was not found: $setupMobileScript"
  }
  & $setupMobileScript
  exit $LASTEXITCODE
}

if ($Action -eq "ci") {
  if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "Project environment is not ready. Run this first:" -ForegroundColor Red
    Write-Host ".\platform.cmd setup" -ForegroundColor Yellow
    exit 1
  }
  if (-not (Test-Path -LiteralPath $ciScript -PathType Leaf)) {
    throw "Required CI runner was not found: $ciScript"
  }
  Push-Location $PSScriptRoot
  try {
    & $venvPython $ciScript
    $ciExitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  exit $ciExitCode
}

if ($Action -eq "ci-tools") {
  if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "Project environment is not ready. Run this first:" -ForegroundColor Red
    Write-Host ".\platform.cmd setup" -ForegroundColor Yellow
    exit 1
  }
  if (-not (Test-Path -LiteralPath $ciToolsScript -PathType Leaf)) {
    throw "Required external CLI runner was not found: $ciToolsScript"
  }
  if (-not $ConfigPath) {
    $ConfigPath = $env:AUTOTEST_CI_TOOLS_CONFIG
  }
  if (-not $ConfigPath) {
    Write-Host "Provide a CLI pipeline config path:" -ForegroundColor Red
    Write-Host ".\platform.cmd ci-tools -ConfigPath .\config\ci-tools.example.yaml" -ForegroundColor Yellow
    exit 2
  }
  Push-Location $PSScriptRoot
  try {
    & $venvPython $ciToolsScript --config $ConfigPath
    $ciToolsExitCode = $LASTEXITCODE
  } finally {
    Pop-Location
  }
  exit $ciToolsExitCode
}

if ($Action -eq "mobile-ci") {
  if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
    Write-Host "Project environment is not ready. Run this first:" -ForegroundColor Red
    Write-Host ".\platform.cmd setup-mobile" -ForegroundColor Yellow
    exit 1
  }
  if (-not (Test-Path -LiteralPath $mobilePytestRunner -PathType Leaf)) {
    throw "Required mobile pytest runner was not found: $mobilePytestRunner"
  }
  if (-not (Test-Path -LiteralPath $mobilePytestEvidence -PathType Leaf)) {
    throw "Required mobile pytest evidence helper was not found: $mobilePytestEvidence"
  }
  if (-not $ConfigPath) {
    $ConfigPath = $env:AUTOTEST_MOBILE_CONFIG
  }
  if (-not $ConfigPath) {
    Write-Host "Provide an Android mobile CI config path:" -ForegroundColor Red
    Write-Host ".\platform.cmd mobile-ci -ConfigPath .\config\mobile-ci.example.yaml" -ForegroundColor Yellow
    exit 2
  }
  Push-Location $PSScriptRoot
  try {
    $mobileTaskRoot = Join-Path $PSScriptRoot ("reports\mobile-ci\task-runs\cli-" + [guid]::NewGuid().ToString("N"))
    $mobilePytestWork = Join-Path $mobileTaskRoot "pytest-work"
    $mobileConsole = Join-Path $mobileTaskRoot "pytest-console.log"
    $mobileJunit = Join-Path $mobileTaskRoot "pytest-junit.xml"
    New-Item -ItemType Directory -Path $mobileTaskRoot -Force | Out-Null
    $env:AUTOTEST_MOBILE_CONFIG = $ConfigPath
    $env:AUTOTEST_MOBILE_REPORT_ROOT = Join-Path $PSScriptRoot "reports\mobile-ci"
    if (-not $env:AUTOTEST_MOBILE_SCENARIOS) { $env:AUTOTEST_MOBILE_SCENARIOS = "[]" }
    if (-not $env:AUTOTEST_MOBILE_DEVICES) { $env:AUTOTEST_MOBILE_DEVICES = "[]" }
    & $venvPython -m pytest -q -s --tb=short --basetemp $mobilePytestWork --junitxml $mobileJunit $mobilePytestRunner *>&1 |
      Tee-Object -FilePath $mobileConsole
    $pytestExitCode = $LASTEXITCODE
    $mobileConsoleText = Get-Content -LiteralPath $mobileConsole -Raw
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [IO.File]::WriteAllText($mobileConsole, $mobileConsoleText, $utf8NoBom)
    & $venvPython $mobilePytestEvidence --report-root $env:AUTOTEST_MOBILE_REPORT_ROOT --console $mobileConsole --junit $mobileJunit --exit-code $pytestExitCode
    $evidenceExitCode = $LASTEXITCODE
    $mobileCiExitCode = if ($pytestExitCode -ne 0) { $pytestExitCode } else { $evidenceExitCode }
    $resolvedTaskRoot = [IO.Path]::GetFullPath($mobileTaskRoot + [IO.Path]::DirectorySeparatorChar)
    $resolvedWork = [IO.Path]::GetFullPath($mobilePytestWork)
    if ($resolvedWork.StartsWith($resolvedTaskRoot) -and (Split-Path -Leaf $resolvedWork) -eq "pytest-work") {
      Remove-Item -LiteralPath $resolvedWork -Recurse -Force -ErrorAction SilentlyContinue
    }
  } finally {
    Pop-Location
  }
  exit $mobileCiExitCode
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
      $demoReportRoot = Join-Path $PSScriptRoot "requirements\demo\salary-trade\reports\latest"
      New-Item -ItemType Directory -Path $demoReportRoot -Force | Out-Null
      $demoPytestTemp = Join-Path $demoReportRoot "pytest-work"
      try {
        & $venvPython -m pytest -q --basetemp $demoPytestTemp tests/test_demo_salary_trade.py tests/test_jmeter_mcp_adapter.py tests/test_dependency_consistency.py
        $demoExitCode = $LASTEXITCODE
      } finally {
        $resolvedRoot = [IO.Path]::GetFullPath($demoReportRoot + [IO.Path]::DirectorySeparatorChar)
        $resolvedTemp = [IO.Path]::GetFullPath($demoPytestTemp)
        if ($resolvedTemp.StartsWith($resolvedRoot) -and (Split-Path -Leaf $resolvedTemp) -eq "pytest-work") {
          Remove-Item -LiteralPath $resolvedTemp -Recurse -Force -ErrorAction SilentlyContinue
        }
      }
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
