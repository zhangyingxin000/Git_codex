param(
  [string]$PipIndexUrl = $env:AUTOTEST_PIP_INDEX_URL,
  [switch]$SkipRuntimeSetup
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$ciRequirements = Join-Path $PSScriptRoot "requirements-ci.lock"
$npmCache = Join-Path $PSScriptRoot ".npm-cache"
$packageLock = Join-Path $PSScriptRoot "package-lock.json"

if (-not $SkipRuntimeSetup) {
  & (Join-Path $PSScriptRoot "setup-env.ps1") -PipIndexUrl $PipIndexUrl -SkipPipUpgrade
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not (Test-Path -LiteralPath $venvPython -PathType Leaf)) {
  throw "Project Python environment is missing. Run .\platform.cmd setup first."
}
if (-not (Test-Path -LiteralPath $ciRequirements -PathType Leaf)) {
  throw "CI requirements lock was not found: $ciRequirements"
}

$pipArgs = @("-m", "pip", "install", "--disable-pip-version-check", "--timeout", "30", "--retries", "2")
if ($PipIndexUrl) { $pipArgs += @("--index-url", $PipIndexUrl) }
& $venvPython @pipArgs -r $ciRequirements
if ($LASTEXITCODE -ne 0) { throw "Failed to install Python CI tools." }

$env:npm_config_cache = $npmCache
Push-Location $PSScriptRoot
try {
  if (Test-Path -LiteralPath $packageLock -PathType Leaf) {
    & npm ci --no-audit --no-fund
  } else {
    & npm install --no-audit --no-fund
  }
  if ($LASTEXITCODE -ne 0) { throw "Failed to install Node CLI tools." }
} finally {
  Pop-Location
}

& $venvPython -m ruff --version
if ($LASTEXITCODE -ne 0) { throw "Ruff verification failed." }
& (Join-Path $PSScriptRoot ".venv\Scripts\detect-secrets.exe") --version
if ($LASTEXITCODE -ne 0) { throw "detect-secrets verification failed." }
& (Join-Path $PSScriptRoot "node_modules\.bin\allure.cmd") --version
if ($LASTEXITCODE -ne 0) { throw "Allure CLI verification failed." }
& (Join-Path $PSScriptRoot "node_modules\.bin\appium.cmd") --version
if ($LASTEXITCODE -ne 0) { throw "Appium CLI verification failed." }

Write-Host "CI tools are ready." -ForegroundColor Green
