[CmdletBinding()]
param(
    [string]$TunnelId = 'tunnel_6a960fbaf06881919bf35ad8848f7941',
    [string[]]$OrganizationIds = @(
        'org-622xRFDQQz4vD3zj8MUfBL63',
        'org-zxxiNhQsCpmshuH4BvnfqsEz'
    ),
    [string]$WorkspaceId = 'a18384f4-bdd9-446b-8e5d-8e4c3fc569af'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$tunnelClient = Join-Path $root '.local-tools\bin\tunnel-client-v0.0.13\windows-amd64\tunnel-client.exe'
if (-not (Test-Path -LiteralPath $tunnelClient -PathType Leaf)) {
    throw "tunnel-client nao encontrado: $tunnelClient"
}

$adminKey = Get-LauncherSecret 'OPENAI_ADMIN_KEY'
try {
    $env:OPENAI_ADMIN_KEY = $adminKey
    $arguments = @('admin', 'tunnels', 'update', $TunnelId)
    foreach ($organizationId in $OrganizationIds) {
        $arguments += @('--organization-id', $organizationId)
    }
    $arguments += @('--workspace-id', $WorkspaceId, '--json')
    $updatedOutput = @(& $tunnelClient @arguments 2>&1)
    $updateExitCode = $LASTEXITCODE
    if ($updateExitCode -ne 0) {
        $safeDetails = (($updatedOutput -join [Environment]::NewLine) -replace 'sk-(?:admin-)?[A-Za-z0-9_-]+', '[redacted]')
        throw "Falha ao vincular o workspace ao tunel: $safeDetails"
    }

    $updated = ($updatedOutput -join [Environment]::NewLine) | ConvertFrom-Json
    if ($updated.id -ne $TunnelId) { throw 'O control plane retornou outro tunel.' }
    foreach ($organizationId in $OrganizationIds) {
        if ($organizationId -notin @($updated.organization_ids)) { throw "A organizacao esperada nao ficou vinculada: $organizationId" }
    }
    if ($WorkspaceId -notin @($updated.workspace_ids)) { throw 'O workspace do ChatGPT nao ficou vinculado.' }

    Write-Host 'Tunel vinculado ao workspace do ChatGPT e verificado no control plane.' -ForegroundColor Green
}
finally {
    Remove-Item Env:OPENAI_ADMIN_KEY -ErrorAction SilentlyContinue
    $adminKey = $null
}
