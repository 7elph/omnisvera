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
  - classe
---

# Índice de Classes

Índice operacional para classes, especializações e arquétipos usados em Omnisvera.

```dataview
TABLE status, rules_status, campaign_status, visibility, thumbnail
FROM "Rules/Classes"
WHERE type = "class"
SORT file.name ASC
```
