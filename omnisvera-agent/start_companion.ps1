param(
  [string]$VaultPath = (Resolve-Path "$PSScriptRoot\..").Path,
  [string]$FastModel = "omnisvera-fast:latest",
  [string]$QualityModel = "qwen2:1.5b",
  [string]$EmbedModel = "nomic-embed-text",
  [ValidateSet("fast", "grounded")]
  [string]$ResponseMode = "grounded",
  [string]$AccessToken = "",
  [string]$MasterToken = "",
  [string]$PlayerToken = "",
  [string]$TokenFile = "",
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
$PlayerProfiles = @{}

if (-not $TokenFile) {
  $TokenFile = Join-Path $Backend "data\access_tokens.json"
}

if (Test-Path $TokenFile) {
  try {
    $savedTokens = Get-Content $TokenFile -Raw | ConvertFrom-Json
    if (-not $MasterToken -and $savedTokens.master_token) {
      $MasterToken = [string]$savedTokens.master_token
    }
    if (-not $PlayerToken -and $savedTokens.player_token) {
      $PlayerToken = [string]$savedTokens.player_token
    }
    if ($savedTokens.player_profiles) {
      foreach ($property in $savedTokens.player_profiles.PSObject.Properties) {
        $PlayerProfiles[$property.Name] = @{
          token = [string]$property.Value.token
          character_path = [string]$property.Value.character_path
          character_title = [string]$property.Value.character_title
        }
      }
    }
  }
  catch {
    Write-Warning "Arquivo local de tokens inválido; novas credenciais serão geradas."
  }
}

if ($AccessToken -and -not $MasterToken) {
  $MasterToken = $AccessToken
}

if (-not $MasterToken) {
  $MasterToken = New-Token
}

if (-not $PlayerToken) {
  $PlayerToken = New-Token
}

$ProfileDefinitions = @{
  vezemir = @{ character_path = "Characters/Individual/Vezemir.md"; character_title = "Vezemir" }
  varkh = @{ character_path = "Characters/Individual/Varkh Nimalis.md"; character_title = "Varkh Nimalis" }
  raziel = @{ character_path = "Characters/Individual/Raziel.md"; character_title = "Raziel" }
  morthak = @{ character_path = "Characters/Individual/Morthak.md"; character_title = "Morthak" }
}
foreach ($profileId in $ProfileDefinitions.Keys) {
  if (-not $PlayerProfiles.ContainsKey($profileId) -or -not $PlayerProfiles[$profileId].token) {
    $PlayerProfiles[$profileId] = @{
      token = New-Token
      character_path = $ProfileDefinitions[$profileId].character_path
      character_title = $ProfileDefinitions[$profileId].character_title
    }
  }
}

$tokenDirectory = Split-Path $TokenFile -Parent
if (-not (Test-Path $tokenDirectory)) {
  New-Item -ItemType Directory -Path $tokenDirectory -Force | Out-Null
}
@{
  master_token = $MasterToken
  player_token = $PlayerToken
  player_profiles = $PlayerProfiles
} | ConvertTo-Json -Depth 5 | Set-Content -Path $TokenFile -Encoding UTF8

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
$env:OMNISVERA_FAST_MODEL = $FastModel
$env:OMNISVERA_QUALITY_MODEL = $QualityModel
$env:OMNISVERA_EMBED_MODEL = $EmbedModel
$env:OMNISVERA_RESPONSE_MODE = $ResponseMode
$env:OLLAMA_MODEL = if ($ResponseMode -eq "grounded") { $QualityModel } else { $FastModel }
$env:OMNISVERA_ACCESS_TOKEN = $MasterToken
$env:OMNISVERA_MASTER_TOKEN = $MasterToken
$env:OMNISVERA_PLAYER_TOKEN = $PlayerToken
$env:OMNISVERA_PLAYER_PROFILES_JSON = ($PlayerProfiles | ConvertTo-Json -Depth 5 -Compress)
$env:OMNISVERA_REBUILD_ON_STARTUP = if ($NoRebuild) { "false" } else { "true" }

$localIps = Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.PrefixOrigin -ne "WellKnown" } |
  Select-Object -ExpandProperty IPAddress

Write-Host ""
Write-Host "Omnisvera Companion" -ForegroundColor Yellow
Write-Host "Vault: $VaultPath"
Write-Host "Modo de resposta: $ResponseMode"
Write-Host "Modelo rápido: $FastModel"
Write-Host "Modelo fundamentado: $QualityModel"
Write-Host "Modelo de embeddings: $EmbedModel"
Write-Host "Token do Mestre: $MasterToken" -ForegroundColor Cyan
Write-Host "Token dos Jogadores: $PlayerToken" -ForegroundColor Green
Write-Host "Acessos individuais:" -ForegroundColor Green
foreach ($profileId in @("vezemir", "varkh", "raziel", "morthak")) {
  Write-Host "  $($PlayerProfiles[$profileId].character_title): $($PlayerProfiles[$profileId].token)"
}
Write-Host "Local: http://127.0.0.1:$Port"
foreach ($ip in $localIps) {
  Write-Host "Wi-Fi/LAN: http://$ip`:$Port"
}
Write-Host ""
Write-Host "Para acesso fora de casa, em outro terminal rode:" -ForegroundColor Yellow
Write-Host "  .\start_cloudflare_tunnel.ps1 -Port $Port"
Write-Host ""

Push-Location $Backend
try {
  & $Python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
}
finally {
  Pop-Location
}
