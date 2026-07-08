param(
  [string]$VaultPath = (Resolve-Path "$PSScriptRoot\..").Path,
  [string]$Model = "omnisvera-fast:latest",
  [string]$AccessToken = "",
  [int]$Port = 8787,
  [switch]$NoBuild,
  [switch]$NoRebuild
)

$ErrorActionPreference = "Stop"

function New-Token {
  $bytes = New-Object byte[] 18
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try {
    $rng.GetBytes($bytes)
  }
  finally {
    $rng.Dispose()
  }
  return [Convert]::ToBase64String($bytes).Replace("+", "").Replace("/", "").Replace("=", "")
}

$Root = Resolve-Path "$PSScriptRoot\.."
$Backend = Join-Path $PSScriptRoot "backend"
$Frontend = Join-Path $PSScriptRoot "frontend"
$Venv = Join-Path $Backend ".venv"

if (-not $AccessToken) {
  $AccessToken = New-Token
}

if (-not (Test-Path $Venv)) {
  python -m venv $Venv
}

$Python = Join-Path $Venv "Scripts\python.exe"

& $Python -m pip install -q -r (Join-Path $Backend "requirements.txt")

if (-not $NoBuild) {
  Push-Location $Frontend
  try {
    npm install
    npm run build
  }
  finally {
    Pop-Location
  }
}

$env:OMNISVERA_VAULT_PATH = $VaultPath
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = $Model
$env:OMNISVERA_ACCESS_TOKEN = $AccessToken
$env:OMNISVERA_REBUILD_ON_STARTUP = if ($NoRebuild) { "false" } else { "true" }

$localIps = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
  Select-Object -ExpandProperty IPAddress

Write-Host ""
Write-Host "Omnisvera Companion" -ForegroundColor Yellow
Write-Host "Vault: $VaultPath"
Write-Host "Modelo Ollama: $Model"
Write-Host "Token de acesso: $AccessToken" -ForegroundColor Cyan
Write-Host "Local: http://127.0.0.1:$Port"
foreach ($ip in $localIps) {
  Write-Host "Wi-Fi/LAN: http://$ip`:$Port"
}
Write-Host ""
Write-Host "Para acesso fora de casa, em outro terminal rode:" -ForegroundColor Yellow
Write-Host "  .\start_ngrok_tunnel.ps1 -Port $Port"
Write-Host ""

Push-Location $Backend
try {
  & $Python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
}
finally {
  Pop-Location
}
