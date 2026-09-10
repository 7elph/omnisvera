[CmdletBinding()]
param(
    [int]$Port = 8787,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Omnisvera Companion"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$agent = Join-Path $root "omnisvera-agent"
$backendLauncher = Join-Path $agent "start_companion.ps1"
$url = "http://127.0.0.1:$Port"
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

function Get-PortOwnerInfo([int]$Port) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -eq $conn) { return $null }
        $ownerPid = $conn.OwningProcess
        $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$ownerPid" -ErrorAction SilentlyContinue
        return [PSCustomObject]@{
            PID = $ownerPid
            ProcessName = if ($proc) { $proc.Name } else { $null }
            CommandLine = if ($proc) { $proc.CommandLine } else { $null }
            ExecutablePath = if ($proc) { $proc.ExecutablePath } else { $null }
        }
    } catch { return $null }
}

function Test-CompanionHealth([int]$Port, [string]$Token) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -Headers @{ "X-Omnisvera-Token" = $Token } -TimeoutSec 3 -ErrorAction Stop
        if ($null -ne $resp -and $resp.backend -eq "ok") { return $true }
        return $false
    } catch { return $false }
}

$masterToken = (Get-Content -LiteralPath (Join-Path $agent "backend\data\access_tokens.json") -Raw | ConvertFrom-Json).master_token
if (-not $masterToken) { throw "master_token nao encontrado em backend\data\access_tokens.json" }

if (Test-LocalPort $Port) {
    if (Test-CompanionHealth -Port $Port -Token $masterToken) {
        Write-Host "Companion ja esta rodando em $url (health ok)." -ForegroundColor Green
    } else {
        $owner = Get-PortOwnerInfo -Port $Port
        if ($owner) {
            throw "Porta $Port ja esta em uso por PID $($owner.PID) ($($owner.ProcessName))`nCommandLine: $($owner.CommandLine)`nExecutavel: $($owner.ExecutablePath)`nO endpoint /health nao respondeu como Companion (Cannot GET /health ou token invalido).`nProvavel ocupante: AI Console (node server.js em 8787/8791) ou outro servico.`nLibere a porta (feche o AI Console, use -Port 8788, ou pare o processo) e tente novamente. Nenhum processo foi encerrado automaticamente."
        } else {
            throw "Porta $Port esta ocupada (TCP aberto) mas /health nao respondeu como Companion e nao foi possivel identificar o processo dono. Libere a porta."
        }
    }
} else {
    Write-Host "Porta $Port livre, iniciando Companion..." -ForegroundColor Yellow
    Start-Process powershell.exe -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $backendLauncher,
        "-Port", $Port, "-NoBuild", "-NoRebuild"
    ) -WorkingDirectory $agent -WindowStyle Hidden | Out-Null
    $deadline = [DateTime]::UtcNow.AddSeconds(90)
    $healthy = $false
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-CompanionHealth -Port $Port -Token $masterToken) { $healthy = $true; break }
        Start-Sleep -Milliseconds 700
    }
    if (-not $healthy) {
        if (Test-LocalPort $Port) {
            $owner = Get-PortOwnerInfo -Port $Port
            if ($owner) {
                throw "Companion nao respondeu em $url/health apos 90s (porta aberta mas health falhou).`nDono atual da porta ${Port}: PID $($owner.PID) ($($owner.ProcessName))`nCommandLine: $($owner.CommandLine)`nVerifique logs do backend em $agent\backend. Nenhum processo foi morto."
            } else {
                throw "Companion nao respondeu em $url/health apos 90s (porta aberta). Verifique logs."
            }
        } else {
            throw "Companion nao abriu a porta $Port apos 90s."
        }
    }
    Write-Host "Companion iniciou e respondeu em $url/health" -ForegroundColor Green
}

$health = Invoke-RestMethod -Uri "$url/health" -Headers @{ "X-Omnisvera-Token" = $masterToken } -TimeoutSec 10
Write-Host "Companion local: $url" -ForegroundColor Green

$tailnetUrl = Enable-PrivateTailnetService $Port
$response = Invoke-WebRequest -UseBasicParsing -Uri $tailnetUrl -TimeoutSec 20
if ($response.StatusCode -ne 200) { throw 'Companion nao respondeu pelo HTTPS do Tailscale.' }
Write-Host "Companion Tailscale: $tailnetUrl" -ForegroundColor Cyan
Write-Host 'Jogadores precisam de acesso autorizado a tailnet e do proprio token do Companion.'
if (-not $NoBrowser) { Start-Process $tailnetUrl }
Write-Host 'Pode fechar este iniciador; o servico continua em segundo plano.' -ForegroundColor Green
