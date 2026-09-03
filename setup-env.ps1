param(
  [string]$PythonExecutable = "",
  [string]$PipIndexUrl = $env:AUTOTEST_PIP_INDEX_URL,
  [switch]$SkipPipUpgrade
)

$ErrorActionPreference = "Stop"
$venvRoot = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venvRoot "Scripts\python.exe"
$requirements = Join-Path $PSScriptRoot "requirements.txt"
$requirementsLock = Join-Path $PSScriptRoot "requirements.lock"

function Resolve-SystemPython {
  if ($PythonExecutable) {
    & $PythonExecutable -c "import sys; print(sys.executable)" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Python executable is not usable: $PythonExecutable" }
    return $PythonExecutable
  }

  foreach ($version in @("3.12", "3.13", "3.14")) {
    try {
      $candidate = & py "-$version" -c "import sys; print(sys.executable)" 2>$null
      if ($LASTEXITCODE -eq 0 -and $candidate) { return $candidate.Trim() }
    } catch {}
  }

  try {
    $candidate = & python -c "import sys; print(sys.executable)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $candidate) { return $candidate.Trim() }
  } catch {}
  throw "Python 3.12-3.14 was not found. Install Python first, then rerun setup-env.ps1."
}

if (-not (Test-Path -LiteralPath $requirements)) {
  throw "requirements.txt was not found: $requirements"
}

$systemPython = Resolve-SystemPython
if (-not (Test-Path -LiteralPath $venvPython)) {
  Write-Host "Creating isolated project environment with: $systemPython" -ForegroundColor Cyan
  & $systemPython -m venv $venvRoot
  if ($LASTEXITCODE -ne 0) { throw "Failed to create project .venv." }
}

$pipBase = @("-m", "pip", "install", "--disable-pip-version-check", "--timeout", "30", "--retries", "2")
if ($PipIndexUrl) {
  $pipBase += @("--index-url", $PipIndexUrl)
  Write-Host "Using configured Python package index." -ForegroundColor DarkCyan
}

if (-not $SkipPipUpgrade) {
  Write-Host "Updating pip inside project .venv..." -ForegroundColor Cyan
  & $venvPython @pipBase --upgrade pip
  if ($LASTEXITCODE -ne 0) { throw "Failed to update pip in project .venv." }
}

Write-Host "Installing project dependencies into .venv..." -ForegroundColor Cyan
$installSource = if (Test-Path -LiteralPath $requirementsLock -PathType Leaf) { $requirementsLock } else { $requirements }
Write-Host "Dependency source: $installSource" -ForegroundColor DarkCyan
& $venvPython @pipBase -r $installSource
if ($LASTEXITCODE -ne 0) { throw "Failed to install requirements.txt." }

& $venvPython -c "import fastapi, uvicorn, pydantic, yaml, sqlalchemy, httpx, redis, pymysql, pytest; print('Dependency verification: OK')"
if ($LASTEXITCODE -ne 0) { throw "Project dependency verification failed." }

$pythonVersion = & $venvPython -c "import platform; print(platform.python_version())"
$requirementsHash = (Get-FileHash -LiteralPath $requirements -Algorithm SHA256).Hash
$requirementsLockHash = if (Test-Path -LiteralPath $requirementsLock -PathType Leaf) { (Get-FileHash -LiteralPath $requirementsLock -Algorithm SHA256).Hash } else { "" }
$indexHost = "default"
if ($PipIndexUrl) {
  try { $indexHost = ([Uri]$PipIndexUrl).Host } catch { $indexHost = "custom" }
}
$metadata = [ordered]@{
  schema_version = "1.0"
  python = $pythonVersion.Trim()
  executable = ".venv/Scripts/python.exe"
  requirements_sha256 = $requirementsHash
  requirements_lock_sha256 = $requirementsLockHash
  package_index = $indexHost
  prepared_at = (Get-Date).ToString("o")
}
$metadata | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $venvRoot "autotest-environment.json") -Encoding UTF8

Write-Host "Environment ready: $venvPython" -ForegroundColor Green
Write-Host "Next: powershell -ExecutionPolicy Bypass -File .\verify-migration.ps1 -RunTests" -ForegroundColor Green
