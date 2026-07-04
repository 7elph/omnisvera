---
obsidianUIMode: "preview"
NoteIcon: "items"
NoteStatus: "Active"
type: "index"
status: "Ativo"
campaign_status: "Ativo"
visibility: "Jogadores"
spoiler_level: "none"
gm_secret: false
created_by: "Codex"
source_system: "Old Dragon 2e"
tags:
  - "indice"
  - "indice-item"
  - "catalogo-compra"
  - "item"
---

# Catálogo de Compras

Catálogo jogável de itens comuns, raros e serviços disponíveis para compras em Omnisvera. Os valores vêm do livro-base anexado e devem ser tratados como referência inicial, sem transformar equipamento comum em relíquia.

## Como Usar

- `purchase_status: Comprável` indica compra comum.
- `purchase_status: Raro` exige fornecedor especializado ou cena de busca.
- `purchase_status: Compra especial` envolve patrimônio, montarias caras, veículos ou autorização social.
- `purchase_status: Improvisado` não tem preço fixo e deve nascer de cena.
- Relíquias dos personagens continuam em notas próprias e usam `base_item` para equilíbrio inicial.

## Armas

```dataview
TABLE item_category AS Categoria, damage AS Dano, damage_type AS "Tipo", range AS Alcance, critical AS Crítico, weight_kg AS "Peso kg", price AS Preço, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Armas"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Proteção

```dataview
TABLE item_category AS Categoria, armor_bonus AS CA, movement_penalty AS Movimento, max_dex_bonus AS "DES máx.", weight_kg AS "Peso kg", price AS Preço, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Proteção"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Kits e Ferramentas

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Efeito, weight_kg AS "Peso kg", price AS Preço, kit_membership AS Kit, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Kits e ferramentas"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Alquimia e Especiais

```dataview
TABLE mechanical_effect AS Efeito, weight_kg AS "Peso kg", price AS Preço, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Alquimia e especiais"
AND purchase_status != "Não comprável"
SORT file.name ASC
```

## Propriedades e Montarias

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Detalhe, price AS Preço, purchase_status AS Compra, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Propriedades e montarias"
AND purchase_status != "Não comprável"
SORT price_po ASC, file.name ASC
```

## Hospedagem e Serviços

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Detalhe, price AS Preço
FROM "Items"
WHERE type = "item"
AND item_family = "Hospedagem e serviços"
AND purchase_status != "Não comprável"
SORT item_category ASC, price_po ASC, file.name ASC
```

## Materiais e Magia

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Efeito, price AS Preço, purchase_status AS Compra, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Materiais e magia"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
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

## Regras Relacionadas

- [[Regras de Compra e Equipamento]]
- [[INDICE_DE_ITENS]]
