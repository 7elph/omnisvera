param(
    [ValidateSet('Install', 'Status', 'Stop', 'Uninstall', 'Check', 'Once')]
    [string]$Action = 'Status'
)
$ErrorActionPreference = 'Stop'
$taskName = 'OMNISVERA Memory Guard'
$guardScript = Join-Path $PSScriptRoot 'backend\scripts\memory_guard.py'
$venv = Join-Path $PSScriptRoot 'backend\.venv'
$pythonConsole = Join-Path $venv 'Scripts\python.exe'
$pythonWindowless = Join-Path $venv 'Scripts\pythonw.exe'
# Prefer the installed base runtime: no extra venv redirector/worker pair.
$baseHome = (Get-Content -LiteralPath (Join-Path $venv 'pyvenv.cfg') |
    Select-String '^home = (.+)$' | Select-Object -First 1).Matches.Groups[1].Value
if ($baseHome -and (Test-Path -LiteralPath (Join-Path $baseHome 'pythonw.exe'))) {
    $pythonWindowless = Join-Path $baseHome 'pythonw.exe'
    $pythonConsole = Join-Path $baseHome 'python.exe'
}
if (!(Test-Path -LiteralPath $pythonWindowless) -or !(Test-Path -LiteralPath $guardScript)) {
    throw 'O runtime local ou o monitor nao esta disponivel. Nenhuma instalacao sera feita.'
}
$existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existing -and ($existing.Actions.Count -ne 1 -or
    $existing.Actions[0].Arguments -ne ('"{0}" --watch' -f $guardScript) -or
    $existing.Actions[0].Execute -ne $pythonWindowless)) {
    throw 'Ja existe uma tarefa com este nome e outra configuracao; ela nao sera alterada.'
}
switch ($Action) {
    'Install' {
        $stopRequest = Join-Path $env:LOCALAPPDATA 'Omnisvera\memory-guard\stop.request'
        if (Test-Path -LiteralPath $stopRequest) { Remove-Item -LiteralPath $stopRequest }
        $identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
        $launch = New-ScheduledTaskAction -Execute $pythonWindowless `
            -Argument ('"{0}" --watch' -f $guardScript) -WorkingDirectory $PSScriptRoot
        $trigger = New-ScheduledTaskTrigger -AtLogOn -User $identity
        $principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew `
            -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries `
            -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden `
            -RestartCount 1 -RestartInterval (New-TimeSpan -Minutes 1)
        Register-ScheduledTask -TaskName $taskName -Action $launch -Trigger $trigger `
            -Principal $principal -Settings $settings -Description `
            'Monitor local de RAM sem IA. Limpeza somente de filhos registrados de ensaios encerrados.' `
            -Force | Out-Null
        Start-ScheduledTask -TaskName $taskName
        Get-ScheduledTask -TaskName $taskName | Select-Object TaskName, State
    }
    'Stop' {
        & $pythonConsole $guardScript --stop
        if ($existing) { Disable-ScheduledTask -TaskName $taskName | Out-Null }
        'Parada solicitada; somente este monitor encerrara em ate 30 segundos.'
    }
    'Uninstall' {
        & $pythonConsole $guardScript --stop
        if ($existing) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false }
        'Agendamento removido. O registro local foi preservado.'
    }
    'Status' {
        if ($existing) { $existing | Select-Object TaskName, State }
        & $pythonConsole $guardScript --status
    }
    'Check' { & $pythonConsole $guardScript --check; exit $LASTEXITCODE }
    'Once' { & $pythonConsole $guardScript --once; exit $LASTEXITCODE }
}
