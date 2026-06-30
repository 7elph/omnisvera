---
obsidianUIMode: preview
NoteIcon: rumor
NoteStatus: Draft
type: index
status: Rascunho
visibility: Mestre
spoiler_level: medium
gm_secret: true
created_by: Sage
campaign_status: Em revisao
tags:
  - indice
  - rumor
---

# Índice de Rumores

Índice operacional de rumores, pistas soltas e informações que podem chegar aos jogadores.

## Rumores Liberados

```dataview
TABLE status, visibility, revealed_in, rumors
FROM "CAMPANHA/Rumors"
WHERE type = "rumor"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.mtime DESC
```

## Rumores do Mestre

```dataview
TABLE status, visibility, revealed_in, rumors
FROM "CAMPANHA/Rumors"
WHERE type = "rumor"
SORT file.mtime DESC
```

## Regra de Uso

- Rumores podem ser parcialmente falsos.
- O texto público deve ser seguro para jogadores.
- A verdade completa, se existir, fica no [[ESTADO_DA_CAMPANHA]] ou em nota de mestre.
