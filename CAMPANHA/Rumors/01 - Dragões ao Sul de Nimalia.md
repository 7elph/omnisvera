---
obsidianUIMode: preview
NoteIcon: rumor
NoteStatus:
type: rumor
status: Completo
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
revealed_in:
created_by: Sage
name: Dragões ao Sul de Nimalia
location: Sul de Nimalia
territory: "[[Nimalia]]"
faction: "[[Conclave dos Errantes]]"
danger_level: C
info: O Conclave dos Errantes ouviu relatos sobre ataques atribuídos a dragões nas regiões ao sul de Nimalia.
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/thumbnails/th_retrato_avistamento.PNG
cover: zz_media/covers/cover_o_dragao_da_missao.png
tags:
  - rumor
  - story
  - capitulo01
  - conclave-dos-errantes

---

#  01 — Dragões ao Sul de Nimalia

O [[Conclave dos Errantes]] ouviu relatos sobre ataques atribuídos a dragões nas regiões ao sul de [[Nimalia]].

Qualquer informação mais confiável provavelmente exigiria visitar a região, conversar com testemunhas e separar medo de fato.

## O que se diz

Há rumores de que dragões estariam atacando vilarejos, roubando gado e até enfrentando monstros por aquela região.

## Onde Pode Ser Ouvido

- tavernas;
- estradas próximas a [[Nimalis]];
- caravanas;
- [[Conclave dos Errantes]];
- mercadores.

## Quem sabe

- [[Conclave dos Errantes]]
- viajantes recentes;
- mercadores que evitam a rota sul;
- moradores de vilas afetadas.

## Ligação com Quests

```datacards
TABLE cover, quest_status, danger_level, location, faction
FROM "CAMPANHA/Quests"
WHERE name = "Investigar Avistamentos de Dragões"
AND type != "index"
SORT file.name ASC
```
