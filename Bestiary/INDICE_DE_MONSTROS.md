---
obsidianUIMode: preview
NoteIcon: monster
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
  - monstro
---

# Índice de Monstros

Índice operacional para monstros, criaturas hostis e ameaças.

## Monstros Liberados

```dataview
TABLE status, danger_level, location, thumbnail
FROM "Bestiary"
WHERE type = "monster"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT danger_level ASC, file.name ASC
```

## Monstros do Mestre

```dataview
TABLE status, danger_level, location, spoiler_level
FROM "Bestiary"
WHERE type = "monster"
AND visibility = "Mestre"
SORT danger_level ASC, file.name ASC
```

## Regra de Uso

- `Bestiary/` é a pasta oficial para monstros, criaturas hostis e ameaças.
- Não criar monstro em lote apenas por completismo.
- Criar nota quando a criatura for aparecer em mesa, rumor, capítulo ou lore ativa.
- Não copiar blocos completos de livros; usar resumo próprio, referência interna e decisões do Sage.
