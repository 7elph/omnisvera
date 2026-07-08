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
name: Caravana Acidentada na Estrada de Avenor
location: "Rota entre [[Nimalis]] e [[Floresta de Avenor]]"
territory: "[[Nimalia]]"
faction:
danger_level: C
rumors:
  - "[[03 - Explorar a Passagem Sob a Estrada]]"
hooks:
  - "[[03 - Explorar a Passagem Sob a Estrada]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/locations/estrada_antiga.png
cover: zz_media/covers/banner_ecos_do_mundo_perdido.png
tags:
  - rumor
  - story
  - capitulo01
  - nimalia
  - avenor
---

# 03 — Caravana Acidentada na Estrada de Avenor

Uma caravana comercial sofreu um acidente em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]].

## O que se diz

Dizem que a estrada cedeu de repente, que uma carroça tombou e que luz azulada apareceu por baixo da terra.

Alguns juram ter ouvido sons metálicos. Outros dizem que era apenas medo de viajante.

## Onde Pode Ser Ouvido

- estrada;
- tavernas próximas a rotas comerciais;
- Mercado Central de [[Nimalis]];
- mercadores;
- guardas de passagem.

## Quem sabe

- sobreviventes da caravana;
- comerciantes de estrada;
- viajantes que passaram pela rota;
- gente que quer evitar problemas com a Guarda.

## Como Investigar

Ir até a estrada, conversar com sobreviventes, examinar a carga e observar o que apareceu sob o caminho.

## Ligação com Quests

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE (contains(hooks, this.file.link) OR contains(rumors, this.file.link))
AND type != "index"
SORT file.name ASC
```

## Uso em Mesa

- Quem pode contar: mercador, carroceiro, guarda ou viajante nervoso.
- Onde pode ser ouvido: estrada, taverna, mercado ou entrada de Nimalis.
- Parte verdadeira: houve acidente e algo antigo apareceu sob a estrada.
- Parte falsa ou distorcida: ninguém sabe ainda se foi magia, monstro, armadilha ou azar.
- Como investigar: visitar o local antes que a Guarda isole tudo.
