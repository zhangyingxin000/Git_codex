$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
  Write-Host "Project .venv is missing. Run this first:" -ForegroundColor Red
  Write-Host "powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\setup-env.ps1`"" -ForegroundColor Yellow
  exit 1
}
$python = $venvPython
$env:AUTOTEST_ALLOW_MUTATIONS = "true"
$env:AUTOTEST_ALLOW_HIGH_RISK = "true"
$env:AUTOTEST_ALLOWED_HOSTS = "test2westarlive.gzxchate.com"
Write-Host "Starting AutoTest AI FastAPI backend at http://127.0.0.1:8765" -ForegroundColor Green
Write-Host "Execution mode: all methods enabled; target restricted to test2westarlive.gzxchate.com" -ForegroundColor Yellow
Write-Host "Python runtime: $python" -ForegroundColor Cyan
& $python -c "import fastapi, uvicorn, pydantic, yaml, sqlalchemy, httpx, redis, pymysql, pytest" 2>$null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Python dependencies are missing. Run this first:" -ForegroundColor Red
  Write-Host "powershell -ExecutionPolicy Bypass -File `"$PSScriptRoot\setup-env.ps1`"" -ForegroundColor Yellow
  exit 1
}
do {
  & $python -m uvicorn quality_hub_backend.api.fastapi_app:app --host 127.0.0.1 --port 8765
  $exitCode = $LASTEXITCODE
  if ($exitCode -eq 75) {
    Write-Host "Reloading AutoTest AI..." -ForegroundColor Cyan
    Start-Sleep -Milliseconds 500
  }
} while ($exitCode -eq 75)
