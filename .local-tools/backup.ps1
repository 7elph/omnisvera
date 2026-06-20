param(
    [string]$Vault = "C:\Users\delib\Desktop\OMNISVERA",
    [string]$Destination = "$env:USERPROFILE\Documents\OMNISVERA Backups",
    [int]$Keep = 14
)

$ErrorActionPreference = "Stop"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$target = Join-Path $Destination $stamp
New-Item -ItemType Directory -Force -Path $target | Out-Null

git -C $Vault bundle create (Join-Path $target "omnisvera.bundle") --all
git -C $Vault diff --binary HEAD | Set-Content -LiteralPath (Join-Path $target "working-tree.patch") -Encoding utf8
git -C $Vault status --short | Set-Content -LiteralPath (Join-Path $target "status.txt") -Encoding utf8
git -C $Vault log -1 --oneline | Set-Content -LiteralPath (Join-Path $target "head.txt") -Encoding utf8

$untracked = git -C $Vault ls-files --others --exclude-standard
if ($untracked) {
    $staging = Join-Path $target "untracked"
    New-Item -ItemType Directory -Force -Path $staging | Out-Null
    foreach ($relative in $untracked) {
        $source = Join-Path $Vault $relative
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            $dest = Join-Path $staging $relative
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dest) | Out-Null
            Copy-Item -LiteralPath $source -Destination $dest
        }
    }
    Compress-Archive -Path (Join-Path $staging "*") -DestinationPath (Join-Path $target "untracked.zip") -Force
    Remove-Item -LiteralPath $staging -Recurse -Force
}

Get-ChildItem -LiteralPath $Destination -Directory |
    Sort-Object Name -Descending |
    Select-Object -Skip $Keep |
    Remove-Item -Recurse -Force

Write-Output $target
