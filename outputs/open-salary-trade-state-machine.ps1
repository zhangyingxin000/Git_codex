param(
    [string]$Ticket = "",
    [string]$ApplicantTicket = "",
    [string]$ProxyTicket = "",
    [string]$ApplicantUid = "",
    [string]$ProxyUid = "",
    [string]$CountryCode = "",
    [string]$Currency = "",
    [string]$SalaryAmount = "",
    [string]$RedisHost = "47.237.139.110",
    [int]$RedisPort = 6450,
    [int]$RedisDb = 0,
    [string]$RedisPassword = "",
    [bool]$RequireRedis = $false,
    [switch]$NoOpen,
    [string]$LoginBaseUrl = "https://test2westarlive.gzxchate.com"
)

$ErrorActionPreference = "Stop"

function Test-JwtLikeTicket {
    param([string]$Name, [string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        throw "$Name is required. Provide account login data, paste a real ticket, or explicitly enable Redis lookup."
    }
    $dotCount = ([regex]::Matches($Value, '\.')).Count
    if ($dotCount -ne 2 -or $Value.Length -lt 80) {
        throw "$Name is not a valid-looking ticket. It should look like xxx.yyy.zzz."
    }
}

function Get-JwtUid {
    param([string]$Token)
    try {
        $payload = $Token.Split('.')[1].Replace('-', '+').Replace('_', '/')
        switch ($payload.Length % 4) { 2 { $payload += '==' } 3 { $payload += '=' } }
        $json = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload))
        return (($json | ConvertFrom-Json).uid)
    } catch {
        return ""
    }
}

function Get-FirstCsvRow {
    param([string]$Path)
    if (Test-Path -LiteralPath $Path) {
        return Import-Csv -LiteralPath $Path | Select-Object -First 1
    }
    return $null
}

function Read-KeyValueFile {
    param([string]$Path)
    $values = @{}
    if (Test-Path -LiteralPath $Path) {
        Get-Content -LiteralPath $Path | ForEach-Object {
            $line = [string]$_
            if ([string]::IsNullOrWhiteSpace($line) -or $line.TrimStart().StartsWith("#") -or !$line.Contains("=")) { return }
            $parts = $line.Split("=", 2)
            $values[$parts[0].Trim()] = $parts[1].Trim().Trim('"').Trim("'")
        }
    }
    return $values
}

function Get-AccountRow {
    param(
        [object[]]$Rows,
        [string]$Role,
        [string]$Country,
        [string]$TradeCurrency,
        [string]$TargetUid = ""
    )
    $enabled = @($Rows | Where-Object { $_.role -eq $Role -and ($_.enabled -ne "false") })
    if (![string]::IsNullOrWhiteSpace($TargetUid)) {
        $uidMatched = @($enabled | Where-Object { $_.uid -eq $TargetUid })
        if ($uidMatched.Count -gt 0) { return $uidMatched[0] }
        return $null
    }
    $matched = @($enabled | Where-Object {
        ([string]::IsNullOrWhiteSpace($_.countryCode) -or $_.countryCode -eq $Country) -and
        ([string]::IsNullOrWhiteSpace($_.currency) -or $_.currency -eq $TradeCurrency -or $_.supportCurrencies -like "*$TradeCurrency*")
    })
    if ($matched.Count -gt 0) { return $matched[0] }
    if ($enabled.Count -gt 0) { return $enabled[0] }
    return $null
}

function Read-RedisResponse {
    param([System.IO.Stream]$Stream)

    function Read-ByteRequired {
        $value = $Stream.ReadByte()
        if ($value -lt 0) { throw "Redis closed the connection while reading response." }
        return [byte]$value
    }

    function Read-RedisLine {
        $bytes = New-Object System.Collections.Generic.List[byte]
        while ($true) {
            $b = Read-ByteRequired
            if ($b -eq 13) {
                $next = Read-ByteRequired
                if ($next -ne 10) { throw "Invalid Redis response line ending." }
                break
            }
            $bytes.Add($b)
        }
        return [Text.Encoding]::UTF8.GetString($bytes.ToArray())
    }

    $prefix = [char](Read-ByteRequired)
    $line = Read-RedisLine
    if ($prefix -eq '-') { throw "Redis error: $line" }
    if ($prefix -eq '+') { return $line }
    if ($prefix -eq ':') { return $line }
    if ($prefix -eq '$') {
        $length = [int]$line
        if ($length -lt 0) { return "" }
        $buffer = New-Object byte[] $length
        $offset = 0
        while ($offset -lt $length) {
            $read = $Stream.Read($buffer, $offset, $length - $offset)
            if ($read -le 0) { throw "Redis closed the connection while reading bulk data." }
            $offset += $read
        }
        $cr = Read-ByteRequired
        $lf = Read-ByteRequired
        if ($cr -ne 13 -or $lf -ne 10) { throw "Invalid Redis bulk response ending." }
        return [Text.Encoding]::UTF8.GetString($buffer)
    }
    throw "Unsupported Redis response prefix: $prefix"
}

function Send-RedisCommand {
    param(
        [System.IO.Stream]$Stream,
        [string[]]$Parts
    )
    $builder = New-Object System.Text.StringBuilder
    [void]$builder.Append("*$($Parts.Count)`r`n")
    foreach ($part in $Parts) {
        $bytes = [Text.Encoding]::UTF8.GetBytes($part)
        [void]$builder.Append("`$$($bytes.Length)`r`n")
        [void]$builder.Append($part)
        [void]$builder.Append("`r`n")
    }
    $payload = [Text.Encoding]::UTF8.GetBytes($builder.ToString())
    $Stream.Write($payload, 0, $payload.Length)
    $Stream.Flush()
    return Read-RedisResponse -Stream $Stream
}

function Get-RedisAccessToken {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$Db,
        [string]$Password,
        [string]$Uid
    )
    if ([string]::IsNullOrWhiteSpace($Uid)) { return "" }
    $client = New-Object System.Net.Sockets.TcpClient
    $client.ReceiveTimeout = 5000
    $client.SendTimeout = 5000
    try {
        $client.Connect($HostName, $Port)
        $stream = $client.GetStream()
        if (![string]::IsNullOrWhiteSpace($Password)) {
            [void](Send-RedisCommand -Stream $stream -Parts @("AUTH", $Password))
        }
        if ($Db -ne 0) {
            [void](Send-RedisCommand -Stream $stream -Parts @("SELECT", [string]$Db))
        }
        return (Send-RedisCommand -Stream $stream -Parts @("HGET", "user_login_info:$Uid", "access_token")).Trim()
    } catch {
        throw "Redis token lookup failed for uid=${Uid}: $($_.Exception.Message)"
    } finally {
        $client.Close()
    }
}

function Join-FormBody {
    param([hashtable]$Values)
    $parts = New-Object System.Collections.Generic.List[string]
    foreach ($key in $Values.Keys) {
        $value = [string]$Values[$key]
        $encodedValue = if ($key -eq "password") { $value } else { [Uri]::EscapeDataString($value) }
        $parts.Add(([Uri]::EscapeDataString([string]$key) + "=" + $encodedValue))
    }
    return [string]::Join("&", $parts)
}

function Invoke-MobileLogin {
    param(
        [string]$BaseUrl,
        [object]$Account,
        [hashtable]$Common
    )
    if (!$Account -or [string]::IsNullOrWhiteSpace($Account.shortId) -or [string]::IsNullOrWhiteSpace($Account.password_encrypted)) {
        return $null
    }
    $bodyValues = @{
        deviceType = $Common.deviceType
        systemLanguage = $Common.systemLanguage
        shortId = [string]$Account.shortId
        appVersion = $Common.appVersion
        os = $Common.os
        netType = $Common.netType
        channel = $Common.channel
        appsflyerId = $Common.appsflyerId
        language = $Common.language
        appCode = $Common.appCode
        deviceId = $Common.deviceId
        version = $Common.version
        password = [string]$Account.password_encrypted
        osVersion = $Common.osVersion
        isVpnConnected = $Common.isVpnConnected
        appid = $Common.appid
        model = $Common.model
        packageName = $Common.packageName
        ispType = $Common.ispType
        organic = $Common.organic
    }
    $url = $BaseUrl.TrimEnd("/") + "/userserv/id/login"
    $body = Join-FormBody -Values $bodyValues
    $response = Invoke-RestMethod -Method Post -Uri $url -ContentType "application/x-www-form-urlencoded" -Body $body -TimeoutSec 20
    if ($response.code -ne 200 -or !$response.data.access_token -or !$response.data.uid) {
        throw "Login failed for role=$($Account.role), shortId=$($Account.shortId), code=$($response.code), message=$($response.message)"
    }
    return @{ ticket = [string]$response.data.access_token; uid = [string]$response.data.uid }
}

$ProjectRoot = "C:\Users\DELL\Documents\Codex\2026-08-19\new-chat\outputs\AutoTest-AI"
$Jmx = Join-Path $ProjectRoot "outputs\salary-trade-state-machine.jmx"
$ResultDir = "D:\apache-jmeter-5.6.3\jmx\20260826"
$JMeter = "D:\apache-jmeter-5.6.3\bin\jmeter.bat"
$JMeterHome = "D:\apache-jmeter-5.6.3\bin"
$RuntimeProperties = Join-Path $ProjectRoot "work\salary-trade-runtime.properties"
$ApplicantCsv = Join-Path $ProjectRoot "data\salary-trade-applicants.csv"
$AccountCsv = Join-Path $ProjectRoot "data\salary-trade-accounts.csv"
$DatabaseEnv = Join-Path $ProjectRoot "database.env"

if (!(Test-Path -LiteralPath $Jmx)) { throw "Salary trade JMX not found: $Jmx" }
if (!(Test-Path -LiteralPath $JMeter)) { throw "JMeter launcher not found: $JMeter" }
if (!(Test-Path -LiteralPath (Split-Path $RuntimeProperties))) {
    New-Item -ItemType Directory -Path (Split-Path $RuntimeProperties) | Out-Null
}

$ExistingRuntime = Read-KeyValueFile -Path $RuntimeProperties
$DatabaseConfig = Read-KeyValueFile -Path $DatabaseEnv
if ([string]::IsNullOrWhiteSpace($ApplicantTicket) -and $ExistingRuntime.ContainsKey("applicant_ticket")) { $ApplicantTicket = [string]$ExistingRuntime["applicant_ticket"] }
if ([string]::IsNullOrWhiteSpace($ApplicantUid) -and $ExistingRuntime.ContainsKey("applicant_uid")) { $ApplicantUid = [string]$ExistingRuntime["applicant_uid"] }
if ([string]::IsNullOrWhiteSpace($CountryCode) -and $ExistingRuntime.ContainsKey("countryCode")) { $CountryCode = [string]$ExistingRuntime["countryCode"] }
if ([string]::IsNullOrWhiteSpace($Currency) -and $ExistingRuntime.ContainsKey("currency")) { $Currency = [string]$ExistingRuntime["currency"] }

$ApplicantRow = Get-FirstCsvRow -Path $ApplicantCsv
if ([string]::IsNullOrWhiteSpace($ApplicantTicket) -and ![string]::IsNullOrWhiteSpace($Ticket)) {
    $ApplicantTicket = $Ticket
}
if ($ApplicantRow) {
    if ([string]::IsNullOrWhiteSpace($ApplicantUid)) { $ApplicantUid = [string]$ApplicantRow.applicant_uid }
    if ([string]::IsNullOrWhiteSpace($ApplicantTicket)) { $ApplicantTicket = [string]$ApplicantRow.applicant_ticket }
    if ([string]::IsNullOrWhiteSpace($CountryCode)) { $CountryCode = [string]$ApplicantRow.countryCode }
    if ([string]::IsNullOrWhiteSpace($Currency)) { $Currency = [string]$ApplicantRow.currency }
    if ([string]::IsNullOrWhiteSpace($SalaryAmount)) { $SalaryAmount = [string]$ApplicantRow.salaryAmount }
}
if ([string]::IsNullOrWhiteSpace($CountryCode)) { $CountryCode = "MA" }
if ([string]::IsNullOrWhiteSpace($Currency)) { $Currency = "USD" }
if ([string]::IsNullOrWhiteSpace($SalaryAmount)) { $SalaryAmount = "100" }

$Common = @{
    deviceType = "0"
    systemLanguage = "zh"
    appVersion = "100.1.5.6"
    os = "android"
    netType = "2"
    channel = "google"
    appsflyerId = "1787889409378-5852177650651460260"
    language = "en"
    appCode = "100156"
    deviceId = "8fcce1f1-5153-3207-9786-0240140a524a"
    version = "100.1.5.6"
    osVersion = "16"
    isVpnConnected = "0"
    appid = "soulfree"
    model = "SM-A546B"
    packageName = "com.soulfree.happiness"
    ispType = "4"
    organic = "Organic"
}

$AccountRows = @()
if (Test-Path -LiteralPath $AccountCsv) { $AccountRows = @(Import-Csv -LiteralPath $AccountCsv) }
$ApplicantAccount = Get-AccountRow -Rows $AccountRows -Role "applicant" -Country $CountryCode -TradeCurrency $Currency -TargetUid $ApplicantUid
$ProxyAccount = Get-AccountRow -Rows $AccountRows -Role "proxy" -Country $CountryCode -TradeCurrency $Currency -TargetUid $ProxyUid

if ($RequireRedis) {
    $ApplicantRedisTicket = ""
    $ProxyRedisTicket = ""
    if (![string]::IsNullOrWhiteSpace($ApplicantUid)) {
        $ApplicantRedisTicket = Get-RedisAccessToken -HostName $RedisHost -Port $RedisPort -Db $RedisDb -Password $RedisPassword -Uid $ApplicantUid
    }
    if (![string]::IsNullOrWhiteSpace($ProxyUid)) {
        $ProxyRedisTicket = Get-RedisAccessToken -HostName $RedisHost -Port $RedisPort -Db $RedisDb -Password $RedisPassword -Uid $ProxyUid
    }
    if ([string]::IsNullOrWhiteSpace($ApplicantRedisTicket)) {
        throw "Redis did not return applicant access_token for user_login_info:${ApplicantUid}."
    }
    if (![string]::IsNullOrWhiteSpace($ProxyUid) -and [string]::IsNullOrWhiteSpace($ProxyRedisTicket)) {
        throw "Redis did not return proxy access_token for user_login_info:${ProxyUid}."
    }
    if (![string]::IsNullOrWhiteSpace($ApplicantRedisTicket)) {
        $ApplicantTicket = $ApplicantRedisTicket
    }
    if (![string]::IsNullOrWhiteSpace($ProxyRedisTicket)) {
        $ProxyTicket = $ProxyRedisTicket
    }
}

if ([string]::IsNullOrWhiteSpace($ApplicantTicket) -and $ApplicantAccount -and ![string]::IsNullOrWhiteSpace([string]$ApplicantAccount.password)) {
    $login = Invoke-MobileLogin -BaseUrl $LoginBaseUrl -Account $ApplicantAccount -Common $Common
    if ($login) { $ApplicantTicket = $login.ticket; $ApplicantUid = $login.uid }
}
if ([string]::IsNullOrWhiteSpace($ProxyTicket) -and $ProxyAccount -and ![string]::IsNullOrWhiteSpace([string]$ProxyAccount.password)) {
    $login = Invoke-MobileLogin -BaseUrl $LoginBaseUrl -Account $ProxyAccount -Common $Common
    if ($login) { $ProxyTicket = $login.ticket; $ProxyUid = $login.uid }
}

if (![string]::IsNullOrWhiteSpace($ApplicantTicket)) { Test-JwtLikeTicket -Name "ApplicantTicket" -Value $ApplicantTicket }
if (![string]::IsNullOrWhiteSpace($ProxyTicket)) {
    Test-JwtLikeTicket -Name "ProxyTicket" -Value $ProxyTicket
}

$ApplicantTicketUid = Get-JwtUid -Token $ApplicantTicket
$ProxyTicketUid = Get-JwtUid -Token $ProxyTicket
if ([string]::IsNullOrWhiteSpace($ApplicantUid)) { $ApplicantUid = [string]$ApplicantTicketUid }
if ([string]::IsNullOrWhiteSpace($ProxyUid) -and $ProxyTicketUid) { $ProxyUid = [string]$ProxyTicketUid }
if ($ApplicantTicketUid -and $ApplicantUid -and ([string]$ApplicantTicketUid -ne [string]$ApplicantUid)) {
    throw "Applicant uid does not match applicant ticket uid. applicant_uid=$ApplicantUid, ticket_uid=$ApplicantTicketUid"
}
if ($ProxyTicketUid -and $ProxyUid -and ([string]$ProxyTicketUid -ne [string]$ProxyUid)) {
    throw "Proxy uid does not match proxy ticket uid. proxy_uid=$ProxyUid, ticket_uid=$ProxyTicketUid"
}

$PropertyLines = @(
    "sample_variables=flow_a_order_no,flow_b_order_no,flow_c_order_no,flow_d_order_no,flow_e_order_no,flow_f_order_no,flow_g_order_no,flow_h_order_no,salary_order_no,applicant_uid,proxy_uid,agent_uid,countryCode,currency",
    "applicant_uid=$ApplicantUid",
    "proxy_uid=",
    "agent_uid=",
    "countryCode=$CountryCode",
    "currency=$Currency",
    "salaryAmount=$SalaryAmount",
    "deviceType=$($Common.deviceType)",
    "systemLanguage=$($Common.systemLanguage)",
    "appVersion=$($Common.appVersion)",
    "os=$($Common.os)",
    "netType=$($Common.netType)",
    "channel=$($Common.channel)",
    "appsflyerId=$($Common.appsflyerId)",
    "language=$($Common.language)",
    "appCode=$($Common.appCode)",
    "deviceId=$($Common.deviceId)",
    "version=$($Common.version)",
    "osVersion=$($Common.osVersion)",
    "isVpnConnected=$($Common.isVpnConnected)",
    "appid=$($Common.appid)",
    "model=$($Common.model)",
    "packageName=$($Common.packageName)",
    "ispType=$($Common.ispType)",
    "organic=$($Common.organic)",
    "applicant_ticket=$ApplicantTicket",
    "proxy_ticket=",
    "applicant_ticket_uid=$ApplicantTicketUid",
    "proxy_ticket_uid=",
    "redis_host=$RedisHost",
    "redis_port=$RedisPort",
    "redis_db=$RedisDb",
    "redis_password=$RedisPassword",
    "redis_login_key_prefix=user_login_info:",
    "mysql_jdbc_url=jdbc:mysql://$($DatabaseConfig["AUTOTEST_DB_HOST"]):$($DatabaseConfig["AUTOTEST_DB_PORT"])/$($DatabaseConfig["AUTOTEST_DB_NAME"])?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai",
    "mysql_jdbc_user=$($DatabaseConfig["AUTOTEST_DB_USER"])",
    "mysql_jdbc_password=$($DatabaseConfig["AUTOTEST_DB_PASSWORD"])"
)

$PropertyLines | Set-Content -LiteralPath $RuntimeProperties -Encoding ASCII

$LatestJtl = Get-ChildItem -LiteralPath $ResultDir -Filter "*.jtl" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

Write-Host "Opening salary trade state-machine JMeter plan."
Write-Host "JMX: $Jmx"
if ($LatestJtl) { Write-Host "Latest known JTL: $($LatestJtl.FullName)" }
Write-Host "Runtime properties: $RuntimeProperties"
Write-Host "Applicant uid used: $ApplicantUid"
Write-Host "Proxy uid source: JMeter JDBC query anchor_salary_trade_agent_whitelist"
Write-Host "Country/currency used: $CountryCode/$Currency"
if ([string]::IsNullOrWhiteSpace($ProxyTicket)) {
    Write-Host "Ticket state: applicant=ready, proxy=resolved inside JMeter after JDBC agent lookup"
} else {
    Write-Host "Ticket state: applicant=ready, proxy=ready"
}

if ($NoOpen) {
    Write-Host "NoOpen enabled: runtime parameters prepared; JMeter was not opened."
} else {
    Start-Process -FilePath $JMeter -ArgumentList @(
        "-q", $RuntimeProperties,
        "-Jmysql_jdbc_url=jdbc:mysql://$($DatabaseConfig["AUTOTEST_DB_HOST"]):$($DatabaseConfig["AUTOTEST_DB_PORT"])/$($DatabaseConfig["AUTOTEST_DB_NAME"])?useUnicode=true&characterEncoding=utf8&useSSL=false&serverTimezone=Asia/Shanghai",
        "-Jmysql_jdbc_user=$($DatabaseConfig["AUTOTEST_DB_USER"])",
        "-Jmysql_jdbc_password=$($DatabaseConfig["AUTOTEST_DB_PASSWORD"])",
        "-Jredis_host=$RedisHost",
        "-Jredis_port=$RedisPort",
        "-Jredis_db=$RedisDb",
        "-Jredis_password=$RedisPassword",
        "-Jredis_login_key_prefix=user_login_info:",
        "-Jsample_variables=flow_a_order_no,flow_b_order_no,flow_c_order_no,flow_d_order_no,flow_e_order_no,flow_f_order_no,flow_g_order_no,flow_h_order_no,salary_order_no,applicant_uid,proxy_uid,agent_uid,countryCode,currency",
        "-Jsalary_result_jtl=$ResultDir\工资代理结算-result.jtl",
        "-t", $Jmx
    ) -WorkingDirectory $JMeterHome
}





