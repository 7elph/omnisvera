param([int]$Port = 8787)

$ErrorActionPreference = "Stop"
$cloudflared = Join-Path $env:LOCALAPPDATA "Omnisvera\bin\cloudflared.exe"
$runtime = Join-Path $PSScriptRoot "backend\data\cloudflare-tunnel"
$log = Join-Path $runtime "cloudflared.log"
$outLog = Join-Path $runtime "cloudflared.out.log"

if (-not (Test-Path $cloudflared)) {
  throw "cloudflared não encontrado em $cloudflared. Execute o instalador local do Companion."
}
if (-not (Test-NetConnection 127.0.0.1 -Port $Port -InformationLevel Quiet)) {
  throw "O Companion não está ativo na porta $Port. Inicie start_companion.ps1 primeiro."
}

New-Item -ItemType Directory -Force -Path $runtime | Out-Null
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force
Remove-Item $log -Force -ErrorAction SilentlyContinue
Remove-Item $outLog -Force -ErrorAction SilentlyContinue
Start-Process -FilePath $cloudflared -ArgumentList @("tunnel","--url","http://127.0.0.1:$Port","--no-autoupdate") -WindowStyle Hidden -RedirectStandardOutput $outLog -RedirectStandardError $log

$public = $null
for ($i = 0; $i -lt 30 -and -not $public; $i++) {
  Start-Sleep -Milliseconds 500
  if (Test-Path $log) {
    $match = Select-String -Path $log -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' -AllMatches | Select-Object -Last 1
    if ($match) { $public = $match.Matches.Value | Select-Object -First 1 }
  }
}
if (-not $public) { throw "O túnel não publicou uma URL. Consulte $log" }

Set-Content -Path (Join-Path $runtime "public-url.txt") -Value $public -Encoding UTF8
Write-Host "Omnisvera Companion via Cloudflare" -ForegroundColor Yellow
Write-Host "URL pública: $public" -ForegroundColor Cyan
Write-Host "O endereço muda quando o túnel reinicia. Os tokens individuais continuam obrigatórios."
