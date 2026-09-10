# Omnisvera AI Console — Tailscale Serve (remote privado, sem expor LAN)
# Uso: powershell -ExecutionPolicy Bypass -File tools/ai-console/start-mobile.ps1
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Resolve-Path (Join-Path $here "..\..")
Set-Location $here

$env:CONSOLE_HOST = "127.0.0.1"
$env:CONSOLE_PORT = "8787"
$env:AI_CONSOLE_PORT = "8787"
$env:OLLAMA_MODEL = "gpt-oss:20b-cloud"
$env:DEFAULT_MODEL = "gpt-oss:20b-cloud"

Write-Host "== Omnisvera AI Console v0.1 (Tailscale) ==" -ForegroundColor Cyan
Write-Host "Console: http://127.0.0.1:8787 (127.0.0.1 only, sem 0.0.0.0)" 
Write-Host "MCP: http://127.0.0.1:8765/mcp — NÃO expor"
Write-Host "Ollama: http://127.0.0.1:11434 — NÃO expor"

# 1. Inicia Console em background
Write-Host "`n[1/4] Iniciando AI Console..." -ForegroundColor Yellow
$console = Start-Process -FilePath "node" -ArgumentList "server.js" -WorkingDirectory $here -PassThru -WindowStyle Minimized
Start-Sleep 3
try {
  $s = Invoke-RestMethod -Uri "http://127.0.0.1:8787/api/status" -TimeoutSec 5
  Write-Host "  Console OK: MCP $($s.mcp) Tools $($s.tools) Ollama $($s.ollama)" -ForegroundColor Green
} catch {
  Write-Host "  Console ainda iniciando ou falhou: $_" -ForegroundColor Red
}

# 2. Verifica Tailscale
Write-Host "`n[2/4] Verificando Tailscale..." -ForegroundColor Yellow
$tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $tailscale) { $tailscale = Get-Command "$env:ProgramFiles\Tailscale\tailscale.exe" -ErrorAction SilentlyContinue }
if (-not $tailscale) {
  Write-Host "  Tailscale não encontrado. Instale em https://tailscale.com/download" -ForegroundColor Red
  exit 1
}
try { & $tailscale.Source status | Out-String | Select-Object -First 5 | Write-Host } catch { Write-Host "  tailscale status falhou: $_" -ForegroundColor Yellow }

# 3. Configura Serve
Write-Host "`n[3/4] Configurando Tailscale Serve..." -ForegroundColor Yellow
try {
  & $tailscale.Source serve --bg http://127.0.0.1:8787 2>&1 | Write-Host
} catch {
  Write-Host "  tailscale serve falhou: $_" -ForegroundColor Red
}
Start-Sleep 2

# 4. Mostra URL
Write-Host "`n[4/4] URLs:" -ForegroundColor Yellow
Write-Host "  PC:     http://127.0.0.1:8787" -ForegroundColor Green
try {
  $serveStatus = & $tailscale.Source serve status 2>&1 | Out-String
  Write-Host $serveStatus
  # tenta extrair https://*.ts.net
  $m = [regex]::Match($serveStatus, "https://[^\s]+")
  if ($m.Success) {
    Write-Host "  REMOTE: $($m.Value)" -ForegroundColor Green
    Write-Host "  (abra no celular conectado à mesma tailnet, em 4G ou Wi-Fi diferente)" -ForegroundColor Cyan
  } else {
    Write-Host "  REMOTE: veja 'tailscale serve status' acima para a URL https://....ts.net" -ForegroundColor Yellow
  }
} catch {
  Write-Host "  Não foi possível obter serve status: $_" -ForegroundColor Yellow
}

Write-Host "`nConsole PID $($console.Id) — deixe esta janela aberta. Ctrl+C para parar." -ForegroundColor Cyan
Write-Host "Logs: http://127.0.0.1:8787/api/status  e  tailscale serve status"
