<#
.SYNOPSIS
    Start a Cloudflare quick tunnel for the Omnisvera MCP HTTP bridge.

.DESCRIPTION
    Starts a Cloudflare quick tunnel that forwards to the MCP HTTP server on port 8765.
    This is a temporary tunnel for testing. For production, use the OpenAI tunnel-client.

.PARAMETER McpPort
    Port of the MCP HTTP server. Default: 8765.

.EXAMPLE
    .\start_mcp_tunnel.ps1
    .\start_mcp_tunnel.ps1 -McpPort 9000
#>
param(
    [int]$McpPort = 8765
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Omnisvera MCP Tunnel"

# Find cloudflared
$root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$cloudflared = Join-Path $root "AppData\Local\Omnisvera\bin\cloudflared.exe"

if (-not (Test-Path -LiteralPath $cloudflared -PathType Leaf)) {
    # Try alternative locations
    $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source
    if (-not $cloudflared) {
        Write-Error "cloudflared not found. Install from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/"
        exit 1
    }
}

# Check if MCP HTTP server is running
function Test-McpPort([int]$Port) {
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

if (-not (Test-McpPort $McpPort)) {
    Write-Warning "MCP HTTP server not running on port $McpPort"
    Write-Host "Starting MCP HTTP server..." -ForegroundColor Yellow
    
    $python = Join-Path $root ".omnisvera-tools\Scripts\python.exe"
    $serverScript = Join-Path $root ".local-tools\mcp_http_server.py"
    
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        Write-Error "Python not found at $python"
        exit 1
    }
    
    $env:OMNISVERA_MCP_HTTP_PORT = $McpPort
    Start-Process -FilePath $python -ArgumentList $serverScript `
        -WorkingDirectory (Join-Path $root ".local-tools") `
        -WindowStyle Hidden | Out-Null
    
    # Wait for server to start
    for ($attempt = 0; $attempt -lt 30 -and -not (Test-McpPort $McpPort); $attempt++) {
        Start-Sleep -Milliseconds 500
    }
    
    if (-not (Test-McpPort $McpPort)) {
        Write-Error "Failed to start MCP HTTP server on port $McpPort"
        exit 1
    }
    Write-Host "MCP HTTP server started on port $McpPort" -ForegroundColor Green
}

Write-Host "=== Omnisvera MCP Cloudflare Tunnel ===" -ForegroundColor Cyan
Write-Host "  MCP HTTP: http://127.0.0.1:${McpPort}/mcp"
Write-Host "  Tunnel:   cloudflare quick tunnel"
Write-Host ""

# Stop any existing cloudflare tunnels
$existingTunnels = Get-Process cloudflared -ErrorAction SilentlyContinue
if ($existingTunnels) {
    Write-Host "Stopping existing cloudflare tunnels..." -ForegroundColor Yellow
    $existingTunnels | Stop-Process -Force
    Start-Sleep -Seconds 2
}

# Start cloudflare tunnel
Write-Host "Starting cloudflare tunnel -> port $McpPort..." -ForegroundColor Yellow
$args = @("tunnel", "--url", "http://127.0.0.1:${McpPort}", "--no-autoupdate")
$process = Start-Process -FilePath $cloudflared -ArgumentList $args `
    -PassThru -NoNewWindow `
    -RedirectStandardOutput "$env:TEMP\mcp-tunnel-out.log" `
    -RedirectStandardError "$env:TEMP\mcp-tunnel-err.log"

Write-Host "  Tunnel PID: $($process.Id)" -ForegroundColor Green

# Wait for tunnel to register and get URL
Start-Sleep -Seconds 5

# Try to extract tunnel URL from stderr log
$tunnelUrl = ""
$errLog = "$env:TEMP\mcp-tunnel-err.log"
if (Test-Path $errLog) {
    $content = Get-Content $errLog -Raw
    if ($content -match "https://[a-z0-9-]+\.trycloudflare\.com") {
        $tunnelUrl = $Matches[0]
    }
}

Write-Host ""
if ($tunnelUrl) {
    Write-Host "Tunnel URL: $tunnelUrl" -ForegroundColor Green
    Write-Host "MCP Endpoint: $tunnelUrl/mcp" -ForegroundColor Green
    Write-Host ""
    Write-Host "Add this to ChatGPT MCP settings:" -ForegroundColor Cyan
    Write-Host "  Server URL: $tunnelUrl/mcp" -ForegroundColor White
} else {
    Write-Host "Tunnel starting... check URL in: $errLog" -ForegroundColor Yellow
    Write-Host "Look for: https://xxx.trycloudflare.com" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel" -ForegroundColor Gray

# Keep running until Ctrl+C
try {
    $process.WaitForExit()
}
finally {
    if (!$process.HasExited) {
        $process.Kill()
    }
}
