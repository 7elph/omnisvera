[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$runtimeDir = Join-Path $root '.assistant-runtime\launchers'
$configPath = Join-Path $runtimeDir 'omnisvera-chatgpt-fresh.yaml'
$pidPath = Join-Path $runtimeDir 'tunnel-fresh.pid'
$stdoutPath = Join-Path $runtimeDir 'tunnel-fresh-restart.stdout.log'
$stderrPath = Join-Path $runtimeDir 'tunnel-fresh-restart.stderr.log'
$tunnelExe = Join-Path $root '.local-tools\bin\tunnel-client-v0.0.13\windows-amd64\tunnel-client.exe'

if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
    throw "Configuração fresh não encontrada: $configPath"
}
if (-not (Test-Path -LiteralPath $tunnelExe -PathType Leaf)) {
    throw "tunnel-client não encontrado: $tunnelExe"
}

if (Test-Path -LiteralPath $pidPath -PathType Leaf) {
    $oldPid = [int](Get-Content -LiteralPath $pidPath -Raw)
    $oldProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$oldPid" -ErrorAction SilentlyContinue
    if ($oldProcess) {
        $expectedConfig = '.assistant-runtime\launchers\omnisvera-chatgpt-fresh.yaml'
        if ($oldProcess.Name -ne 'tunnel-client.exe' -or $oldProcess.CommandLine -notlike "*$expectedConfig*") {
            throw "O PID $oldPid não pertence ao túnel fresh esperado; reinício recusado."
        }
        Stop-Process -Id $oldPid -ErrorAction Stop
        Start-Sleep -Milliseconds 800
    }
}

$env:CONTROL_PLANE_API_KEY = Get-LauncherSecret 'CONTROL_PLANE_API_KEY'
$process = Start-Process -FilePath $tunnelExe `
    -ArgumentList @('run', '--config', '.assistant-runtime\launchers\omnisvera-chatgpt-fresh.yaml') `
    -WorkingDirectory $root `
    -WindowStyle Hidden `
    -RedirectStandardOutput $stdoutPath `
    -RedirectStandardError $stderrPath `
    -PassThru
$process.Id | Set-Content -LiteralPath $pidPath -NoNewline

$ready = $false
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $ready = (Invoke-RestMethod 'http://127.0.0.1:8080/readyz' -TimeoutSec 2) -eq 'ready'
    }
    catch {
        $ready = $false
    }
    if ($ready) { break }
    Start-Sleep -Seconds 1
}
if (-not $ready) {
    throw 'O túnel fresh não ficou pronto na porta 8080.'
}

[pscustomobject]@{
    pid = $process.Id
    health = Invoke-RestMethod 'http://127.0.0.1:8080/healthz'
    ready = Invoke-RestMethod 'http://127.0.0.1:8080/readyz'
} | ConvertTo-Json
