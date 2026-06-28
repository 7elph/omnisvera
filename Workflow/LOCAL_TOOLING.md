---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Active
tags:
  - workflow
  - tooling
  - local-environment
---

# Omnisvera — Ambiente Local

## Objetivo

Permitir que o Sage rode auditorias locais do vault e use as ferramentas criadas pela IA sem depender de instalação implícita durante uma migração.

## Requisitos mínimos

- Python 3.x;
- PowerShell;
- Git;
- Obsidian;
- Ollama, opcional;
- VS Code, opcional.

## Ferramentas instaladas/preparadas

- **Documentos e Markdown:** Pandoc e MarkItDown.
- **PDF:** Poppler, QPDF, PyMuPDF e pypdf.
- **OCR:** Tesseract com idiomas português e inglês.
- **Imagens e mídia:** ImageMagick, Pillow, FFmpeg e ExifTool.
- **YAML e dados:** yamllint, PyYAML, ruamel.yaml, jq e yq.
- **Busca e arquivos:** ripgrep, fd e 7-Zip.
- **GitHub:** GitHub CLI e Git LFS.

Algumas ferramentas só ficam disponíveis em terminais abertos depois da instalação.

## Ferramentas do repositório

| Caminho | Função |
|---|---|
| `.local-tools/validate_frontmatter.py` | valida frontmatter/YAML das notas |
| `.local-tools/validate_links.py` | valida wikilinks internos |
| `.local-tools/validate_media.py` | valida referências de mídia |
| `.local-tools/vault_audit.py` | auditoria geral do vault |
| `.local-tools/vault_tools.py` | utilitário local de auditoria, índice e busca |
| `.local-tools/backup.ps1` | backup local do vault |
| `.local-tools/bootstrap.ps1` | preparação local do ambiente Python |
| `.local-tools/check_environment.py` | checagem passiva de comandos disponíveis |
| `.local-tools/assistant_bridge.py` | ponte auxiliar para consulta local |
| `.local-tools/assistant_console.ps1` | console auxiliar local |
| `.local-tools/mcp_server.py` | servidor MCP local auxiliar |
| `.ollama/Modelfile.omnisvera-fast` | modelo local rápido |
| `.ollama/Modelfile.omnisvera-local` | modelo local completo |
| `.vscode/extensions.json` | extensões recomendadas para VS Code |

## Como validar

```powershell
python .local-tools/check_environment.py
python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
python .local-tools/vault_audit.py
```

Se o Python do ambiente virtual estiver disponível:

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit --changed
```

## Busca semântica local

O índice ignora mídias, configurações do Obsidian e conteúdo legado quando configurado para isso.

Atualizar o índice:

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py index
```

Pesquisar:

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py search "relação entre Avenor e Nimalia"
```

O índice fica em `.local-index/` e não é enviado ao Git.

## Ollama

Perfis preparados:

- `omnisvera-fast`: extrações curtas e classificação.
- `omnisvera-local`: análise textual local com contexto curto.
- `nomic-embed-text`: busca semântica do vault.

O Ollama é opcional para uso do vault. Ele ajuda a pré-classificar, resumir e buscar material, mas decisões de cânone continuam dependendo do Sage.

## Limitações atuais

- O GitHub CLI pode precisar de `gh auth login` no notebook.
- A busca semântica é auxiliar: resultados precisam ser confrontados com [[CANON]] e com as notas originais.
- Recriar o índice após mudanças narrativas extensas.
- Nenhum script local deve instalar dependências automaticamente sem aprovação.

## Restaurar o assistente

O ambiente Python e o índice são regeneráveis e ficam fora do Git. Para reconstruí-los:

```powershell
powershell -ExecutionPolicy Bypass -File .local-tools\bootstrap.ps1
```

O trecho de configuração do MCP local está em `.local-tools/codex-mcp-snippet.toml`.
