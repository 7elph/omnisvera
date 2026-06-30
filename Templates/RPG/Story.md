---
obsidianUIMode: preview
NoteIcon: story
NoteStatus: New
type: story
visibility: Jogadores
spoiler_level: light
gm_secret: false
status: Planejado
campaign_status: Planejado
cssclasses:
  - b-sides-script
  - capitulo
chapter:
chapter_tag:
chapters:
date:
location:
territory:
faction:
characters:
items:
quests:
rumors:
cover:
description:
created_by:
tags:
  - story
  - capitulo
---

# Capítulo XX: Nome

#### _Crônicas de [[EARTHROPO/EARTHROPO|Earthropo]] — capítulo em preparação_

> [!important]
> Esta nota representa a versão pública/operacional do capítulo. Bastidores completos, spoilers pesados e decisões internas do mestre devem ficar em [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]].

> [!NOTE|clean no-i right]+ Nome do Capítulo
> ![[zz_media/banner-earthropo.png|400]]

> [!world]- SINOPSE
> Escreva aqui a sinopse curta do capítulo, com foco no que a nota precisa comunicar em consulta rápida.

## Elenco Principal

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE (
  contains(chapters, this.chapter)
  OR contains(tags, this.chapter_tag)
)
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT file.name ASC

// Settings
preset: compact
columns: 5
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## Estado do Capítulo

- Status:
- Data prevista:
- Local principal:
- Personagens em foco:
- Facções em movimento:

## Função do Capítulo

Explique o papel deste capítulo na campanha.

## Recapitulação

## Cena de Abertura

## Objetivo da Sessão

## Personagens Importantes

## Locais Importantes

## Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE quest_status != "Concluída" AND quest_status != "Falhou"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT file.name ASC
```

## Possíveis Consequências

## Pós-Sessão

- O que aconteceu:
- O que mudou:
- NPCs afetados:
- Locais afetados:
- Ganchos criados:

## Uso em Mesa

- Como apresentar:
- O que os jogadores sabem:
- O que fica no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]]:
- Como entra em cena:
- Ganchos:
- Consequências possíveis:
