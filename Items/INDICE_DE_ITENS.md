---
obsidianUIMode: "preview"
NoteIcon: "items"
NoteStatus: "Active"
type: "index"
status: "Ativo"
campaign_status: "Ativo"
visibility: "Mestre"
spoiler_level: "none"
gm_secret: true
created_by: "Sage"
tags:
  - "indice"
  - "indice-item"
---

# Índice de Itens

Índice operacional para itens comuns, catálogo de compras, relíquias, armas, escudos, objetos narrativos e serviços compráveis.

## Notas Centrais

- [[Catálogo de Compras]] — índice jogável para compra de equipamentos.
- [[Regras de Compra e Equipamento]] — moedas, materiais especiais, serviços mágicos e regra de item base.

## Regra de Uso

- `item_family` organiza o catálogo por função ampla.
- `item_category` define a categoria prática: arma, proteção, kit, serviço, propriedade etc.
- `purchase_status` separa `Comprável`, `Raro`, `Compra especial`, `Improvisado` e `Não comprável`.
- `base_item` liga relíquias narrativas a um item comum de equilíbrio inicial.
- `origin_fit` conecta itens aos capítulos de origem: `origem-vezemir`, `origem-varkh`, `origem-raziel` e `capitulo01`.
- `visibility` e `gm_secret` continuam controlando o que aparece para jogadores.

## Catálogo Comprável

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, weight_kg AS "Peso kg", purchase_status AS Compra, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND purchase_status != "Não comprável"
SORT item_family ASC, item_category ASC, file.name ASC
```

## Relíquias e Itens Narrativos

```dataview
TABLE item_type AS Tipo, owner AS Portador, base_item AS "Item base", status, visibility, danger_level
FROM "Items"
WHERE type = "item"
AND purchase_status = "Não comprável"
SORT owner ASC, file.name ASC
```

## Todos os Itens

```dataview
TABLE item_family AS Família, item_category AS Categoria, item_type AS Tipo, price AS Preço, owner AS Portador, status, visibility, danger_level
FROM "Items"
WHERE type = "item"
SORT item_family ASC, file.name ASC
```

## Itens dos Jogadores

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, owner AS Portador, status
FROM "Items"
WHERE type = "item"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT owner ASC, item_family ASC, file.name ASC
```

## Itens de Mestre / Spoiler

```dataview
TABLE item_type AS Tipo, owner AS Portador, status, spoiler_level, base_item AS "Item base"
FROM "Items"
WHERE type = "item"
AND visibility = "Mestre"
SORT spoiler_level DESC, file.name ASC
```

## Por Origem

### Vezemir

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-vezemir")
SORT item_family ASC, file.name ASC
```

### Varkh

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-varkh")
SORT item_family ASC, file.name ASC
```

### Raziel

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-raziel")
SORT item_family ASC, file.name ASC
```

## Pendências

- Definir imagens para itens comuns apenas quando houver necessidade visual.
- Confirmar se as relíquias liberam propriedades especiais por nível, capítulo ou gatilho narrativo.
- Manter o catálogo de compra separado dos itens únicos de campanha.
