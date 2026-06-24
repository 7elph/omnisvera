---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Ativo
visibility: gm
tags:
  - workflow
  - tooling
  - local-environment
---

# Ferramentas Locais de Omnisvera

Ambiente preparado para análise e manutenção do vault sem alterar seu formato de frontmatter.

## Ferramentas instaladas

- **Documentos e Markdown:** Pandoc e MarkItDown.
- **PDF:** Poppler, QPDF, PyMuPDF e pypdf.
- **OCR:** Tesseract com idiomas português e inglês.
- **Imagens e mídia:** ImageMagick, Pillow, FFmpeg e ExifTool.
- **YAML e dados:** yamllint, PyYAML, ruamel.yaml, jq e yq.
- **Busca e arquivos:** ripgrep, fd e 7-Zip.
- **GitHub:** GitHub CLI e Git LFS. O LFS está instalado, mas nenhum padrão do vault foi migrado automaticamente.

Algumas ferramentas só ficam disponíveis em terminais abertos depois da instalação.

## Auditoria do vault

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit
```

Para verificar apenas notas modificadas:

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit --changed
```

## Busca semântica local

O índice ignora mídias, configurações do Obsidian e arquivos de Disgraceland marcados como legado.

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
- `omnisvera-local`: análise textual local com contexto de 2.048 tokens.
- `nomic-embed-text`: busca semântica do vault.

O Ollama foi configurado para carregar somente um modelo por vez e descarregá-lo após 30 segundos. Modelos maiores já existentes foram preservados, mas não devem ser usados junto com Obsidian e outras aplicações pesadas neste notebook.

## Limitações atuais

- O GitHub CLI está instalado, mas ainda não foi autenticado com `gh auth login`.
- A busca semântica é auxiliar: resultados precisam ser confrontados com [[CANON]] e com as notas originais.
- Recriar o índice após mudanças narrativas extensas.

## Restaurar o assistente

O ambiente Python e o índice são regeneráveis e ficam fora do Git. Para reconstruí-los:

```powershell
powershell -ExecutionPolicy Bypass -File .local-tools\bootstrap.ps1
```

O trecho de configuração do MCP local está em `.local-tools/codex-mcp-snippet.toml`.
