[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$runtimeDir = Join-Path $root '.assistant-runtime\launchers'
$freshConfig = Join-Path $runtimeDir 'omnisvera-chatgpt-fresh.yaml'
$tunnelExe = Join-Path $root '.local-tools\bin\tunnel-client-v0.0.13\windows-amd64\tunnel-client.exe'

$freshRuntimeKey = Get-LauncherSecret 'CONTROL_PLANE_API_KEY_FRESH'
$freshAdminKey = Get-LauncherSecret 'OPENAI_ADMIN_KEY_FRESH'
Set-LauncherSecret 'CONTROL_PLANE_API_KEY' (ConvertTo-SecureString $freshRuntimeKey -AsPlainText -Force) | Out-Null
Set-LauncherSecret 'OPENAI_ADMIN_KEY' (ConvertTo-SecureString $freshAdminKey -AsPlainText -Force) | Out-Null

$oldListener = Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($oldListener) {
    $oldProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$($oldListener.OwningProcess)"
    if (
        $oldProcess.Name -ne 'tunnel-client.exe' -or
        $oldProcess.CommandLine -notlike '*run --profile omnisvera-mia*'
    ) {
        throw "A porta 8080 pertence a um processo inesperado; promoção recusada: $($oldProcess.CommandLine)"
    }
    Stop-Process -Id $oldProcess.ProcessId -ErrorAction Stop
    Start-Sleep -Milliseconds 800
}

& $tunnelExe profiles add omnisvera-mia --from-file $freshConfig --force
if ($LASTEXITCODE -ne 0) { throw 'Não foi possível promover o perfil omnisvera-mia.' }

& (Join-Path $PSScriptRoot 'restart_fresh_tunnel.ps1')
if ($LASTEXITCODE -ne 0) { throw 'O túnel fresh não reiniciou como perfil canônico.' }

[pscustomobject]@{
    profile = 'omnisvera-mia'
    tunnel_id = 'tunnel_6a962fcd3bf08191a4326fda34446795'
    organization_id = 'org-zxxiNhQsCpmshuH4BvnfqsEz'
    health = Invoke-RestMethod 'http://127.0.0.1:8080/healthz'
    ready = Invoke-RestMethod 'http://127.0.0.1:8080/readyz'
} | ConvertTo-Json
