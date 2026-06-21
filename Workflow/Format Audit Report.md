---
obsidianUIMode: preview
NoteIcon: audit
NoteStatus: Active
status: Atualizado
tags:
  - workflow
  - audit
  - report
  - omnisvera
---

# Relatório de Auditoria

_Atualizado em 21 de junho de 2026._

## Resultado atual

- **Notas ativas verificadas:** 83
- **Erros de YAML:** 0
- **Arquivos vazios:** 0
- **Wikilinks ativos ainda sem nota:** 0

## Wikilinks pendentes

Nenhum wikilink ativo sem destino foi encontrado. Referências legadas são excluídas desta contagem.

## Escopo

O relatório exclui:

- arquivos de mídia;
- configurações internas do Obsidian;
- ambientes e índices locais;
- notas cujo nome começa com `Legacy -`.

## Comando de verificação

```powershell
.omnisvera-tools\Scripts\python.exe .local-tools\vault_tools.py audit
```

Este relatório não exige que todo campo vazio seja preenchido. Placeholders deliberados continuam válidos quando registrados em [[MIGRATION_LEDGER]].
