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
name: O Frasco Afogado Está Silencioso
location: "[[O Frasco Afogado]]"
territory: "[[Nimalia]]"
faction:
danger_level: D
rumors:
  - "[[02 - Investigar Remédios Falsos de Maré Baixa]]"
hooks:
  - "[[02 - Investigar Remédios Falsos de Maré Baixa]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/locations/loja_odran.png
cover: zz_media/locations/loja_odran.png
tags:
  - rumor
  - story
  - capitulo01
  - mare-baixa
---

# 04 — O Frasco Afogado Está Silencioso

Há quem diga que [[O Frasco Afogado]] anda quieto demais para uma loja acostumada a cheiro de ervas, álcool barato e panela fervendo.

## O que se diz

Alguns moradores de [[Maré Baixa]] dizem que o movimento diminuiu. Outros afirmam ter visto gente estranha rondando o lugar.

Ninguém sabe se isso tem relação com os remédios falsos.

## Onde Pode Ser Ouvido

- [[Maré Baixa]];
- cais e becos perto do porto;
- vendedores de remédio barato;
- gente que conhecia [[Mestre Odran Veyl]].

## Quem sabe

- vizinhos da loja;
- clientes antigos;
- vendedores informais;
- pessoas que devem favores a Odran ou a [[Varkh Nimalis]].

## Como Investigar

Ir até o local, observar movimento, procurar testemunhas e comparar os frascos falsos com o método usado por Odran.

## Ligação com Quests

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE (contains(hooks, this.file.link) OR contains(rumors, this.file.link))
AND type != "index"
SORT file.name ASC
```

## Uso em Mesa

- Quem pode contar: vizinho, vendedor de rua, criança de Maré Baixa ou contato do Conclave.
- Onde pode ser ouvido: cais, taverna pobre, beco ou mercado informal.
- Parte verdadeira: o lugar está ligado à memória de Odran e Varkh.
- Parte falsa ou distorcida: ninguém pode afirmar culpa de Odran.
- Como investigar: visitar a loja e seguir rastros de frascos adulterados.
