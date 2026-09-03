# Omnisvera Hourly Scheduler
# Runs the observation → signal capture cycle every hour
# Usage: .\start_scheduler.ps1

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $scriptDir "..\.omnisvera-tools\Scripts\python.exe"
$schedulerModule = "omnisvera_mcp.scheduler"
$rootPath = $scriptDir

Write-Host "Starting Omnisvera Hourly Scheduler..."
Write-Host "Python: $venvPython"
Write-Host "Root: $rootPath"
Write-Host "Interval: 3600 seconds (1 hour)"
Write-Host ""

# Run the scheduler in loop mode
& $venvPython -m $schedulerModule --loop --interval 3600 --root $rootPath
