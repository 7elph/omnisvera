---
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

```dataview
TABLE status, visibility, revealed_in, rumors
FROM "CAMPANHA/Rumors"
WHERE type = "rumor"
SORT file.mtime DESC
```
