---
obsidianUIMode: preview
NoteIcon: religion
NoteStatus: Draft
type: lore
status: Cânone parcial
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
thumbnail: zz_media/fe-dos-antigos.png
cover: zz_media/fe-dos-antigos.png
info: Índice operacional de religiões, cultos e tradições espirituais de Earthropo.
description: Religiões públicas, tradições espirituais e crenças em revisão para uso em mesa.
chapters: []
tags:
  - home
  - lore
  - religiao
  - earthropo
---

# Religiões de Earthropo

> [!NOTE|clean no-i right]+ Religiões de Earthropo
> ![[fe-dos-antigos.png|400]]

> [!world]- SINOPSE
> A fé em Earthropo aparece como templo, tradição oral, rito doméstico, culto escondido, memória antiga e disputa política. Nem toda crença é uma igreja organizada; nem toda igreja entende a verdade sobre aquilo que venera.

## Status

> [!warning]
> Documento em revisão. Cânone parcial.

Este índice organiza religiões, tradições espirituais e cultos em desenvolvimento. Ele não resolve doutrinas, lideranças ou dogmas sem confirmação posterior.

## Índice de Religiões

> [!infobox]
> ```datacards
> TABLE thumbnail, status, info
> FROM "Religion"
> WHERE file.name != this.file.name
> SORT file.name ASC
>
> // Settings
> preset: compact
> columns: 4
> imageProperty: thumbnail
> cardSpacing: 4
> ```

## Religiões Ativas

| religião | status | crença central | uso em mesa |
|---|---|---|---|
| [[Igreja das Chamas]] | `EM_REVISAO` | Fé organizada associada às chamas, virtudes, memória e purificação. | Templos, sacerdotes, moral pública, julgamento, ritos de memória. |
| [[Fé dos Antigos]] | `EM_REVISAO` | Tradições anteriores ao Eclipse; possível relação com os Criadores. | Ruínas, símbolos antigos, fé popular, conflito com versões oficiais. |
| [[Caminho dos Errantes]] | `EM_REVISAO` | Tradição espiritual ligada a viagens, ciclos e retorno. | Estradas, viajantes, mercadores, peregrinos, despedidas e reencontros. |

## Tradições Espirituais

- Cultos domésticos e ancestrais ainda precisam ser definidos.
- Crenças élficas, anãs e dos antropos devem ser apresentadas gradualmente.
- Nem toda tradição espiritual precisa virar igreja organizada.

## Cultos e Crenças em Revisão

| crença/culto | status | observação |
|---|---|---|
| [[Culto dos Sussurrantes]] | `NEEDS_SAGE_REVIEW` | Conceito herdado de versão anterior; não tratar como religião canônica sem revisão. |

## Relação com Facções

- [[Igreja das Chamas]] pode ter relação com a Coroa, mas isso ainda precisa de definição política.
- [[Caminho dos Errantes]] não deve ser confundido automaticamente com o [[Conclave dos Errantes]].
- Cultos ligados ao [[Véu Cinzento]] devem ser tratados como segredo do mestre até confirmação.

## Modelo para Cada Religião

Ao desenvolver uma religião ou tradição espiritual, manter esta ordem:

1. Crenças centrais.
2. Práticas e tradições.
3. Símbolos.
4. Estrutura.
5. Influência.
6. Relações.
7. Segredos do mestre.
8. Uso em mesa.

## Reservas do Mestre

- A relação entre religiões, Criadores e o [[Eclipse de Obsidiana]] permanece em aberto.
- Contradições entre fé pública e história antiga devem ser reveladas progressivamente.
- Revelações pesadas devem ficar no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]] até serem liberadas.

## Uso em Mesa

- Como apresentar: símbolos, ritos pequenos, frases, medos e costumes locais.
- O que os jogadores sabem: religiões públicas e seus templos visíveis.
- O que apenas o mestre sabe: verdades antigas, cultos perigosos e manipulações institucionais.
- Como entra em cena: bênçãos, funerais, julgamento moral, investigação de ruínas e conflito político.
- Ganchos: relíquia religiosa falsa, sacerdote desaparecido, templo com registros contraditórios.
- Consequências possíveis: apoio de fiéis, perseguição, acesso a arquivos ou hostilidade de culto.
