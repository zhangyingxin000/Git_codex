$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI"
$Source = Join-Path $ProjectRoot "outputs\performance-baseline-with-salary-thread.jmx"
$TargetDir = "D:\apache-jmeter-5.6.3\jmx\20260826"
$JMeter = "D:\apache-jmeter-5.6.3\bin\jmeter.bat"

if (!(Test-Path -LiteralPath $Source)) {
    throw "Generated JMX not found: $Source"
}
if (!(Test-Path -LiteralPath $TargetDir)) {
    throw "Target directory not found: $TargetDir"
}
if (!(Test-Path -LiteralPath $JMeter)) {
    throw "JMeter launcher not found: $JMeter"
}

$Target = Get-ChildItem -LiteralPath $TargetDir -Filter "*.jmx" |
    Where-Object { $_.Name -notlike "*.backup-*" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -eq $Target) {
    throw "No editable baseline JMX found in: $TargetDir"
}

$Backup = Join-Path $TargetDir ("baseline.backup-before-salary-thread-" + (Get-Date -Format "yyyyMMdd-HHmmss") + ".jmx")

Copy-Item -LiteralPath $Target.FullName -Destination $Backup
Copy-Item -LiteralPath $Source -Destination $Target.FullName -Force

Write-Host "Salary trade thread group has been written."
Write-Host "Target: $($Target.FullName)"
Write-Host "Backup: $Backup"
Write-Host "Opening JMeter with the updated baseline..."

Start-Process -FilePath $JMeter -ArgumentList @("-t", $Target.FullName) -WorkingDirectory "D:\apache-jmeter-5.6.3\bin"

Write-Host "JMeter launch command sent."
