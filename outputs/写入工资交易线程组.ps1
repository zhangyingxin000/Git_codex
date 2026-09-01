$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI"
$Source = Join-Path $ProjectRoot "outputs\性能基线-追加工资交易线程组.jmx"
$Target = "D:\apache-jmeter-5.6.3\jmx\20260826\性能基线.jmx"
$Backup = "D:\apache-jmeter-5.6.3\jmx\20260826\性能基线.backup-before-salary-thread-$(Get-Date -Format 'yyyyMMdd-HHmmss').jmx"

if (!(Test-Path -LiteralPath $Source)) {
    throw "Generated JMX not found: $Source"
}
if (!(Test-Path -LiteralPath $Target)) {
    throw "Target JMX not found: $Target"
}

Copy-Item -LiteralPath $Target -Destination $Backup
Copy-Item -LiteralPath $Source -Destination $Target -Force

Write-Host "Salary trade thread group has been written."
Write-Host "Target: $Target"
Write-Host "Backup: $Backup"

$JMeter = "D:\apache-jmeter-5.6.3\bin\jmeter.bat"
if (!(Test-Path -LiteralPath $JMeter)) {
    throw "JMeter launcher not found: $JMeter"
}

Write-Host "Opening JMeter with the baseline JMX..."
Start-Process -FilePath $JMeter -ArgumentList @("-t", $Target) -WorkingDirectory "D:\apache-jmeter-5.6.3\bin"
Write-Host "JMeter launch command sent. Please check the desktop window."
