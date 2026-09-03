$ErrorActionPreference = "Stop"
$platformScript = Join-Path $PSScriptRoot "platform.ps1"

Write-Host "start.ps1 is kept for compatibility. The preferred command is .\platform.cmd" -ForegroundColor DarkGray
& $platformScript start @args
exit $LASTEXITCODE
