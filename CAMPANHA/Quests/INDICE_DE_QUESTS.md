---
obsidianUIMode: preview
NoteIcon: quest
NoteStatus: Draft
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

## Quests Liberadas

```dataview
TABLE quest_status, visibility, danger_level, hooks
FROM "CAMPANHA/Quests"
WHERE type = "quest"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.mtime DESC
```

## Quests do Mestre

```dataview
TABLE quest_status, visibility, danger_level, hooks
FROM "CAMPANHA/Quests"
WHERE type = "quest"
SORT file.mtime DESC
```

## Regra de Uso

- Quests públicas precisam ter `visibility: Jogadores` ou `visibility: Público`.
- Verdades ocultas, causas reais e consequências secretas ficam no [[ESTADO_DA_CAMPANHA]].
- Quests concluídas ou falhas não precisam desaparecer; devem mudar `quest_status`.
