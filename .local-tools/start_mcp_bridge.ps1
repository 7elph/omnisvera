<#
.SYNOPSIS
    Start the Omnisvera MCP HTTP bridge + optional cloudflare tunnel.

.DESCRIPTION
    Starts the MCP HTTP server on port 8765 (configurable via OMNISVERA_MCP_HTTP_PORT).
    Optionally starts a cloudflare quick tunnel to expose the MCP endpoint publicly.

.PARAMETER Port
    HTTP port for the MCP bridge. Default: 8765.

.PARAMETER Tunnel
    If specified, starts a cloudflare quick tunnel pointing to the MCP port.

.PARAMETER Detach
    If specified, runs the server in background (detached process).

.EXAMPLE
    .\start_mcp_bridge.ps1
    .\start_mcp_bridge.ps1 -Tunnel
    .\start_mcp_bridge.ps1 -Port 9000 -Tunnel -Detach
#>
param(
    [int]$Port = 8765,
    [switch]$Tunnel,
    [switch]$Detach
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir
$pythonExe = Join-Path $rootDir "..\.omnisvera-tools\Scripts\python.exe"
$serverScript = Join-Path $scriptDir "mcp_http_server.py"
$cloudflared = Join-Path $rootDir "..\AppData\Local\Omnisvera\bin\cloudflared.exe"

# Validate
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found at $pythonExe"
    exit 1
}
if (-not (Test-Path $serverScript)) {
    Write-Error "MCP server script not found at $serverScript"
    exit 1
}

# Set environment
$env:OMNISVERA_MCP_HTTP_HOST = "127.0.0.1"
$env:OMNISVERA_MCP_HTTP_PORT = $Port

Write-Host "=== Omnisvera MCP Bridge ===" -ForegroundColor Cyan
Write-Host "  Host:    127.0.0.1"
Write-Host "  Port:    $Port"
Write-Host "  Path:    /mcp"
Write-Host "  URL:     http://127.0.0.1:${Port}/mcp"
Write-Host ""

# Start the MCP HTTP server
if ($Detach) {
    Write-Host "Starting MCP bridge in background..." -ForegroundColor Yellow
    $process = Start-Process -FilePath $pythonExe -ArgumentList $serverScript `
        -WorkingDirectory $rootDir -PassThru -NoNewWindow `
        -RedirectStandardOutput "$env:TEMP\mcp-bridge-out.log" `
        -RedirectStandardError "$env:TEMP\mcp-bridge-err.log"
    Write-Host "  PID: $($process.Id)" -ForegroundColor Green
} else {
    Write-Host "Starting MCP bridge (Ctrl+C to stop)..." -ForegroundColor Yellow
}

# Start tunnel if requested
if ($Tunnel) {
    if (-not (Test-Path $cloudflared)) {
        Write-Warning "cloudflared not found at $cloudflared"
        Write-Warning "Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/"
    } else {
        Write-Host "Starting cloudflare tunnel -> port $Port..." -ForegroundColor Yellow
        if ($Detach) {
            $tunnelProcess = Start-Process -FilePath $cloudflared `
                -ArgumentList "tunnel --url http://127.0.0.1:${Port} --no-autoupdate" `
                -PassThru -NoNewWindow `
                -RedirectStandardOutput "$env:TEMP\mcp-tunnel-out.log" `
                -RedirectStandardError "$env:TEMP\mcp-tunnel-err.log"
            Write-Host "  Tunnel PID: $($tunnelProcess.Id)" -ForegroundColor Green
            Write-Host ""
            Write-Host "Check tunnel URL in: $env:TEMP\mcp-tunnel-err.log" -ForegroundColor Cyan
        } else {
            Write-Host "Tunnel will start in a separate window..." -ForegroundColor Cyan
            Start-Process -FilePath $cloudflared `
                -ArgumentList "tunnel --url http://127.0.0.1:${Port} --no-autoupdate"
        }
    }
}

if (-not $Detach) {
    # Run server in foreground
    & $pythonExe $serverScript
}
