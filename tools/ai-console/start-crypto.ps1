$ErrorActionPreference = 'Stop'
$env:OMNISVERA_AI_CONSOLE_PROFILE = 'crypto'
$env:AI_CONSOLE_PORT = '8791'
$env:AI_CONSOLE_HOST = '127.0.0.1'
$env:CONSOLE_HOST = '127.0.0.1'
Push-Location $PSScriptRoot
try { & node server.js } finally { Pop-Location }
