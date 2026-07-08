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
  - capitulo
chapter: 01 - Ecos do Mundo Perdido
chapter_tag: capitulo01
chapters:
  - 01 - Ecos do Mundo Perdido
date: "1º de Aurora de 2100"
location: "Rota entre [[Nimalis]] e [[Floresta de Avenor]]"
territory: "[[EARTHROPO/EARTHROPO|Earthropo]]"
faction:
  - "[[Guarda Real de Nimalia]]"
  - "[[Conclave dos Errantes]]"
characters:
  - "[[Vezemir]]"
  - "[[Varkh Nimalis]]"
  - "[[Raziel]]"
  - "[[Morthak]]"
cover: "zz_media/covers/banner_ecos_do_mundo_perdido.png"
description: Primeiro capítulo coletivo da campanha, reunindo Vezemir, Varkh, Raziel e Morthak diante dos primeiros sinais de ruínas antigas, remédios falsos e mistérios esquecidos sob Earthropo.
tags:
  - capitulo
  - story
  - capitulo01
  - earthropo
---

# Capítulo 01: Ecos do Mundo Perdido

#### _Crônicas de [[EARTHROPO/EARTHROPO|Earthropo]] — 1º de [[CALENDAR|Aurora]], 2100_

> [!NOTE|clean no-i right]+ 01 - Ecos do Mundo Perdido
> ![[zz_media/covers/banner_ecos_do_mundo_perdido.png|400]]

> [!world]- SINOPSE
> O primeiro capítulo aproxima [[Vezemir]], [[Varkh Nimalis]], [[Raziel]] e [[Morthak]] por meio de um incidente em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]]. Uma caravana aparentemente comum sofre um acidente depois de um tremor localizado, frascos de remédios falsificados se quebram e uma passagem artificial surge sob a terra. O que parecia contrabando comum revela sinais de algo antigo sob Earthropo. Cada personagem encontra ali uma pista íntima: símbolos e sensações ligadas a Avenor para Vezemir, os remédios falsos de Odran para Varkh, marcas de um passado que Raziel reconhece sem compreender totalmente e uma ativação antiga que chama Morthak como se sua não-vida estivesse fora de registro.

## Elenco Principal

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE (
  contains(chapters, this.chapter)
  OR contains(tags, this.chapter_tag)
  OR file.name = "Vezemir"
  OR file.name = "Varkh Nimalis"
  OR file.name = "Raziel"
  OR file.name = "Morthak"
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

---

## Função do Capítulo

Este capítulo serve como o primeiro ponto de convergência entre as histórias de [[Vezemir]], [[Varkh Nimalis]], [[Raziel]] e [[Morthak]].

A função dele não é revelar todo o mundo. É colocar os jogadores diante de sinais concretos de que suas buscas individuais tocam o mesmo problema maior:

- relíquias antigas;
- falsificações alquímicas;
- ruínas esquecidas;
- sinais de ameaças antigas ainda sem explicação;
- histórias que sobreviveram como rumor, medo ou superstição;
- estruturas antigas que ainda funcionam parcialmente sob [[EARTHROPO/EARTHROPO|Earthropo]].

---

## Pontos Sustentados pelo Vault

- [[Vezemir]] busca o dragão de colar dourado e respostas sobre os antigos guardiões ligados à queda de [[Leth'valora]].
- [[Varkh Nimalis]] investiga remédios falsos ligados aos métodos de [[Mestre Odran Veyl]].
- [[Raziel]] despertou após mais de trezentos anos e procura os responsáveis por sua traição.
- [[Morthak]] é um [[Morto-Vivo Esqueleto]] e [[Mago]] atraído pela ativação da [[Unidade DORN-7]].
- [[Nimalia]] é o reino dos antropos, com [[Nimalis]] como capital.
- A [[Floresta de Avenor]] faz fronteira com Nimalia.
- [[Leth'valora]] foi destruída pelo [[Dragão de Colar Dourado]].

---

## Premissa Pública

Rumores recentes falam de tremores na rota entre [[Nimalis]] e a [[Floresta de Avenor]]. Parte do caminho cedeu, uma caravana foi atingida e algo antigo apareceu sob a estrada.

Os relatos ainda são confusos:

- alguns viajantes falam de luz azulada saindo de rachaduras na pedra;
- outros mencionam frascos de remédio falso espalhados entre a carga, com símbolos que lembram o método de [[Mestre Odran Veyl]], mas parecem adulterados;
- há quem jure ter ouvido sons metálicos vindos do subterrâneo;
- a caravana parecia comercial e comum, sem sinal público de missão oficial;
- o [[Conclave dos Errantes]] pode ter interesse no caso.
- uma presença arcana incomum pode ser atraída pela ativação subterrânea sem entender o motivo.

Cada personagem tem uma razão própria para seguir esse rastro.

---

## Estrutura da Sessão

- **Abertura:** estrada entre [[Nimalis]] e [[Floresta de Avenor]], com uma caravana comercial acidentada.
- **Investigação inicial:** frascos quebrados, vítimas assustadas, carga adulterada e marcas que apontam para Odran sem confirmar culpa.
- **Exploração:** a estrada cede e revela uma passagem artificial antiga.
- **Primeiro contato:** a [[Unidade DORN-7]] desperta parcialmente, confusa e danificada, sem explicar o mundo; se detectar [[Morthak]], pode registrá-lo como “morto ativo fora de registro”.
- **Pressão final:** a [[Guarda Real de Nimalia]] chega apenas no fim, tentando isolar a área e controlar testemunhas.
- **Gancho de encerramento:** um mapa fragmentado aponta outro setor enquanto alguém foge com uma prova.

O capítulo deve terminar com impacto e pergunta, não com explicação cosmológica.

---

## Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE quest_status != "Concluída" AND quest_status != "Falhou"
AND type != "index"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND type != "index"
AND gm_secret != true
SORT file.name ASC
```

---

## Uso em Mesa

- **Como apresentar:** começar por uma consequência concreta, não por explicação de lore.
- **O que os jogadores sabem:** há um acidente, uma carga suspeita, uma passagem antiga e interesses conflitantes na estrada.
- **O que fica no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]]:** a verdade completa sobre a estrutura, a entidade subterrânea e as conexões maiores da campanha.
- **Como entra em cena:** por acidente, investigação, contrato, perseguição ou descoberta durante a rota entre Nimalis e a Floresta de Avenor.
- **Entrada de Morthak:** atraído pela ativação de DORN-7, como se a estrutura reconhecesse sua não-vida.
- **Ganchos:** frasco falso, símbolo antigo, sobrevivente assustado, ruína interditada, mapa incompleto, carga adulterada.
- **Consequências possíveis:** os personagens se unem por conveniência, dívida, suspeita ou ameaça compartilhada.

---

## Pós-Sessão

- O que aconteceu:
- O que mudou:
- NPCs afetados:
- Locais afetados:
- Ganchos criados:
