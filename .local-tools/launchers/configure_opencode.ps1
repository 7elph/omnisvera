[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')
$folder = Join-Path $env:USERPROFILE '.config\opencode'
$path = Join-Path $folder 'opencode.json'
if (-not (Test-Path -LiteralPath $folder)) { New-Item -ItemType Directory -Path $folder | Out-Null }
$config = if (Test-Path -LiteralPath $path) {
    Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
} else { [pscustomobject]@{} }
if (-not $config.PSObject.Properties['mcp']) {
    $config | Add-Member -NotePropertyName mcp -NotePropertyValue ([pscustomobject]@{})
}
$entry = [pscustomobject]@{
    type = 'local'
    enabled = $true
    command = @(
        (Join-Path $LauncherRoot '.omnisvera-tools\Scripts\python.exe'),
        (Join-Path $LauncherRoot '.local-tools\mcp_opencode_server.py')
    )
    timeout = 30000
}
$existing = $config.mcp.PSObject.Properties['omnisvera']
if ($existing -and (($existing.Value | ConvertTo-Json -Depth 20 -Compress) -eq ($entry | ConvertTo-Json -Depth 20 -Compress))) {
    Write-Host 'Omnisvera MCP ja esta configurado no OpenCode.'
    return
}
if (Test-Path -LiteralPath $path) {
    Copy-Item -LiteralPath $path -Destination ($path + '.before-omnisvera-' + [Guid]::NewGuid().ToString('N') + '.bak')
}
$config.mcp | Add-Member -NotePropertyName omnisvera -NotePropertyValue $entry -Force
$json = $config | ConvertTo-Json -Depth 100
[IO.File]::WriteAllText($path, $json, [Text.UTF8Encoding]::new($false))
Write-Host 'Omnisvera MCP adicionado; configuracoes existentes preservadas.'
