param(
    [string]$Workflow = "examples/jmeter-mcp/health-workflow.json",
    [string]$OutputDir = "reports/jmeter-mcp-poc",
    [switch]$UsePlatformHealth
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BridgeRoot = Join-Path $Root "tools/jmeter-mcp"
$JMeterHome = $env:AUTOTEST_JMETER_HOME
if (-not $JMeterHome) {
    $JMeterHome = $env:JMETER_HOME
}
if (-not $JMeterHome -and $env:AUTOTEST_JMETER) {
    $JMeterHome = Split-Path -Parent (Split-Path -Parent $env:AUTOTEST_JMETER)
}
if (-not $JMeterHome) {
    $ProjectPython = Join-Path $Root ".venv/Scripts/python.exe"
    if (-not (Test-Path -LiteralPath $ProjectPython -PathType Leaf)) {
        $ProjectPython = (Get-Command python -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    }
    if ($ProjectPython) {
        $DetectedJMeter = (& $ProjectPython -c "import app; print(app._jmeter_command() or '')" 2>$null | Select-Object -Last 1)
        if ($DetectedJMeter -and (Test-Path -LiteralPath $DetectedJMeter -PathType Leaf)) {
            $JMeterHome = Split-Path -Parent (Split-Path -Parent $DetectedJMeter)
        }
    }
}
if (-not $JMeterHome) {
    $DetectedJMeter = (Get-Command jmeter.bat,jmeter -ErrorAction SilentlyContinue | Select-Object -First 1).Source
    if ($DetectedJMeter) {
        $JMeterHome = Split-Path -Parent (Split-Path -Parent $DetectedJMeter)
    }
}
if (-not $JMeterHome) {
    throw "JMeter was not found from YAML/environment/PATH. Configure tools.jmeter.home or AUTOTEST_JMETER_HOME."
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw "Node.js is required. Install Node.js 18 or newer first."
}
if (-not (Test-Path (Join-Path $BridgeRoot "node_modules/jmeter-mcp-server/dist/index.js"))) {
    throw "JMeter MCP dependencies are missing. Run: npm install --prefix .\tools\jmeter-mcp"
}

$Arguments = @(
    (Join-Path $BridgeRoot "bridge.mjs"),
    "--workflow", (Join-Path $Root $Workflow),
    "--output-dir", (Join-Path $Root $OutputDir),
    "--jmeter-home", $JMeterHome,
    "--workspace", (Join-Path $Root "work/jmeter-mcp")
)
if (-not $UsePlatformHealth) {
    $Arguments += "--self-test"
}

& node @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "JMeter MCP POC failed with exit code $LASTEXITCODE."
}
