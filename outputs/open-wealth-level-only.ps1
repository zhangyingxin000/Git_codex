param(
    [string]$Ticket = "",
    [string]$Uid = "1454694"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI"
$Jmx = Join-Path $ProjectRoot "outputs\wealth-level-only.jmx"
$JMeter = "D:\apache-jmeter-5.6.3\bin\jmeter.bat"
$JMeterHome = "D:\apache-jmeter-5.6.3\bin"
$RuntimeProperties = Join-Path $ProjectRoot "work\wealth-level-runtime.properties"

if (!(Test-Path -LiteralPath $Jmx)) {
    throw "Wealth level JMX not found: $Jmx"
}
if (!(Test-Path -LiteralPath $JMeter)) {
    throw "JMeter launcher not found: $JMeter"
}

$PropertyLines = @(
    "uid=$Uid",
    "deviceType=0",
    "systemLanguage=zh",
    "appVersion=100.1.5.4",
    "os=android",
    "netType=2",
    "channel=google",
    "appsflyerId=1787628595990-5267637366511328587",
    "language=en",
    "appCode=100154",
    "deviceId=8fcce1f1-5153-3207-9786-0240140a524a",
    "version=100.1.5.4",
    "osVersion=16",
    "isVpnConnected=0",
    "appid=soulfree",
    "model=SM-A546B",
    "packageName=com.soulfree.happiness",
    "ispType=4",
    "organic=Organic"
)

if (![string]::IsNullOrWhiteSpace($Ticket)) {
    $PropertyLines += "ticket=$Ticket"
}

$PropertyLines | Set-Content -LiteralPath $RuntimeProperties -Encoding ASCII

Write-Host "Opening wealth level JMeter plan."
Write-Host "JMX: $Jmx"
Write-Host "Runtime properties: $RuntimeProperties"
Write-Host "Ticket provided: $(-not [string]::IsNullOrWhiteSpace($Ticket))"

Start-Process -FilePath $JMeter -ArgumentList @("-q", $RuntimeProperties, "-t", $Jmx) -WorkingDirectory $JMeterHome
