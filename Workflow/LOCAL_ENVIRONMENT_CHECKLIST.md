# Omnisvera — Checklist do Notebook do Sage

Fonte relacionada: [[LOCAL_TOOLING]]

## Objetivo

Registrar o que o notebook precisa ter disponível para manter o vault, rodar auditorias e usar as ferramentas locais criadas pela IA.

## Checklist

| Item | Instalado? | Como verificar | Observações |
|---|---|---|---|
| Python | [ ] | `python --version` | obrigatório para validadores locais |
| Git | [ ] | `git --version` | obrigatório para versionamento |
| PowerShell | [ ] | `$PSVersionTable` | obrigatório no Windows |
| Obsidian | [ ] | verificação manual | obrigatório para uso do vault |
| Ollama | [ ] | `ollama --version` | opcional; útil para IA local |
| VS Code | [ ] | `code --version` | opcional; útil para edição técnica |
| GitHub CLI | [ ] | `gh --version` | opcional; útil para PRs e autenticação |
| Git LFS | [ ] | `git lfs version` | recomendado para mídia grande |
| Tesseract | [ ] | `tesseract --version` | opcional; OCR |
| ImageMagick | [ ] | `magick --version` | opcional; tratamento de imagem |
| FFmpeg | [ ] | `ffmpeg -version` | opcional; áudio/vídeo |
| ExifTool | [ ] | `exiftool -ver` | opcional; metadados de mídia |
| jq | [ ] | `jq --version` | opcional; JSON |
| yq | [ ] | `yq --version` | opcional; YAML |
| ripgrep | [ ] | `rg --version` | recomendado para buscas rápidas |

## Checagem automática passiva

```powershell
python .local-tools/check_environment.py
```

Esse script apenas verifica disponibilidade de comandos. Ele não instala, remove ou configura nada.

## Validação do vault

```powershell
python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
python .local-tools/vault_audit.py
```

## Critério mínimo antes de migração grande

- Git funcionando.
- Python funcionando.
- Obsidian abrindo o vault.
- Validadores locais rodando ou falhando de forma documentada.
- Backup local ou commit limpo antes de mudanças em lote.
