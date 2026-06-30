---
obsidianUIMode: preview
NoteIcon: rumor
NoteStatus: Draft
type: rumor
status: Rascunho
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
revealed_in:
created_by: Sage
name:
location:
territory:
faction:
danger_level:
rumors: []
hooks: []
chapters: []
thumbnail:
cover:
tags:
  - rumor
---

# Rumor

Resumo curto do rumor em linguagem que pode chegar aos jogadores.

## O que se diz

Versão pública, incompleta ou distorcida do rumor.

## Onde Pode Ser Ouvido

Taverna, mercado, estrada, porto, guilda, templo, guarda, caravana ou outro ponto de circulação.

## Quem sabe

NPCs, facções ou grupos que podem entregar esse rumor.

## Como Investigar

Pistas que levam os jogadores a confirmar, negar ou complicar o rumor.

## Ligação com Quests

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE contains(hooks, this.file.link) OR contains(rumors, this.file.link)
SORT file.name ASC
```

## Uso em Mesa

- Quem pode contar:
- Onde pode ser ouvido:
- Parte verdadeira:
- Parte falsa ou distorcida:
- Como investigar:

## Pendências do Sage

- Completar apenas com a versão que pode circular entre personagens.
- A verdade completa do mestre deve ficar em [[ESTADO_DA_CAMPANHA]].
