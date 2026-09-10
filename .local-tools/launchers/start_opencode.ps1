[CmdletBinding()]
param(
    [string]$ProjectPath = "C:\Users\delib\Desktop\OmnisveraGame",
    [int]$Port = 4096,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Omnisvera - OpenCode"
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

function Test-LocalPort([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $result = $client.BeginConnect("127.0.0.1", $Port, $null, $null)
        if (-not $result.AsyncWaitHandle.WaitOne(1000, $false)) { return $false }
        $client.EndConnect($result)
        return $true
    }
    catch { return $false }
    finally { $client.Dispose() }
}

$configPath = Join-Path $env:USERPROFILE ".config\opencode"
if (-not (Test-Path -LiteralPath $configPath -PathType Container)) {
    New-Item -ItemType Directory -Path $configPath -Force | Out-Null
}

$url = "http://127.0.0.1:$Port"
if (-not $env:OPENCODE_SERVER_USERNAME) {
    $env:OPENCODE_SERVER_USERNAME = [Environment]::GetEnvironmentVariable('OPENCODE_SERVER_USERNAME', 'User')
}
if (-not $env:OPENCODE_SERVER_USERNAME) { $env:OPENCODE_SERVER_USERNAME = 'sage' }
[Environment]::SetEnvironmentVariable('OPENCODE_SERVER_USERNAME', $env:OPENCODE_SERVER_USERNAME, 'User')
$env:OPENCODE_SERVER_PASSWORD = Get-LauncherSecret 'OPENCODE_SERVER_PASSWORD'
$routerKey = Get-LauncherSecret 'ROUTER9_API_KEY' -Optional
if ($routerKey) { $env:ROUTER9_API_KEY = $routerKey }
& (Join-Path $PSScriptRoot 'configure_opencode.ps1')

if (-not (Test-Path -LiteralPath $ProjectPath -PathType Container)) {
    throw "Projeto não encontrado: $ProjectPath"
}

if (-not (Test-LocalPort 20128)) {
    $routerLauncher = Join-Path $env:USERPROFILE "OmnisveraTools\Start-9Router-Local.ps1"
    if (-not (Test-Path -LiteralPath $routerLauncher -PathType Leaf)) {
        throw "Iniciador do 9Router não encontrado: $routerLauncher"
    }
    Start-Process powershell.exe -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $routerLauncher
    ) -WindowStyle Hidden | Out-Null
    for ($attempt = 0; $attempt -lt 30 -and -not (Test-LocalPort 20128); $attempt++) {
        Start-Sleep -Seconds 1
    }
}
if (-not (Test-LocalPort 20128)) { throw "9Router não abriu a porta 20128." }

try {
    $models = Invoke-RestMethod -Uri "http://127.0.0.1:20128/v1/models" -TimeoutSec 10
    if (-not $models.data) { throw "lista de modelos vazia" }
}
catch { throw "9Router não respondeu corretamente: $($_.Exception.Message)" }

$openCode = Join-Path $env:APPDATA "npm\node_modules\opencode-ai\bin\opencode.exe"
if (-not (Test-Path -LiteralPath $openCode -PathType Leaf)) {
    throw "OpenCode não encontrado: $openCode"
}

if (-not (Test-LocalPort $Port)) {
    New-Item -ItemType Directory -Path $LauncherState -Force | Out-Null
    Start-Process -FilePath $openCode -ArgumentList @('web', '--hostname', '127.0.0.1', '--port', $Port) -WorkingDirectory $ProjectPath -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LauncherState 'opencode.out.log') -RedirectStandardError (Join-Path $LauncherState 'opencode.err.log') | Out-Null
    Wait-LocalPort $Port 45
}
$credentials = '{0}:{1}' -f $env:OPENCODE_SERVER_USERNAME, $env:OPENCODE_SERVER_PASSWORD
$authorization = 'Basic ' + [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($credentials))
$response = Invoke-WebRequest -UseBasicParsing -Uri "$url/global/health" -Headers @{Authorization=$authorization} -TimeoutSec 15
if ($response.StatusCode -ne 200) { throw 'OpenCode nao respondeu corretamente.' }
$tailnetUrl = Enable-PrivateTailnetService $Port
$remote = Invoke-WebRequest -UseBasicParsing -Uri "$tailnetUrl/global/health" -Headers @{Authorization=$authorization} -TimeoutSec 20
if ($remote.StatusCode -ne 200) { throw 'OpenCode nao respondeu pelo HTTPS do Tailscale.' }
Write-Host "OpenCode pronto no celular: $tailnetUrl" -ForegroundColor Green
Write-Host "Usuario: $env:OPENCODE_SERVER_USERNAME" -ForegroundColor Cyan
Write-Host 'Omnisvera MCP: conexao local automatica, somente leitura.'
Write-Host 'Pode fechar este iniciador; OpenCode continua em segundo plano.'
if (-not $NoBrowser) { Start-Process $tailnetUrl }
