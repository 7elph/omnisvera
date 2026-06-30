---
obsidianUIMode: preview
NoteIcon: story
NoteStatus: Active
type: story
status: Em Preparação
campaign_status: Em Andamento
visibility: Jogadores
spoiler_level: light
gm_secret: false
cssclasses:
  - b-sides-script
  - chapter
chapter: 01 - Ecos do Mundo Perdido
chapters:
  - 01 - Ecos do Mundo Perdido
date:
location: "Rota entre [[Nimalis]] e [[Floresta de Avenor]]"
territory: "[[EARTHROPO/EARTHROPO|Earthropo]]"
faction:
  - "[[Guarda Real de Nimalia]]"
  - "[[Conclave dos Errantes]]"
characters:
  - "[[Vezemir]]"
  - "[[Varkh Nimalis]]"
  - "[[Raziel]]"
cover: "[[zz_media/banner-ecos-do-mundo-perdido.png]]"
description: Primeiro capítulo coletivo da campanha, reunindo Vezemir, Varkh e Raziel diante dos primeiros sinais de ruínas antigas, remédios falsos e mistérios esquecidos sob Earthropo.
tags:
  - chapter
  - story
  - chapter01
  - earthropo
---

# Capítulo 01: Ecos do Mundo Perdido

#### _Crônicas de [[EARTHROPO/EARTHROPO|Earthropo]] — capítulo em preparação_

> [!NOTE|clean no-i right]+ 01 - Ecos do Mundo Perdido
> ![[banner-ecos-do-mundo-perdido.png|400]]

> [!world]- SINOPSE
> O primeiro capítulo aproxima [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]]. Uma caravana sofre um acidente depois de um tremor localizado, frascos de remédios falsificados se quebram e uma passagem artificial surge sob a terra. O que parecia contrabando comum revela sinais de algo antigo sob Earthropo. Cada personagem encontra ali uma pista íntima: o dragão e os Guardiões para Vezemir, os remédios falsos de Odran para Varkh, e marcas de um passado que Raziel reconhece sem compreender totalmente.

## Elenco Principal

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE contains(chapters, "01 - Ecos do Mundo Perdido")
OR contains(tags, "chapter01")
OR file.name = "Vezemir"
OR file.name = "Varkh Nimalis"
OR file.name = "Raziel"
SORT file.name ASC

// Settings
preset: compact
columns: 5
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

---

## Função do Capítulo

Este capítulo serve como o primeiro ponto de convergência entre as histórias de [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]].

A função dele não é revelar todo o mundo. É colocar os jogadores diante de sinais concretos de que suas buscas individuais tocam o mesmo problema maior:

- relíquias antigas;
- falsificações alquímicas;
- ruínas esquecidas;
- marcas do [[Véu Cinzento]];
- histórias que sobreviveram como rumor, medo ou superstição;
- estruturas antigas que ainda funcionam parcialmente sob [[EARTHROPO/EARTHROPO|Earthropo]].

---

## Pontos Sustentados pelo Vault

- [[Vezemir]] busca o dragão de colar dourado e respostas sobre os [[Guardiões do Véu Cinzento]].
- [[Varkh Nimalis]] investiga remédios falsos ligados aos métodos de [[Mestre Odran Veyl]].
- [[Raziel]] despertou após mais de trezentos anos e procura os responsáveis por sua traição.
- [[Nimalia]] é o reino dos antropos, com [[Nimalis]] como capital.
- A [[Floresta de Avenor]] faz fronteira com Nimalia.
- [[Leth'valora]] foi destruída pelo [[Dragão de Colar Dourado]].

---

## Premissa Pública

Rumores recentes falam de tremores na rota entre [[Nimalis]] e a [[Floresta de Avenor]]. Parte do caminho cedeu, uma caravana foi atingida e algo antigo apareceu sob a estrada.

Os relatos ainda são confusos:

- alguns viajantes falam de luz azulada saindo de rachaduras na pedra;
- outros mencionam frascos de remédio falso espalhados entre a carga;
- há quem jure ter ouvido sons metálicos vindos do subterrâneo;
- a [[Guarda Real de Nimalia]] começou a afastar curiosos;
- o [[Conclave dos Errantes]] pode ter interesse no caso.

Cada personagem tem uma razão própria para seguir esse rastro.

---

## Possíveis Pontos de Encontro

> [!note]
> Escolher apenas um quando a sessão for preparada. Não canonizar todos ao mesmo tempo.

- Uma rota entre [[Nimalis]] e a [[Floresta de Avenor]].
- Uma investigação sobre remédios falsos que chega perto de território ligado ao Véu.
- Uma ruína menor conectada indiretamente às [[Ruínas de Valthor]].
- Um pedido do [[Conclave dos Errantes]] envolvendo uma relíquia ou escolta.
- Um rumor vindo do [[Mar da Neblina]] que cruza com documentos da Coroa.

---

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
WHERE visibility = "Jogadores" OR visibility = "Público"
AND gm_secret != true
SORT file.name ASC
```

---

## Uso em Mesa

- **Como apresentar:** começar por uma consequência concreta, não por explicação de lore.
- **O que os jogadores sabem:** há um acidente, uma carga suspeita, uma passagem antiga e interesses conflitantes na estrada.
- **O que fica no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]]:** a verdade completa sobre a estrutura, a entidade subterrânea e as conexões maiores da campanha.
- **Como entra em cena:** por acidente, investigação, contrato, perseguição ou descoberta durante a rota entre Nimalis e a Floresta de Avenor.
- **Ganchos:** frasco falso, símbolo antigo, sobrevivente assustado, ruína interditada, mapa incompleto, carga adulterada.
- **Consequências possíveis:** os personagens se unem por conveniência, dívida, suspeita ou ameaça compartilhada.

---

## Pós-Sessão

- O que aconteceu:
- O que mudou:
- NPCs afetados:
- Locais afetados:
- Ganchos criados:
