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
  - raca
---

# Índice de Raças

Índice operacional para raças permitidas, restritas ou em revisão em Omnisvera.

```dataview
TABLE status, campaign_status, visibility, thumbnail
FROM "Rules/Races"
WHERE type = "race"
SORT file.name ASC
```
