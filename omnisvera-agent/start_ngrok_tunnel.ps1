param(
  [int]$Port = 8787
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command ngrok -ErrorAction SilentlyContinue)) {
  throw "ngrok não encontrado. Instale/configure ngrok ou use Tailscale/VPN."
}

$existing = Get-Process ngrok -ErrorAction SilentlyContinue
if (-not $existing) {
  Start-Process -FilePath "ngrok" -ArgumentList @("http", "http://localhost:$Port") -WindowStyle Hidden
  Start-Sleep -Seconds 4
}

$tunnels = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels"
$public = $tunnels.tunnels | Where-Object { $_.proto -eq "https" } | Select-Object -First 1

if (-not $public) {
  throw "ngrok está rodando, mas não encontrei túnel HTTPS em http://127.0.0.1:4040/api/tunnels"
}

Write-Host ""
Write-Host "Omnisvera Companion via ngrok" -ForegroundColor Yellow
Write-Host "URL pública: $($public.public_url)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Abra essa URL no celular e informe o token impresso pelo start_companion.ps1."
Write-Host "Não compartilhe a URL/token com jogadores se houver notas de mestre no índice."
