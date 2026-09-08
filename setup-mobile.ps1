param(
  [string]$PipIndexUrl = $env:AUTOTEST_PIP_INDEX_URL,
  [switch]$SkipCiSetup
)

$ErrorActionPreference = "Stop"
$appium = Join-Path $PSScriptRoot "node_modules\.bin\appium.cmd"
$env:APPIUM_HOME = Join-Path $PSScriptRoot ".appium"
$env:npm_config_cache = Join-Path $PSScriptRoot ".npm-cache"

if (-not $SkipCiSetup -or -not (Test-Path -LiteralPath $appium -PathType Leaf)) {
  & (Join-Path $PSScriptRoot "setup-ci.ps1") -PipIndexUrl $PipIndexUrl
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$installed = & $appium driver list --installed 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) { throw "Unable to inspect installed Appium drivers." }
if ($installed -notmatch "uiautomator2") {
  Write-Host "Installing the project-local UiAutomator2 driver..." -ForegroundColor Cyan
  & $appium driver install uiautomator2
  if ($LASTEXITCODE -ne 0) { throw "Failed to install the UiAutomator2 driver." }
}

Write-Host "Android Appium environment is ready." -ForegroundColor Green
Write-Host "APPIUM_HOME: $env:APPIUM_HOME" -ForegroundColor DarkCyan
