$ErrorActionPreference = 'Stop'
$claudeRoot = Split-Path -Parent $PSScriptRoot
$claudeRuntime = Join-Path $claudeRoot '.assistant-runtime\claude-connector'
$claudeCloudflared = Join-Path $env:LOCALAPPDATA 'Omnisvera\bin\cloudflared.exe'
$claudePython = Join-Path $claudeRoot '.omnisvera-tools\Scripts\python.exe'
New-Item -ItemType Directory -Path $claudeRuntime -Force | Out-Null
$claudeOwner = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls $claudeRuntime /inheritance:r /grant:r "${claudeOwner}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Failed to protect connector credentials' }
$claudePasswordFile = Join-Path $claudeRuntime 'login-password.txt'
if (-not (Test-Path -LiteralPath $claudePasswordFile)) {
    $claudeBytes = New-Object byte[] 32
    $claudeRng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    $claudeRng.GetBytes($claudeBytes)
    [IO.File]::WriteAllText($claudePasswordFile, [Convert]::ToBase64String($claudeBytes))
    $claudeRng.Dispose()
}
if (Get-NetTCPConnection -LocalPort 8767 -State Listen -ErrorAction SilentlyContinue) {
    throw 'Port 8767 already occupied; no existing service changed'
}
$claudeTunnelLog = Join-Path $claudeRuntime 'tunnel.err.log'
$claudeTunnel = Start-Process -FilePath $claudeCloudflared -ArgumentList @('tunnel','--url','http://127.0.0.1:8767','--no-autoupdate') -WindowStyle Hidden -PassThru -RedirectStandardError $claudeTunnelLog -RedirectStandardOutput (Join-Path $claudeRuntime 'tunnel.out.log')
$claudeDeadline = (Get-Date).AddSeconds(45)
$claudeUrl = $null
while ((Get-Date) -lt $claudeDeadline) {
    if (Test-Path -LiteralPath $claudeTunnelLog) {
        $claudeMatch = [regex]::Match((Get-Content -LiteralPath $claudeTunnelLog -Raw), 'https://[a-z0-9-]+\.trycloudflare\.com')
        if ($claudeMatch.Success) { $claudeUrl = $claudeMatch.Value; break }
    }
    Start-Sleep -Milliseconds 500
}
if (-not $claudeUrl) { throw 'Cloudflare did not return an HTTPS URL; inspect tunnel.err.log' }
@{issuer=$claudeUrl; tunnel_pid=$claudeTunnel.Id} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $claudeRuntime 'config.json')
$claudeServer = Start-Process -FilePath $claudePython -ArgumentList (Join-Path $PSScriptRoot 'claude_connector.py') -WorkingDirectory $claudeRoot -WindowStyle Hidden -PassThru -RedirectStandardError (Join-Path $claudeRuntime 'server.err.log') -RedirectStandardOutput (Join-Path $claudeRuntime 'server.out.log')
Write-Output "PUBLIC MCP URL: $claudeUrl/mcp"
Write-Output "Connector PID: $($claudeServer.Id); tunnel PID: $($claudeTunnel.Id)"
Write-Output "Login password file: $claudePasswordFile"
