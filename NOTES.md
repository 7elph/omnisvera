---
obsidianUIMode: preview
NoteIcon: notes
NoteStatus: Active
status: Ativo
visibility: gm
tags:
  - home
  - notes
  - workflow
  - omnisvera
---

# Notas de Omnisvera

Ponto de entrada para preparação, decisões de continuidade e material ainda em desenvolvimento.

## Estado da campanha

- [[CANON|Cânone de Omnisvera]]
- [[ASSISTANT_HANDOFF|Handoff dos Assistentes]]
- [[MIGRATION_LEDGER|Registro da Migração]]
- [[OUTLINES|Estrutura da Campanha]]
- [[Scratch Notes|Notas de Trabalho]]

## Consulta rápida

- [[LATEST_NEWS|Rumores e Descobertas]]
- [[EARTHROPO]]
- [[Workflow/GEOGRAPHY|Registro Geográfico de Earthropo]]
- [[TIMELINE]]
- [[LORE]]
- [[RELIGION|Religiões de Earthropo]]
- [[CULTURE|Cultura de Earthropo]]
- [[ECONOMY|Economia de Earthropo]]

## Consolidação

- [[Workflow/CONSOLIDATION_DECISIONS|Decisões respondidas]]
- [[Workflow/TEMPLATES|Templates]]
- [[Workflow/DELETION_REVIEW|Revisão de exclusões]]

## Modificado recentemente

```dataview
TABLE WITHOUT ID
link(file.path, file.name) AS "Nota",
file.mtime AS "Modificada"
FROM "/"
WHERE file.name != this.file.name
AND !contains(file.path, "zz_media")
AND !contains(file.path, ".obsidian")
AND !contains(file.name, "Legacy -")
SORT file.mtime DESC
LIMIT 15
```
