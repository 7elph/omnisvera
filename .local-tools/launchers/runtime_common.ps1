$LauncherRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
$LauncherState = Join-Path $LauncherRoot '.assistant-runtime\launchers'
$AllowedLauncherSecrets = @(
    'OPENCODE_SERVER_PASSWORD',
    'ROUTER9_API_KEY',
    'CONTROL_PLANE_API_KEY',
    'CONTROL_PLANE_API_KEY_FRESH',
    'OPENAI_ADMIN_KEY',
    'OPENAI_ADMIN_KEY_FRESH'
)

function Test-LocalPort([int]$Port) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $pending = $client.BeginConnect('127.0.0.1', $Port, $null, $null)
        if (-not $pending.AsyncWaitHandle.WaitOne(1000, $false)) { return $false }
        $client.EndConnect($pending)
        return $true
    }
    catch { return $false }
    finally { $client.Dispose() }
}

function Wait-LocalPort([int]$Port, [int]$Seconds = 30) {
    $deadline = [DateTime]::UtcNow.AddSeconds($Seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if (Test-LocalPort $Port) { return }
        Start-Sleep -Milliseconds 500
    }
    throw "Servico nao abriu a porta $Port."
}

function Get-LauncherSecret([string]$Name, [switch]$Optional) {
    if ($Name -notin $AllowedLauncherSecrets) {
        throw 'Credencial nao permitida.'
    }
    $path = Join-Path $LauncherState "$Name.dpapi"
    $secure = $null
    if (Test-Path -LiteralPath $path) {
        try { $secure = (Get-Content -LiteralPath $path -Raw).Trim() | ConvertTo-SecureString -ErrorAction Stop }
        catch { Write-Verbose 'Credencial de outro contexto Windows; tentando ambiente autorizado deste usuario.' }
    }
    if (-not $secure) {
        $value = [Environment]::GetEnvironmentVariable($Name, 'User')
        if (-not $value) { $value = [Environment]::GetEnvironmentVariable($Name, 'Process') }
        if (-not $value) {
            if ($Optional) { return $null }
            throw "Configure $Name uma vez com setup_credentials.ps1. Nao cole a chave no chat."
        }
        $secure = ConvertTo-SecureString $value -AsPlainText -Force
        New-Item -ItemType Directory -Path $LauncherState -Force | Out-Null
        $secure | ConvertFrom-SecureString | Set-Content -LiteralPath $path -Encoding ASCII
    }
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
}

function Set-LauncherSecret([string]$Name, [SecureString]$SecureValue) {
    if ($Name -notin $AllowedLauncherSecrets) { throw 'Credencial nao permitida.' }
    if (-not $SecureValue -or $SecureValue.Length -eq 0) { throw 'Credencial vazia.' }
    New-Item -ItemType Directory -Path $LauncherState -Force | Out-Null
    $target = Join-Path $LauncherState "$Name.dpapi"
    $temporary = Join-Path $LauncherState "$Name.dpapi.new"
    $SecureValue | ConvertFrom-SecureString | Set-Content -LiteralPath $temporary -Encoding ASCII
    $decoded = (Get-Content -LiteralPath $temporary -Raw).Trim() | ConvertTo-SecureString -ErrorAction Stop
    if ($decoded.Length -ne $SecureValue.Length) { throw 'Falha na verificacao da credencial criptografada.' }
    if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination "$target.previous" -Force }
    Move-Item -LiteralPath $temporary -Destination $target -Force
    return $target
}

function Enable-PrivateTailnetService([int]$Port) {
    $tailscale = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
    if (-not (Test-Path -LiteralPath $tailscale)) { throw 'Tailscale nao esta instalado.' }
    if ((Get-Service Tailscale).Status -ne 'Running') { Start-Service Tailscale }
    $raw = & $tailscale status --json
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel consultar o Tailscale.' }
    $status = $raw | ConvertFrom-Json
    if ($status.BackendState -eq 'Stopped') {
        & $tailscale up --timeout=15s | Out-Host
        if ($LASTEXITCODE -ne 0) { throw 'Tailscale nao conectou; confira o login.' }
        $raw = & $tailscale status --json
        if ($LASTEXITCODE -ne 0) { throw 'Tailscale nao respondeu apos conectar.' }
        $status = $raw | ConvertFrom-Json
    }
    if ($status.BackendState -ne 'Running') { throw "Tailscale: $($status.BackendState). Confira o login." }
    New-Item -ItemType Directory -Path $LauncherState -Force | Out-Null
    $log = Join-Path $LauncherState ("serve-{0}-{1}" -f $Port, [Guid]::NewGuid().ToString('N'))
    $process = Start-Process -FilePath $tailscale -ArgumentList @(
        'serve', '--bg', '--yes', "--https=$Port", "http://127.0.0.1:$Port"
    ) -WindowStyle Hidden -PassThru -RedirectStandardOutput "$log.out" -RedirectStandardError "$log.err"
    $null = $process.Handle
    if (-not $process.WaitForExit(20000)) {
        $process.Kill()
        throw "Tailscale Serve aguarda autorizacao. Consulte $log.out"
    }
    $process.Refresh()
    if ($process.ExitCode -ne 0) { throw "Tailscale Serve falhou. Consulte $log.err" }
    $dns = ([string]$status.Self.DNSName).TrimEnd('.')
    if (-not $dns) { throw 'Tailscale nao informou o DNS da maquina.' }
    return ('https://{0}:{1}' -f $dns, $Port)
}
