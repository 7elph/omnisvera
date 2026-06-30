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

## Regra de Uso

- `item_type` define a função prática: arma, escudo, relíquia, máscara, caderno, estabelecimento etc.
- `visibility` controla se o item pode aparecer para jogadores.
- `gm_secret: true` indica item sensível ou revelação de mestre.
- `thumbnail` alimenta cards e listagens.
- Itens que ainda não possuem imagem devem permanecer sem `thumbnail`/`cover` até existir imagem correspondente em `zz_media`.
- `O Frasco Afogado` permanece em `Items/` por enquanto porque funciona como estabelecimento narrativo ligado a Varkh; pode virar `Location` em etapa futura.

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
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
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

## Itens sem Imagem Específica

```dataview
TABLE item_type, owner, status
FROM "Items"
WHERE type = "item"
AND (thumbnail = null OR thumbnail = "")
SORT file.name ASC
```

## Pendências

- Definir imagens para itens de Varkh que ainda não têm thumbnail/capa.
- Decidir se `O Frasco Afogado` permanece em `Items` ou vira `Location`/estabelecimento no futuro.
- Confirmar mecânicas finais de relíquias e artefatos.
- Confirmar se as propriedades especiais de Grisalma, Muralha de Dorn, Adagas e Manto viram mecânica ou continuam como descrição narrativa controlada pelo mestre.
