---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Draft
type: race
status: Rascunho
campaign_status: Em revisão
visibility: Mestre
spoiler_level: medium
gm_secret: true
revealed_in:
created_by: Sage

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

## Cultura e Relações

## Mecânica Resumida

Anotações próprias e curtas para uso na campanha.

## Personagens Relacionados

```dataview
TABLE thumbnail, class, status, location, faction
FROM "Characters"
WHERE race = this.file.link OR race = this.file.name
SORT file.name ASC
```

## Ganchos

```dataview
TABLE quest_status, danger_level
FROM "CAMPANHA/Quests"
WHERE contains(rumors, this.file.link) OR contains(hooks, this.file.link)
SORT file.mtime DESC
```

## Uso em Mesa

- Como apresentar:
- O que os jogadores sabem:
- O que apenas o mestre sabe:
- Como entra em cena:
- Ganchos:
- Consequências possíveis:

## Pendências do Sage
