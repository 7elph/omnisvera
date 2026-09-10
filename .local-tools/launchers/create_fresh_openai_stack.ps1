[CmdletBinding()]
param(
    [string]$OrganizationId = 'org-zxxiNhQsCpmshuH4BvnfqsEz',
    [string]$WorkspaceId = 'a18384f4-bdd9-446b-8e5d-8e4c3fc569af'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')

$root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$tunnelClient = Join-Path $root '.local-tools\bin\tunnel-client-v0.0.13\windows-amd64\tunnel-client.exe'
$statePath = Join-Path $LauncherState 'openai-fresh-stack.json'
$timestamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')

function Invoke-OpenAIAdminJson {
    param(
        [ValidateSet('Get', 'Post', 'Delete')][string]$Method,
        [string]$Path,
        [string]$AdminKey,
        [object]$Body
    )
    $parameters = @{
        Method = $Method
        Uri = "https://api.openai.com$Path"
        Headers = @{ Authorization = "Bearer $AdminKey"; 'Content-Type' = 'application/json' }
        TimeoutSec = 30
    }
    if ($null -ne $Body) { $parameters.Body = $Body | ConvertTo-Json -Depth 8 -Compress }
    return Invoke-RestMethod @parameters
}

if (-not (Test-Path -LiteralPath $tunnelClient -PathType Leaf)) {
    throw "tunnel-client nao encontrado: $tunnelClient"
}
if (Test-Path -LiteralPath $statePath) {
    throw "Estado fresh ja existe em $statePath. Valide ou remova o conjunto anterior antes de criar outro."
}

$bootstrapAdminKey = Get-LauncherSecret 'OPENAI_ADMIN_KEY'
$freshAdminKey = $null
$freshRuntimeKey = $null
try {
    $freshAdmin = Invoke-OpenAIAdminJson -Method Post -Path '/v1/organization/admin_api_keys' `
        -AdminKey $bootstrapAdminKey -Body @{ name = "Omnisvera Fresh Admin $timestamp" }
    if (-not $freshAdmin.value -or -not $freshAdmin.id) { throw 'A API nao retornou a nova admin key completa.' }
    $freshAdminKey = [string]$freshAdmin.value
    $freshAdminSecure = ConvertTo-SecureString $freshAdminKey -AsPlainText -Force
    Set-LauncherSecret 'OPENAI_ADMIN_KEY_FRESH' $freshAdminSecure | Out-Null

    $null = Invoke-OpenAIAdminJson -Method Get -Path "/v1/organization/admin_api_keys/$($freshAdmin.id)" `
        -AdminKey $freshAdminKey -Body $null

    $project = Invoke-OpenAIAdminJson -Method Post -Path '/v1/organization/projects' `
        -AdminKey $freshAdminKey -Body @{ name = "Omnisvera Companion Fresh $timestamp" }
    if (-not $project.id) { throw 'A API nao retornou o projeto novo.' }

    $serviceAccount = Invoke-OpenAIAdminJson -Method Post `
        -Path "/v1/organization/projects/$($project.id)/service_accounts" `
        -AdminKey $freshAdminKey -Body @{ name = 'Omnisvera MCP Runtime' }
    if (-not $serviceAccount.id -or -not $serviceAccount.api_key.value) {
        throw 'A API nao retornou a service account com runtime key.'
    }
    $freshRuntimeKey = [string]$serviceAccount.api_key.value
    $freshRuntimeSecure = ConvertTo-SecureString $freshRuntimeKey -AsPlainText -Force
    Set-LauncherSecret 'CONTROL_PLANE_API_KEY_FRESH' $freshRuntimeSecure | Out-Null

    $env:OPENAI_ADMIN_KEY = $freshAdminKey
    $tunnelOutput = @(& $tunnelClient admin tunnels create `
        --name 'Omnisvera Companion Fresh' `
        --description 'Fresh Secure MCP Tunnel para o Companion Omnisvera no ChatGPT.' `
        --organization-id $OrganizationId `
        --workspace-id $WorkspaceId `
        --json 2>&1)
    $tunnelExitCode = $LASTEXITCODE
    if ($tunnelExitCode -ne 0) {
        $safeDetails = (($tunnelOutput -join [Environment]::NewLine) -replace 'sk-(?:admin-)?[A-Za-z0-9_-]+', '[redacted]')
        throw "Falha ao criar o tunel fresh: $safeDetails"
    }
    $tunnel = ($tunnelOutput -join [Environment]::NewLine) | ConvertFrom-Json
    if (-not $tunnel.id) { throw 'O control plane nao retornou o tunnel_id novo.' }

    $state = [ordered]@{
        created_at = [DateTime]::UtcNow.ToString('o')
        organization_id = $OrganizationId
        workspace_id = $WorkspaceId
        admin_key_id = [string]$freshAdmin.id
        project_id = [string]$project.id
        service_account_id = [string]$serviceAccount.id
        runtime_key_id = [string]$serviceAccount.api_key.id
        tunnel_id = [string]$tunnel.id
        tunnel_name = [string]$tunnel.name
    }
    $state | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $statePath -Encoding UTF8
    $state | ConvertTo-Json -Depth 4
}
finally {
    Remove-Item Env:OPENAI_ADMIN_KEY -ErrorAction SilentlyContinue
    $bootstrapAdminKey = $null
    $freshAdminKey = $null
    $freshRuntimeKey = $null
}
