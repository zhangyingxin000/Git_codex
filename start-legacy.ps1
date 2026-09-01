$ErrorActionPreference = "Stop"
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $python = $null
  foreach ($version in @("3.12", "3.13", "3.14")) {
    try {
      $candidate = & py "-$version" -c "import sys; print(sys.executable)" 2>$null
      if ($LASTEXITCODE -eq 0 -and $candidate) {
        $python = $candidate.Trim()
        break
      }
    } catch {}
  }
  if (-not $python) { $python = "python" }
}
Write-Host "Starting AutoTest AI legacy backend at http://127.0.0.1:8765" -ForegroundColor Yellow
$env:AUTOTEST_ALLOW_MUTATIONS = "true"
$env:AUTOTEST_ALLOW_HIGH_RISK = "true"
$env:AUTOTEST_ALLOWED_HOSTS = "test2westarlive.gzxchate.com"
Write-Host "Execution mode: all methods enabled; target restricted to test2westarlive.gzxchate.com" -ForegroundColor Yellow
Write-Host "Python runtime: $python" -ForegroundColor Cyan
do {
  & $python "$PSScriptRoot\app.py"
  $exitCode = $LASTEXITCODE
  if ($exitCode -eq 75) {
    Write-Host "Reloading AutoTest AI..." -ForegroundColor Cyan
    Start-Sleep -Milliseconds 500
  }
} while ($exitCode -eq 75)
