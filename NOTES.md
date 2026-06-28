---
obsidianUIMode: preview
NoteIcon: notes
NoteStatus: Active
status: Active
tags:
  - home
  - notes
  - workflow
  - omnisvera
---

# Notas de Omnisvera

Ponto de entrada para preparação, decisões de continuidade e material ainda em desenvolvimento.

## Estado da campanha

- [[Workflow/CANON|Cânone de Omnisvera]]
- [[Workflow/ASSISTANT_HANDOFF|Handoff dos Assistentes]]
- [[Workflow/MIGRATION_LEDGER|Registro da Migração]]
- [[Workflow/OUTLINES|Estrutura da Campanha]]
- [[Workflow/Scratch Notes|Notas de Trabalho]]

## Consulta rápida

- [[LATEST_NEWS|Rumores e Descobertas]]
- [[EARTHROPO]]
- [[Workflow/GEOGRAPHY|Registro Geográfico de Earthropo]]
- [[TIMELINE]]
- [[LORE]]
- [[RELIGION|Religiões de Earthropo]]
- [[CULTURE|Cultura de Earthropo]]
- [[ECONOMY|Economia de Earthropo]]

## Material legado

Materiais históricos e arquivos de template ficam fora da navegação operacional do vault.

## Modificado recentemente

```dataview
TABLE WITHOUT ID
link(file.path, file.name) AS "Nota",
file.mtime AS "Modificada"
FROM "/"
WHERE file.name != this.file.name
AND !contains(file.path, "zz_media")
AND !contains(file.path, "Workflow/")
AND !contains(file.path, "Templates/")
AND !contains(file.path, ".obsidian")
AND !contains(file.name, "Legacy -")
SORT file.mtime DESC
LIMIT 15
```
