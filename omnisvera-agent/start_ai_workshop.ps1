param([ValidateSet('start','status','pause','stop')][string]$Action = 'status')
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
$python = Join-Path $root '.venv-observer\Scripts\python.exe'
$runtime = Join-Path $root '.autonomy\runtime'
$config = Join-Path $runtime 'ai-workshop-automation.json'
$env:AI_WORKSHOP_CONFIG_FILE = $config
$env:OMNISVERA_AI_WORKSHOP_DB = Join-Path $runtime 'ai-workshop.sqlite3'
$runner = Join-Path $root 'backend\scripts\run_ai_workshop.py'
if ($Action -ne 'start') {
    & $python $runner worker $Action
    exit $LASTEXITCODE
}
if (!(Test-Path -LiteralPath $config)) { throw 'Configuração explícita da oficina ausente.' }
$settings = Get-Content -LiteralPath $config -Raw | ConvertFrom-Json
if (!$settings.enabled) { throw 'Automação desativada na configuração.' }
$lock = Join-Path $runtime 'ai-workshop.worker.lock'
# The native worker enforces single-instance identity, table state and RAM admission.
$arguments = @('-u', ('"' + $runner + '"'), 'worker', 'start', '--worker-id', 'companion-preparation',
    '--lock-file', ('"' + $lock + '"'), '--min-free-ram-mb', '1024', '--lease-seconds', '900', '--idle-seconds', '30')
$child = Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden -PassThru
Write-Output ('Oficina iniciada; PID do lançador: ' + $child.Id)
