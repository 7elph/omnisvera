[CmdletBinding()]
param(
    [ValidateSet('OPENCODE_SERVER_PASSWORD', 'CONTROL_PLANE_API_KEY', 'OPENAI_ADMIN_KEY')]
    [string]$Name = 'CONTROL_PLANE_API_KEY',
    [switch]$FromClipboard
)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'runtime_common.ps1')
if ([Environment]::UserName -ne 'delib') { throw 'Execute no usuario Windows delib, nao no ambiente isolado.' }
if ($FromClipboard) {
    $clipboardValue = ([string](Get-Clipboard -Raw)).Trim()
    $expectedPattern = if ($Name -eq 'OPENAI_ADMIN_KEY') { '^sk-admin-[A-Za-z0-9_-]{20,}$' } else { '^sk-[A-Za-z0-9_-]{30,}$' }
    if ($clipboardValue -notmatch $expectedPattern) { throw "O clipboard nao contem uma chave completa valida para $Name. Nenhum arquivo alterado." }
    $secure = ConvertTo-SecureString $clipboardValue -AsPlainText -Force
} else {
    $secure = Read-Host "Informe $Name (entrada oculta, salva com protecao do Windows)" -AsSecureString
}
if ($secure.Length -eq 0) { throw 'Valor vazio; nenhuma credencial foi alterada.' }
New-Item -ItemType Directory -Path $LauncherState -Force | Out-Null
$target = Join-Path $LauncherState "$Name.dpapi"
$temporary = Join-Path $LauncherState "$Name.dpapi.new"
$secure | ConvertFrom-SecureString | Set-Content -LiteralPath $temporary -Encoding ASCII
$decoded = (Get-Content -LiteralPath $temporary -Raw).Trim() | ConvertTo-SecureString -ErrorAction Stop
if ($decoded.Length -ne $secure.Length) { throw 'Falha na verificacao da credencial criptografada.' }
if (Test-Path -LiteralPath $target) { Copy-Item -LiteralPath $target -Destination "$target.previous" -Force }
Move-Item -LiteralPath $temporary -Destination $target -Force
if ($FromClipboard -and ([string](Get-Clipboard -Raw)).Trim() -eq $clipboardValue) {
    # Windows PowerShell 5.1 rejects an empty string in Set-Clipboard.
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.Clipboard]::Clear()
}
$clipboardValue = $null
Write-Host 'Credencial salva para este usuario Windows. Nao foi escrita em log nem no Git.' -ForegroundColor Green
