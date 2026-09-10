[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Omnisvera MCP"
. (Join-Path $PSScriptRoot 'runtime_common.ps1')
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$python = Join-Path $root ".omnisvera-tools\Scripts\python.exe"
$server = Join-Path $root ".local-tools\mcp_http_server.py"
$tunnelClient = Join-Path $root ".local-tools\bin\tunnel-client-v0.0.13\windows-amd64\tunnel-client.exe"

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

function Test-TunnelClient {
    try {
        $health = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/healthz" -TimeoutSec 3
        $ready = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8080/readyz" -TimeoutSec 3
        return $health.StatusCode -eq 200 -and $health.Content.Trim() -eq "live" `
            -and $ready.StatusCode -eq 200 -and $ready.Content.Trim() -eq "ready"
    }
    catch { return $false }
}

if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw "Python do MCP nao encontrado: $python" }
if (-not (Test-Path -LiteralPath $tunnelClient -PathType Leaf)) { throw "tunnel-client nao encontrado: $tunnelClient" }

if (-not (Test-LocalPort 8765)) {
    $outLog = Join-Path $env:TEMP "omnisvera-mcp-http.stdout.log"
    $errLog = Join-Path $env:TEMP "omnisvera-mcp-http.stderr.log"
    Start-Process -FilePath $python -ArgumentList @($server) -WorkingDirectory $root `
        -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $errLog | Out-Null
    for ($attempt = 0; $attempt -lt 30 -and -not (Test-LocalPort 8765); $attempt++) {
        Start-Sleep -Milliseconds 500
    }
}
if (-not (Test-LocalPort 8765)) { throw "MCP HTTP não abriu a porta 8765." }

$storedKey = Get-LauncherSecret 'CONTROL_PLANE_API_KEY' -Optional
if ($storedKey) { $env:CONTROL_PLANE_API_KEY = $storedKey }
if (-not (Test-TunnelClient)) {
    if (-not $storedKey) { throw 'Falta salvar a runtime API key uma vez: execute setup_credentials.ps1. O MCP local continua disponivel para OpenCode.' }
    & $tunnelClient doctor --profile omnisvera-mia --explain
    if ($LASTEXITCODE -ne 0) { throw "Diagnostico do MCP Tunnel falhou." }
    Start-Process -FilePath $tunnelClient -ArgumentList @("run", "--profile", "omnisvera-mia") `
        -WorkingDirectory $root -WindowStyle Hidden | Out-Null
    for ($attempt = 0; $attempt -lt 30 -and -not (Test-TunnelClient); $attempt++) {
        Start-Sleep -Seconds 1
    }
}
if (-not (Test-TunnelClient)) { throw "MCP Tunnel nao respondeu como live na porta 8080." }

Write-Host "Omnisvera MCP esta ativo." -ForegroundColor Green
Write-Host "Core HTTP : http://127.0.0.1:8765/mcp" -ForegroundColor Cyan
Write-Host "Tunnel    : perfil omnisvera-mia" -ForegroundColor Cyan
Write-Host "ChatGPT   : plugin Omnisvera Companion Fresh" -ForegroundColor Cyan
Write-Host 'OpenCode  : MCP local iniciado automaticamente pelo proprio OpenCode' -ForegroundColor Cyan
if (-not $storedKey) {
    Write-Warning 'O tunel atual funciona, mas sua chave ainda precisa ser salva para reiniciar automaticamente apos desligar o PC.'
}
Write-Host 'Pode fechar este iniciador; os processos continuam em segundo plano.'
