$ErrorActionPreference = "Stop"
$Vault = "C:\Users\delib\Desktop\OMNISVERA"
$Python = Join-Path $Vault ".omnisvera-tools\Scripts\python.exe"
$Bridge = Join-Path $Vault ".local-tools\assistant_bridge.py"
$VaultTools = Join-Path $Vault ".local-tools\vault_tools.py"

Set-Location -LiteralPath $Vault

while ($true) {
    Clear-Host
    Write-Host "OMNISVERA - Assistente Local" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1. Ver estado e handoff"
    Write-Host "2. Buscar no vault"
    Write-Host "3. Perguntar usando arquivos específicos"
    Write-Host "4. Auditar notas"
    Write-Host "5. Criar backup agora"
    Write-Host "0. Sair"
    Write-Host ""
    $choice = Read-Host "Escolha"

    switch ($choice) {
        "1" {
            & $Python $Bridge status
        }
        "2" {
            $query = Read-Host "Busca"
            & $Python $VaultTools search $query --limit 8
        }
        "3" {
            $question = Read-Host "Pergunta"
            Write-Host "Informe caminhos relativos separados por vírgula."
            Write-Host "Exemplo: Workflow/CANON.md, Locations/Fortaleza de Gharok.md"
            $rawFiles = Read-Host "Fontes"
            $args = @($Bridge, "ask", $question)
            foreach ($file in ($rawFiles -split ",")) {
                $trimmed = $file.Trim()
                if ($trimmed) {
                    $args += @("--file", $trimmed)
                }
            }
            & $Python @args
        }
        "4" {
            & $Python $VaultTools audit
        }
        "5" {
            & (Join-Path $Vault ".local-tools\backup.ps1")
        }
        "0" {
            break
        }
        default {
            Write-Host "Opção inválida." -ForegroundColor Yellow
        }
    }

    if ($choice -eq "0") {
        break
    }
    Write-Host ""
    Read-Host "Pressione Enter para continuar"
}
