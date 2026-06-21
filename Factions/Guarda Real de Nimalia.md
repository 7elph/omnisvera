---
obsidianUIMode: preview
NoteIcon: faction
NoteStatus: Draft
status: Ativa
visibility: shared
leader: "[[General Cassian Valerius]]"
headquarters: Fortaleza Real, Nimalis
territory: "[[Nimalia]]"
thumbnail: zz_media/t7.png
tags:
  - faction
  - military
  - guard
  - nimalia
---

# Guarda Real de Nimalia

> [!NOTE|clean no-i right]+ Guarda Real
> ![[t7.png|400]]

A Guarda Real é a força responsável pela segurança da Coroa, da capital e das principais rotas do Reino de [[Nimalia]].

## Liderança

[[General Cassian Valerius]] coordena a defesa estratégica do reino e responde diretamente a [[Augustus Terra Decimus]].

## Funções

- Proteger Nimalis e instalações reais.
- Patrulhar estradas e fronteiras prioritárias.
- Responder a monstros, desastres e ameaças organizadas.
- Apoiar autoridades locais quando o risco supera sua capacidade.

## Estrutura

Números exatos de soldados, companhias e postos permanecem em aberto. A Guarda deve parecer suficiente para proteger o reino, mas incapaz de resolver sozinha todos os perigos encontrados pelos aventureiros.

## Membros

```dataview
TABLE thumbnail, location, status, occupation
FROM "Characters"
WHERE contains(string(faction), this.file.name)
SORT file.name ASC
```
