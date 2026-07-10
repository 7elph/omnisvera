param(
    [int]$IntervalSeconds = 300,
    [switch]$AutoRebuild
)

$ErrorActionPreference = "Stop"

$BackendRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $BackendRoot "..\..")
$Python = Join-Path $BackendRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not $env:OMNISVERA_PLAYER_TOKEN) {
    Write-Error "Defina OMNISVERA_PLAYER_TOKEN antes de iniciar o watchdog."
}

$argsList = @(
    (Join-Path $BackendRoot "rag_watchdog.py"),
    "--root", $RepoRoot.Path,
    "--loop",
    "--interval", $IntervalSeconds
)

if ($AutoRebuild) {
    if (-not $env:OMNISVERA_MASTER_TOKEN) {
        Write-Error "AutoRebuild precisa de OMNISVERA_MASTER_TOKEN para chamar /index/rebuild."
    }
    $argsList += "--auto-rebuild"
}

Write-Host "Iniciando RAG Watchdog do Omnisvera Companion..."
Write-Host "Raiz: $($RepoRoot.Path)"
Write-Host "Intervalo: $IntervalSeconds segundos"
& $Python @argsList
