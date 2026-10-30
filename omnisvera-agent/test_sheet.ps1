param(
    [ValidateSet('raziel', 'morthak', 'vezemir', 'dorn7')]
    [string[]]$Personagens = @('raziel', 'morthak'),
    [int]$Porta = 8871
)
$ErrorActionPreference = 'Stop'
$sheetPython = Join-Path $PSScriptRoot '.venv-observer\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $sheetPython)) {
    throw 'Python de testes não encontrado em .venv-observer. Use backend/scripts/run_sheet_test.py com seu Python configurado.'
}
& $sheetPython (Join-Path $PSScriptRoot 'backend\scripts\run_sheet_test.py') --port $Porta --actors @Personagens
exit $LASTEXITCODE
