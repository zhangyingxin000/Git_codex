param(
    [string]$Ticket = "",
    [string]$ProxyTicket = ""
)

$ErrorActionPreference = "Stop"

$ProjectRoot = "C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI"
$Jmx = Join-Path $ProjectRoot "outputs\performance-baseline-with-salary-thread.jmx"
$ResultDir = "D:\apache-jmeter-5.6.3\jmx\20260826"
$JMeter = "D:\apache-jmeter-5.6.3\bin\jmeter.bat"
$JMeterHome = "D:\apache-jmeter-5.6.3\bin"
$RuntimeExporter = Join-Path $ProjectRoot "work\export_jmeter_runtime.py"
$RuntimeProperties = Join-Path $ProjectRoot "work\jmeter-runtime.properties"
$Python = "C:\Users\DELL\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if (!(Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

if (!(Test-Path -LiteralPath $Jmx)) {
    throw "Generated JMX not found: $Jmx"
}
if (!(Test-Path -LiteralPath $JMeter)) {
    throw "JMeter launcher not found: $JMeter"
}
if (!(Test-Path -LiteralPath $RuntimeExporter)) {
    throw "Runtime exporter not found: $RuntimeExporter"
}

Push-Location $ProjectRoot
try {
    $RuntimeJson = & $Python $RuntimeExporter "prj_e3515817c4"
} finally {
    Pop-Location
}
$Runtime = $RuntimeJson | ConvertFrom-Json
if (![string]::IsNullOrWhiteSpace($Ticket)) {
    $Runtime.ticket = $Ticket
}

if ([string]::IsNullOrWhiteSpace($Runtime.ticket)) {
    throw "Saved runtime ticket not found. Please complete login once in the workbench first."
}

Write-Host "Opening JMeter GUI with generated salary baseline."
Write-Host "JMX: $Jmx"

$LatestJtl = Get-ChildItem -LiteralPath $ResultDir -Filter "*.jtl" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($null -ne $LatestJtl) {
    Write-Host "Latest known JTL: $($LatestJtl.FullName)"
} else {
    Write-Host "No JTL file found yet in: $ResultDir"
}

$PropertyLines = @()
$Runtime.PSObject.Properties | ForEach-Object {
    if ($null -ne $_.Value -and -not [string]::IsNullOrWhiteSpace([string]$_.Value)) {
        $PropertyLines += "$($_.Name)=$($_.Value)"
    }
}
if (![string]::IsNullOrWhiteSpace($ProxyTicket)) {
    $PropertyLines += "proxy_ticket=$ProxyTicket"
}
$PropertyLines | Set-Content -LiteralPath $RuntimeProperties -Encoding ASCII

$Args = @("-q", $RuntimeProperties, "-t", $Jmx)

Write-Host "Runtime ticket loaded from local credential store."
if (![string]::IsNullOrWhiteSpace($Ticket)) {
    Write-Host "Runtime ticket overridden from command parameter."
}
Write-Host "Runtime uid: $($Runtime.uid)"
Write-Host "Runtime properties prepared for JMeter."
if (![string]::IsNullOrWhiteSpace($ProxyTicket)) {
    Write-Host "代理 ticket 已从命令参数写入。"
} elseif ($null -ne $Runtime.proxy_ticket -and ![string]::IsNullOrWhiteSpace([string]$Runtime.proxy_ticket)) {
    Write-Host "代理 ticket 已从本地凭证写入。"
} else {
    Write-Host "未提供代理 ticket，代理操作线程会给出明确阻塞提示。"
}

Start-Process -FilePath $JMeter -ArgumentList $Args -WorkingDirectory $JMeterHome

Write-Host "JMeter launch command sent."


