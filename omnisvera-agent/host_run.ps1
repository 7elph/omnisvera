param([int]$Port=8787)
$ErrorActionPreference='Stop'
Set-Location -LiteralPath $PSScriptRoot
$HostLogDir=Join-Path $PSScriptRoot 'host-data/logs'
New-Item -ItemType Directory -Path $HostLogDir -Force | Out-Null
& (Join-Path $PSScriptRoot 'backend/.venv/Scripts/python.exe') (Join-Path $PSScriptRoot 'serve_companion.py') --port $Port >> (Join-Path $HostLogDir 'server.log') 2>&1
exit $LASTEXITCODE
