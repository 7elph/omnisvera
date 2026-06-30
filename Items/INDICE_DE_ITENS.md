---
obsidianUIMode: preview
NoteIcon: items
NoteStatus: Active
type: index
status: Ativo
campaign_status: Ativo
visibility: Mestre
spoiler_level: none
gm_secret: true
created_by: Sage
tags:
  - indice
  - item
---

# Índice de Itens

Índice operacional para itens, artefatos, armas, escudos, relíquias, estabelecimentos importantes e objetos narrativos.

## Todos os Itens

```dataview
TABLE thumbnail, item_type, owner, status, visibility, danger_level
FROM "Items"
WHERE type = "item"
SORT file.name ASC
```

## Itens dos Jogadores

```dataview
TABLE thumbnail, item_type, owner, status
FROM "Items"
WHERE type = "item"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT owner ASC, file.name ASC
```

## Itens de Mestre / Spoiler

```dataview
TABLE item_type, owner, status, spoiler_level
FROM "Items"
WHERE type = "item"
AND visibility = "Mestre"
SORT spoiler_level DESC, file.name ASC
```

## Pendências

- Definir imagens para itens de Varkh que ainda não têm thumbnail/capa.
- Decidir se `O Frasco Afogado` permanece em `Items` ou vira `Location`/estabelecimento no futuro.
- Confirmar mecânicas finais de relíquias e artefatos.
