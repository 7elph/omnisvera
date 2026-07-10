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
name: Remédios Falsos da Maré Baixa
location: 
territory: Nimalia
faction: 
danger_level: D
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/thumbnails/th_remedios_falsos.PNG
cover: zz_media/misc/remedios_falsos.png
tags:
  - rumor
  - story
  - capitulo01
  - conclave-dos-errantes

---

# 02 - Remédios Falsos da Maré Baixa

Remédios falsos circulam em Nimalia usando o símbolo e os métodos de [[Mestre Odran Veyl|Odran]]. Pessoas compram cura e recebem veneno. Documentos falsificados surgem com assinaturas perfeitas demais. Guardas procuram por “um corvo alquimista”.

## O que se diz

Remédios falsos começaram a circular em Nimalia nos últimos meses.
- Os remédios falsos usam uma versão adulterada do símbolo antigo de Odran.
- Pessoas compram cura e recebem veneno.

## Onde Pode Ser Ouvido

- tavernas;
- [[Conclave dos Errantes]];
- mercadores.

## Quem sabe

- vítimas envenenadas;
- [[Conclave dos Errantes]];
- a guarda procurando o "corvo alquimista".


## Ligação com Quests

```datacards
TABLE cover, quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE (contains(hooks, this.file.link) OR contains(rumors, this.file.link))
AND type != "index"
SORT file.name ASC
```
