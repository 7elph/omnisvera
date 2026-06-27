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
  - item
---

# Índice de Itens

Índice operacional para itens, artefatos, tesouros e objetos importantes.

```dataview
TABLE status, campaign_status, visibility, thumbnail
FROM "Items"
WHERE type = "item"
SORT file.name ASC
```
