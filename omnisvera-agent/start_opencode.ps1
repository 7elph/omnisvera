param(
  [int]$Port = 4096,
  [string]$HostAddress = "127.0.0.1"
)

$ErrorActionPreference = "Stop"
$Project = (Resolve-Path $PSScriptRoot).Path
$ConfigDir = Join-Path $Project ".opencode-local"
New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
$env:OPENCODE_CONFIG_DIR = $ConfigDir
$env:XDG_CONFIG_HOME = $ConfigDir
$env:XDG_DATA_HOME = $ConfigDir
$env:XDG_CACHE_HOME = $ConfigDir
$env:XDG_STATE_HOME = $ConfigDir
$userOpenCodeUsername = [Environment]::GetEnvironmentVariable("OPENCODE_SERVER_USERNAME", "User")
$userOpenCodePassword = [Environment]::GetEnvironmentVariable("OPENCODE_SERVER_PASSWORD", "User")
if ([string]::IsNullOrWhiteSpace($env:OPENCODE_SERVER_USERNAME) -and -not [string]::IsNullOrWhiteSpace($userOpenCodeUsername)) {
  $env:OPENCODE_SERVER_USERNAME = $userOpenCodeUsername
}
if ([string]::IsNullOrWhiteSpace($env:OPENCODE_SERVER_PASSWORD) -and -not [string]::IsNullOrWhiteSpace($userOpenCodePassword)) {
  $env:OPENCODE_SERVER_PASSWORD = $userOpenCodePassword
}
if ([string]::IsNullOrWhiteSpace($env:OPENCODE_SERVER_USERNAME)) {
  $env:OPENCODE_SERVER_USERNAME = "sage"
}
$OpenCode = (Get-Command opencode -ErrorAction SilentlyContinue).Source
if (-not $OpenCode) {
  $OpenCode = Join-Path $env:APPDATA "npm\node_modules\opencode-ai\bin\opencode.exe"
}
if (-not (Test-Path -LiteralPath $OpenCode)) {
  throw "OpenCode não foi encontrado. Instale-o ou ajuste o caminho em start_opencode.ps1."
}

Push-Location $Project
try {
  Write-Host "OpenCode · OMNISVERA Companion" -ForegroundColor Yellow
  Write-Host "Projeto: $Project"
  Write-Host "Acesse: http://$HostAddress`:$Port"
  if (-not [string]::IsNullOrWhiteSpace($env:OPENCODE_SERVER_PASSWORD)) {
    Write-Host "Login Basic: $env:OPENCODE_SERVER_USERNAME + senha OPENCODE_SERVER_PASSWORD" -ForegroundColor DarkYellow
  }
  Write-Host "Leia AGENTS.md antes de editar. Não faça push sem autorização." -ForegroundColor Cyan
  & $OpenCode web --hostname $HostAddress --port $Port
}
finally {
  Pop-Location
}
