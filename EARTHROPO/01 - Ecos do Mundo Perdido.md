---
obsidianUIMode: preview
NoteIcon: story
NoteStatus: Draft
type: story
status: Planejado
campaign_status: Planejado
visibility: Mestre
spoiler_level: heavy
gm_secret: true
cssclasses:
  - b-sides-script
  - chapter
chapter: 01 - Ecos do Mundo Perdido
chapters:
  - 01 - Ecos do Mundo Perdido
date:
location:
territory: Earthropo
faction:
characters:
  - "[[Vezemir]]"
  - "[[Varkh Nimalis]]"
  - "[[Raziel]]"
cover: "[[zz_media/banner-ecos-do-mundo-perdido.png]]"
description: Primeiro arco coletivo planejado para reunir Vezemir, Varkh e Raziel diante dos primeiros sinais do Véu, das relíquias antigas e dos segredos perdidos de Earthropo.
tags:
  - chapter
  - story
  - chapter01
  - earthropo
---

# Capítulo 01

#### _Crônicas de Earthropo_

## Ecos do Mundo Perdido

> [!warning] Capítulo ainda não jogado
> Esta nota reserva o lugar do primeiro arco coletivo. As ideias abaixo são estrutura de preparação, não acontecimentos confirmados em mesa.

## Função do Capítulo

Este capítulo deve servir como o primeiro ponto de convergência entre as histórias de [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]].

A função dele não é revelar todo o mundo, e sim colocar os jogadores diante de sinais concretos de que suas buscas individuais tocam o mesmo problema maior:

- relíquias antigas;
- falsificações alquímicas;
- ruínas esquecidas;
- marcas do [[Véu Cinzento]];
- histórias que sobreviveram como rumor, medo ou superstição.

## Personagens em Foco

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE contains(tags, "player") OR contains(tags, "jogador")
SORT file.name ASC

// Settings
preset: compact
columns: 3
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## Pontos Sustentados pelo Vault

- [[Vezemir]] busca o dragão de colar dourado e respostas sobre os [[Guardiões do Véu Cinzento]].
- [[Varkh Nimalis]] investiga remédios falsos ligados aos métodos de [[Mestre Odran Veyl]].
- [[Raziel]] despertou após mais de trezentos anos e procura os responsáveis por sua traição.
- [[Nimalia]] é o reino dos antropos, com [[Nimalis]] como capital.
- A [[Floresta de Avenor]] faz fronteira com Nimalia.
- [[Leth'valora]] foi destruída pelo [[Dragão de Colar Dourado]].
- A forma exata como os três personagens se encontram permanece em aberto.

## Premissa de Trabalho

Um mesmo rastro começa a aparecer em lugares diferentes: um símbolo antigo em um frasco falso, uma inscrição apagada em uma ruína, uma história sobre névoa cinzenta contada por gente que jura não acreditar em lendas.

Cada personagem tem uma razão própria para seguir esse rastro.

- Vezemir vê uma possível ligação com o dragão e com os Guardiões do Véu Cinzento.
- Varkh vê uma pista sobre quem está usando os métodos de Odran.
- Raziel vê ecos de poderes antigos ligados às [[Ruínas de Valthor]], à [[Fortaleza de Gharok]] e ao sangue que o reconstruiu.

## Possíveis Pontos de Encontro

> [!note]
> Escolher apenas um quando a sessão for preparada. Não canonizar todos ao mesmo tempo.

- Uma rota entre [[Nimalis]] e a [[Floresta de Avenor]].
- Uma investigação sobre remédios falsos que chega perto de território ligado ao Véu.
- Uma ruína menor conectada indiretamente às [[Ruínas de Valthor]].
- Um pedido do [[Conclave dos Errantes]] envolvendo uma relíquia ou escolta.
- Um rumor vindo do Mar da Neblina que cruza com documentos da Coroa.

## Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM #quest
WHERE quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM #rumor
SORT file.name ASC
```

## Segredos do Mestre

- A conexão real entre o [[Véu Cinzento]], os Guardiões e os Criadores ainda não deve ser revelada de uma vez.
- A relação entre o dragão de colar dourado e os eventos antigos deve ser mostrada por pistas, não por exposição direta.
- As pistas de Varkh devem parecer mundanas antes de apontarem para algo maior.
- Raziel deve entrar com peso, mas sem resolver o mistério inteiro sozinho.

## Pendências Antes de Jogar

- Definir ponto inicial da mesa.
- Definir o primeiro incidente visível.
- Separar informação pública de segredo do mestre.
- Confirmar quais imagens serão usadas como capa, retrato ou handout.
- Definir quais pistas aparecem no primeiro encontro.

## Uso em Mesa

- **Como apresentar:** começar por uma consequência concreta, não por explicação de lore.
- **O que os jogadores sabem:** cada personagem sabe sua própria motivação inicial.
- **O que apenas o mestre sabe:** as conexões entre Véu, dragão, sangue antigo e falsificações.
- **Como entra em cena:** por rastro, contrato, rumor, perseguição ou descoberta.
- **Ganchos:** frasco falso, símbolo antigo, sobrevivente assustado, ruína interditada, mapa incompleto.
- **Consequências possíveis:** os personagens se unem por conveniência, dívida, suspeita ou ameaça compartilhada.
