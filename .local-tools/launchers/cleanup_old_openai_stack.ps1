[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$tunnelExe = Join-Path $root '.local-tools\bin\tunnel-client-v0.0.13\windows-amd64\tunnel-client.exe'
$organizationId = 'org-zxxiNhQsCpmshuH4BvnfqsEz'
$freshTunnelId = 'tunnel_6a962fcd3bf08191a4326fda34446795'
$oldTunnelId = 'tunnel_6a8fe7e703b08191b816cad825a6268d'
$oldProjectId = 'proj_h8mpp90TmQmuF3ZeJ5WksH3I'
$oldAdminKeyId = 'key_jxl412u0wFZ6nSa5'

$adminKey = Get-LauncherSecret 'OPENAI_ADMIN_KEY'
$env:OPENAI_ADMIN_KEY = $adminKey
$headers = @{
    Authorization = "Bearer $adminKey"
    'OpenAI-Organization' = $organizationId
    'Content-Type' = 'application/json'
}

$tunnelPayload = (& $tunnelExe admin tunnels list --organization-id $organizationId --json) | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Falha ao listar túneis da organização.' }
$tunnels = if ($null -ne $tunnelPayload.data) {
    @($tunnelPayload.data)
} elseif ($null -ne $tunnelPayload.tunnels) {
    @($tunnelPayload.tunnels)
} elseif ($null -ne $tunnelPayload.items) {
    @($tunnelPayload.items)
} else {
    @($tunnelPayload)
}
$tunnelIds = @($tunnels | ForEach-Object { if ($_.id) { $_.id } else { $_.tunnel_id } })
if ($freshTunnelId -notin $tunnelIds) {
    $shape = $tunnelPayload.PSObject.Properties.Name -join ','
    throw "O túnel fresh não apareceu na organização; limpeza recusada. Campos=$shape IDs=$($tunnelIds -join ',')"
}

$projectPayload = Invoke-RestMethod -Method Get -Uri 'https://api.openai.com/v1/organization/projects?limit=100' -Headers $headers
$projects = @($projectPayload.data)
if ('proj_fQnH8dj6amRlCEnMJKesnDOz' -notin @($projects | ForEach-Object { $_.id })) {
    throw 'O projeto fresh não apareceu na organização; limpeza recusada.'
}

$keyPayload = Invoke-RestMethod -Method Get -Uri 'https://api.openai.com/v1/organization/admin_api_keys?limit=100' -Headers $headers
$adminKeys = @($keyPayload.data)
if ('key_B6PG7DZr0t4P0qFL' -notin @($adminKeys | ForEach-Object { $_.id })) {
    throw 'A admin key fresh não apareceu na organização; limpeza recusada.'
}

$removed = [ordered]@{
    tunnel = 'already_absent'
    project = 'already_archived_or_absent'
    project_api_keys = 0
    project_service_accounts = 0
    admin_key = 'already_absent'
}

if ($oldTunnelId -in $tunnelIds) {
    & $tunnelExe admin tunnels delete $oldTunnelId --confirm --json | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao excluir o túnel antigo.' }
    $removed.tunnel = 'deleted'
}

$oldProject = $projects | Where-Object id -eq $oldProjectId | Select-Object -First 1
if ($oldProject -and $oldProject.status -ne 'archived') {
    try {
        Invoke-RestMethod -Method Post -Uri "https://api.openai.com/v1/organization/projects/$oldProjectId/archive" -Headers $headers | Out-Null
        $removed.project = 'archived'
    }
    catch {
        if ($_.ErrorDetails.Message -notlike '*project_default*') { throw }

        $serviceAccountPayload = Invoke-RestMethod -Method Get -Uri "https://api.openai.com/v1/organization/projects/$oldProjectId/service_accounts?limit=100" -Headers $headers
        foreach ($serviceAccount in @($serviceAccountPayload.data)) {
            Invoke-RestMethod -Method Delete -Uri "https://api.openai.com/v1/organization/projects/$oldProjectId/service_accounts/$($serviceAccount.id)" -Headers $headers | Out-Null
            $removed.project_service_accounts++
        }

        $apiKeyPayload = Invoke-RestMethod -Method Get -Uri "https://api.openai.com/v1/organization/projects/$oldProjectId/api_keys?limit=100" -Headers $headers
        foreach ($apiKey in @($apiKeyPayload.data)) {
            Invoke-RestMethod -Method Delete -Uri "https://api.openai.com/v1/organization/projects/$oldProjectId/api_keys/$($apiKey.id)" -Headers $headers | Out-Null
            $removed.project_api_keys++
        }

        $renameBody = @{ name = 'Default (system, unused)' } | ConvertTo-Json
        Invoke-RestMethod -Method Post -Uri "https://api.openai.com/v1/organization/projects/$oldProjectId" -Headers $headers -Body $renameBody | Out-Null
        $removed.project = 'default_project_retained_empty'
    }
}

if ($oldAdminKeyId -in @($adminKeys | ForEach-Object { $_.id })) {
    $deleteKeyResponse = Invoke-WebRequest -SkipHttpErrorCheck -Method Delete -Uri "https://api.openai.com/v1/organization/admin_api_keys/$oldAdminKeyId" -Headers $headers
    if ($deleteKeyResponse.StatusCode -ge 200 -and $deleteKeyResponse.StatusCode -lt 300) {
        $removed.admin_key = 'deleted'
    }
    else {
        $refreshedKeyPayload = Invoke-RestMethod -Method Get -Uri 'https://api.openai.com/v1/organization/admin_api_keys?limit=100' -Headers $headers
        $refreshedKeyIds = @($refreshedKeyPayload.data | ForEach-Object { $_.id })
        if ($oldAdminKeyId -in $refreshedKeyIds) {
            $keyMetadata = $refreshedKeyPayload.data | Where-Object id -eq $oldAdminKeyId | Select-Object -First 1
            throw "A chave antiga continua listada, mas a exclusão falhou. status=$($deleteKeyResponse.StatusCode) body=$($deleteKeyResponse.Content) object=$($keyMetadata.object) owner_type=$($keyMetadata.owner.type) owner_id=$($keyMetadata.owner.id) name=$($keyMetadata.name)"
        }
        $removed.admin_key = 'already_absent'
    }
}

$remainingTunnelPayload = (& $tunnelExe admin tunnels list --organization-id $organizationId --json) | ConvertFrom-Json
if ($LASTEXITCODE -ne 0) { throw 'Falha ao verificar os túneis restantes.' }
$remainingTunnels = if ($null -ne $remainingTunnelPayload.data) {
    @($remainingTunnelPayload.data)
} elseif ($null -ne $remainingTunnelPayload.tunnels) {
    @($remainingTunnelPayload.tunnels)
} elseif ($null -ne $remainingTunnelPayload.items) {
    @($remainingTunnelPayload.items)
} else {
    @($remainingTunnelPayload)
}
$remainingTunnelIds = @($remainingTunnels | ForEach-Object { if ($_.id) { $_.id } else { $_.tunnel_id } })

[pscustomobject]@{
    removed = $removed
    fresh_tunnel_present = $freshTunnelId -in $remainingTunnelIds
    old_tunnel_present = $oldTunnelId -in $remainingTunnelIds
} | ConvertTo-Json -Depth 4
