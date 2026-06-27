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
  - magia
---

# Índice de Magias

Este índice organiza magias por uso de campanha.

Não reproduzir texto integral de livros ou materiais protegidos. Cada nota de magia deve conter apenas estrutura própria, resumo original e campos de controle.

```dataview
TABLE level, status, campaign_status, danger_level
FROM "Rules/Spells"
WHERE type = "spell"
SORT level ASC, file.name ASC
```
