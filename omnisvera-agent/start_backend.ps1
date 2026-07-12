param(
  [int]$Port = 8787
)

$ErrorActionPreference = "Stop"

# Reutiliza as credenciais persistidas localmente pelo inicializador oficial.
# Assim, reiniciar o backend não invalida o acesso já salvo nos celulares.
& (Join-Path $PSScriptRoot "start_companion.ps1") -Port $Port -NoBuild -NoRebuild
