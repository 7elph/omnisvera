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
  - quest
---

# Índice de Quests

Índice operacional de ganchos, objetivos e frentes de aventura.

```dataview
TABLE quest_status, visibility, danger_level, hooks
FROM "CAMPANHA/Quests"
WHERE type = "quest"
SORT file.mtime DESC
```
