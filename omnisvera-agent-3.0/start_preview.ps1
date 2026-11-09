param(
    [string]$GodotExecutable = $env:OMNISVERA_GODOT_PATH,
    [string]$BackendUrl = 'http://127.0.0.1:8787',
    [int]$Port = 8872,
    [switch]$SkipBuild
)
$ErrorActionPreference = 'Stop'
if (!$GodotExecutable) {
    $portable = Join-Path $env:LOCALAPPDATA 'Omnisvera/tools/Godot-4.7.1/Godot_v4.7.1-stable_win64_console.exe'
    $found = Get-Command godot -ErrorAction SilentlyContinue
    if (Test-Path -LiteralPath $portable) { $GodotExecutable = $portable }
    elseif ($found) { $GodotExecutable = $found.Source }
}
if (!$SkipBuild) {
    if (!$GodotExecutable -or !(Test-Path -LiteralPath $GodotExecutable)) {
        throw 'Informe -GodotExecutable com o Godot e seus templates Web correspondentes.'
    }
    New-Item -ItemType Directory -Path (Join-Path $PSScriptRoot 'build/web') -Force | Out-Null
    & $GodotExecutable --headless --path $PSScriptRoot --editor --import --quit
    if ($LASTEXITCODE -ne 0) { throw 'Falha na importação do projeto' }
    & $GodotExecutable --headless --path $PSScriptRoot --export-release Web (Join-Path $PSScriptRoot 'build/web/index.html')
    if ($LASTEXITCODE -ne 0) { throw 'Falha na exportação Web' }
}
$companion = Join-Path (Split-Path $PSScriptRoot -Parent) 'omnisvera-agent'
$python = Join-Path $companion '.venv-observer/Scripts/python.exe'
if (!(Test-Path -LiteralPath $python)) {
    $python = (Get-Command python -ErrorAction Stop).Source
}
& $python (Join-Path $PSScriptRoot 'tools/serve_preview.py') --backend $BackendUrl --port $Port
exit $LASTEXITCODE
