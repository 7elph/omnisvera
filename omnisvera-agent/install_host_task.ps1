param([int]$Port=8787,[string]$TaskName='OmnisveraCompanion')
$ErrorActionPreference='Stop'
$HostPython=Join-Path $PSScriptRoot 'backend/.venv/Scripts/python.exe'
& $HostPython (Join-Path $PSScriptRoot 'serve_companion.py') --check
if ($LASTEXITCODE -ne 0) { throw 'A instalação precisa passar no --check antes do agendamento.' }
$HostUser=[System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$HostRunner=Join-Path $PSScriptRoot 'host_run.ps1'
$HostAction=New-ScheduledTaskAction -Execute 'powershell.exe' -Argument ('-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}" -Port {1}' -f $HostRunner,$Port) -WorkingDirectory $PSScriptRoot
$HostTrigger=New-ScheduledTaskTrigger -AtLogOn -User $HostUser
$HostPrincipal=New-ScheduledTaskPrincipal -UserId $HostUser -LogonType Interactive -RunLevel Limited
$HostSettings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { throw 'Já existe tarefa com esse nome; nenhuma tarefa foi substituída.' }
Register-ScheduledTask -TaskName $TaskName -Action $HostAction -Trigger $HostTrigger -Principal $HostPrincipal -Settings $HostSettings | Select-Object TaskName,State
# Starts at the next user logon; does not interrupt a currently running server.
