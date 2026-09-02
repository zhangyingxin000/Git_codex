param(
  [switch]$RunTests
)

$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$requiredFiles = @(
  "requirements.txt",
  "pyproject.toml",
  "config\env.example.yaml",
  "config\data-sources.example.yaml"
)

if (-not (Test-Path -LiteralPath $venvPython)) {
  throw "Project .venv is missing. Run setup-env.ps1 before starting the platform."
}

foreach ($relativePath in $requiredFiles) {
  $path = Join-Path $PSScriptRoot $relativePath
  if (-not (Test-Path -LiteralPath $path)) { throw "Migration asset is missing: $relativePath" }
}

Write-Host "Checking isolated Python runtime..." -ForegroundColor Cyan
Push-Location $PSScriptRoot
try {
  & $venvPython -c "import pathlib, sys; expected=(pathlib.Path.cwd()/'.venv').resolve(); actual=pathlib.Path(sys.prefix).resolve(); assert actual == expected, f'Expected {expected}, got {actual}'; print(sys.executable)"
  if ($LASTEXITCODE -ne 0) { throw "Python runtime is not isolated to the project .venv." }

  Write-Host "Checking required Python packages..." -ForegroundColor Cyan
  & $venvPython -c "import fastapi, uvicorn, pydantic, yaml, sqlalchemy, httpx, redis, pymysql, pytest; print('Required packages: OK')"
  if ($LASTEXITCODE -ne 0) { throw "One or more project dependencies are missing." }

  Write-Host "Checking application imports..." -ForegroundColor Cyan
  & $venvPython -m py_compile "app.py" "quality_hub_backend\api\fastapi_app.py"
  if ($LASTEXITCODE -ne 0) { throw "Application import check failed." }

  if ($RunTests) {
    Write-Host "Running platform regression tests..." -ForegroundColor Cyan
    & $venvPython -m pytest -q
    if ($LASTEXITCODE -ne 0) { throw "Platform regression tests failed." }
  }
} finally {
  Pop-Location
}

Write-Host "Migration verification passed." -ForegroundColor Green
