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
name: Dragões ao Sul de Nimalia
location:
territory: "[[Nimalia]]"
faction: "[[Conclave dos Errantes]]"
danger_level: Médio
rumors:
  - "[[Quest 01 - Investigar Avistamentos de Dragões]]"
hooks:
  - "[[Quest 01 - Investigar Avistamentos de Dragões]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail:
cover:
tags:
  - rumor
  - story
  - chapter01
  - conclave-dos-errantes
---

# Rumor 01 — Dragões ao Sul de Nimalia

O [[Conclave dos Errantes]] ouviu relatos sobre ataques atribuídos a dragões nas regiões ao sul de [[Nimalia]].

Qualquer informação mais confiável provavelmente exigiria visitar a região, conversar com testemunhas e separar medo de fato.

## O que se diz

Há rumores de que dragões estariam atacando vilarejos, roubando gado e até enfrentando monstros por aquela região.

## Onde Pode Ser Ouvido

- tavernas;
- estradas próximas a [[Nimalis]];
- caravanas;
- contatos do [[Conclave dos Errantes]];
- mercadores assustados.

## Quem sabe

- [[Conclave dos Errantes]]
- viajantes recentes;
- mercadores que evitam a rota sul;
- moradores de vilas afetadas, se os relatos forem confirmados.

## Como Investigar

- Comparar relatos de testemunhas diferentes.
- Verificar marcas de ataque, pegadas, cinzas, gado morto ou destroços.
- Descobrir se os ataques realmente vieram de dragões ou se o nome está sendo usado para aumentar o medo.
- Procurar ligação com outras pistas dracônicas, como [[Dragão de Colar Dourado]].

## Ligação com Quests

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE contains(hooks, this.file.link) OR contains(rumors, this.file.link)
SORT file.name ASC
```

## Uso em Mesa

- Quem pode contar: mercador, batedor, membro do Conclave ou viajante ferido.
- Onde pode ser ouvido: Nimalis, estrada, mercado ou taverna.
- Parte verdadeira: há ataques ou desaparecimentos em rotas ao sul.
- Parte falsa ou distorcida: ainda não está confirmado que sejam dragões.
- Como investigar: viajar até a região, ouvir testemunhas e procurar rastros físicos.

## Pendências do Sage

- Confirmar se este rumor entra já no Capítulo 01.
- Definir se os ataques são reais, exagerados ou fabricados.
- Definir se há relação com o [[Dragão de Colar Dourado]].
