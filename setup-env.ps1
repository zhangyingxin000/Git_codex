$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  $systemPython = $null
  foreach ($version in @("3.12", "3.13", "3.14")) {
    try {
      $candidate = & py "-$version" -c "import sys; print(sys.executable)" 2>$null
      if ($LASTEXITCODE -eq 0 -and $candidate) {
        $systemPython = $candidate.Trim()
        break
      }
    } catch {}
  }
  if (-not $systemPython) {
    $systemPython = "python"
  }
  Write-Host "Creating project virtual environment with: $systemPython" -ForegroundColor Cyan
  & $systemPython -m venv "$PSScriptRoot\.venv"
}

Write-Host "Installing backend dependencies into project .venv..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r "$PSScriptRoot\requirements.txt"

Write-Host "Environment ready: $venvPython" -ForegroundColor Green
