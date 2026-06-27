---
type: index
status: Rascunho
visibility: Mestre
spoiler_level: heavy
gm_secret: true
created_by: Sage
campaign_status: Em revisao
tags:
  - indice
  - monstro
---

# Índice de Monstros

Índice operacional para monstros, criaturas hostis e ameaças.

```dataview
TABLE status, danger_level, location, thumbnail
FROM "Bestiary"
WHERE type = "monster"
SORT danger_level ASC, file.name ASC
```
