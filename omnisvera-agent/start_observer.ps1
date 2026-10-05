param([int]$Port = 18914, [switch]$ShowToken)
$ErrorActionPreference = 'Stop'
$runtimePath = Join-Path $PSScriptRoot '.observer-runtime'
$secretPath = Join-Path $runtimePath 'operator-token.xml'
$databasePath = Join-Path (Split-Path $PSScriptRoot) '.assistant-runtime\omnisvera-mcp\memory.db'
$pythonPath = Join-Path $PSScriptRoot '.venv-observer\Scripts\python.exe'
if (!(Test-Path -LiteralPath $databasePath)) { throw 'Operational database missing; nothing was created.' }
if (!(Test-Path -LiteralPath $pythonPath)) { throw 'Install requirements-observer.txt in .venv-observer first.' }
if (!(Test-Path -LiteralPath $secretPath)) {
    New-Item -ItemType Directory -Path $runtimePath -Force | Out-Null
    $bytes = New-Object byte[] 48
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    ConvertTo-SecureString ([Convert]::ToBase64String($bytes)) -AsPlainText -Force | Export-Clixml -LiteralPath $secretPath
}
# Windows DPAPI: this credential is decryptable only in the owning user context.
$secureToken = Import-Clixml -LiteralPath $secretPath
$credential = New-Object System.Management.Automation.PSCredential('observer', $secureToken)
if ($ShowToken) { $credential.GetNetworkCredential().Password; return }
$env:OMNISVERA_APP_DB = $databasePath
$env:OMNISVERA_APP_TOKEN = $credential.GetNetworkCredential().Password
try {
    Push-Location (Join-Path $PSScriptRoot 'backend')
    & $pythonPath -m uvicorn omnisvera_app:configured_app --factory --host 127.0.0.1 --port $Port
} finally {
    Pop-Location
    Remove-Item Env:OMNISVERA_APP_TOKEN -ErrorAction SilentlyContinue
    Remove-Item Env:OMNISVERA_APP_DB -ErrorAction SilentlyContinue
}
