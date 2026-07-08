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
name: A Guarda Real Está Fechando Rotas
location: "[[Nimalis]]"
territory: "[[Nimalia]]"
faction: "[[Guarda Real de Nimalia]]"
danger_level: D
rumors:
  - "[[03 - Explorar a Passagem Sob a Estrada]]"
hooks:
  - "[[03 - Explorar a Passagem Sob a Estrada]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/faction/guarda_real_nimalia.png
cover: zz_media/faction/guarda_real_nimalia.png
tags:
  - rumor
  - story
  - capitulo01
  - guarda-real
  - nimalia
---

# 05 — A Guarda Real Está Fechando Rotas

Viajantes comentam que patrulhas da [[Guarda Real de Nimalia]] estão mais rígidas nas saídas de [[Nimalis]] e em trechos de estrada próximos à [[Floresta de Avenor]].

## O que se diz

Dizem que a Guarda está procurando contrabando, monstros ou alguém específico. Ninguém concorda sobre o motivo.

## Onde Pode Ser Ouvido

- portões de [[Nimalis]];
- estradas comerciais;
- taverna de viajantes;
- carroceiros e mercadores.

## Quem sabe

- guardas de patrulha;
- mercadores parados em barreiras;
- viajantes impedidos de seguir viagem;
- contatos da [[Guilda dos Mercadores]].

## Como Investigar

Observar patrulhas, falar com mercadores retidos e descobrir quais cargas estão sendo revistadas com mais cuidado.

## Ligação com Quests

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE (contains(hooks, this.file.link) OR contains(rumors, this.file.link))
AND type != "index"
SORT file.name ASC
```

## Uso em Mesa

- Quem pode contar: mercador irritado, guarda cansado ou viajante barrado.
- Onde pode ser ouvido: portão, estrada, mercado ou taverna.
- Parte verdadeira: patrulhas estão mais atentas.
- Parte falsa ou distorcida: ninguém sabe publicamente se há ordem especial da Coroa.
- Como investigar: seguir a movimentação da Guarda e comparar quais rotas recebem mais atenção.
