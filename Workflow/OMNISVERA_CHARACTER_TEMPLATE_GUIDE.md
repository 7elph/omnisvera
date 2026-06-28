# Omnisvera — Guia de Templates de Personagem

> [!IMPORTANT]
> Este documento segue a taxonomia oficial atual do Sage.
> Fonte da verdade: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].

## Função

Define o padrão de criação de personagens novos.

Não aplicar em massa a personagens existentes sem lote piloto.

## Frontmatter recomendado

```yaml
---
type: character
NoteIcon: character
status: Rascunho
visibility: Mestre
spoiler_level: heavy
gm_secret: true
revealed_in:
created_by: Sage
campaign_status: Em revisao

name:
epithet:
aliases: []

race:
class:
role:

origin:
location:
territory:
faction: []
faith: []

thumbnail:
cover:

arcs: []
chapters: []

level:
danger_level:
hooks: []
rumors: []

tags:
  - personagem
---
```

## Imagem

Usar `thumbnail` como imagem principal de card e retrato interno quando não houver decisão específica.

```md
> [!NOTE|clean no-i right]+ Retrato
> ![[arquivo-da-imagem.png|400]]
```

## Estrutura recomendada

```md
# Nome — Epíteto

## Visão Geral

## Aparições

## História

## Situação Atual

## Personalidade

## Relações

## Ganchos

## Pendências
```

## Aparições

`chapters` é o campo funcional para capítulos/story/seções.

```dataview
LIST
FROM "EARTHROPO"
WHERE contains(this.chapters, file.name)
SORT file.name ASC
```

## Personagens dos jogadores

Personagens dos jogadores devem usar:

```yaml
visibility: Jogadores
spoiler_level: none
gm_secret: false
tags:
  - personagem
  - jogador
```

## NPCs e antagonistas

NPCs com segredos ou informação de preparação devem usar:

```yaml
visibility: Mestre
spoiler_level: heavy
gm_secret: true
tags:
  - personagem
  - npc
```

## Regras

- Não inventar origem, facção ou segredo sem fonte interna.
- Não transformar nota de jogador em nota pública se houver segredo de mestre.
- Não remover `thumbnail`, `cover`, `chapters` ou `tags`.
- Não depender de tag antiga para cor visual quando já houver equivalente Omnisvera.
