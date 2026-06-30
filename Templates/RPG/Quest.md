---
obsidianUIMode: preview
NoteIcon: quest
NoteStatus: Draft
type: quest
status: Rascunho
quest_status: Aberta
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
revealed_in:
created_by: Sage
name:
location:
territory:
faction: []
danger_level:
hooks: []
rumors: []
chapters: []
thumbnail:
cover:
tags:
  - quest
---

# Nome da Quest

## Gancho Público

O que os personagens ouvem, veem ou recebem como chamado inicial.

## Objetivo Conhecido

O que parece ser o objetivo da quest do ponto de vista dos jogadores.

## Locais Relacionados

## Envolvidos Conhecidos

## Pistas Públicas

## Rumores Relacionados

```dataview
TABLE status, visibility, location
FROM "CAMPANHA/Rumors"
WHERE contains(hooks, this.file.link) OR contains(rumors, this.file.link)
SORT file.name ASC
```

## Estado

## Uso em Mesa

- Como os jogadores descobrem:
- Objetivo claro:
- Complicação:
- Recompensa:
- Consequência se ignorada:

## Pendências do Sage

- Completar apenas com informações que podem aparecer para jogadores.
- Bastidores, verdades secretas e consequências ocultas devem ficar em [[ESTADO_DA_CAMPANHA]].
