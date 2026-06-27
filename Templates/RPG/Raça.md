---
type: race
status: Rascunho
visibility: Mestre
spoiler_level: medium
gm_secret: true
revealed_in:
created_by: Sage
campaign_status: Em revisao

name:
aliases: []
origin:
territory:
faction: []
religion: []

level:
danger_level:
hooks: []
rumors: []

thumbnail:
cover:
chapters: []

tags:
  - raca
---

# Nome da Raça

## Visão Geral

Resumo próprio, sem reprodução literal de livro.

## Presença em Omnisvera

Onde esta raça aparece, como é vista e quais vínculos culturais existem.

## Mecânica resumida

Anotações próprias e curtas para uso na campanha.

## Ganchos

```dataview
TABLE quest_status, danger_level
FROM "CAMPANHA/Quests"
WHERE contains(rumors, this.file.link) OR contains(hooks, this.file.link)
SORT file.mtime DESC
```
