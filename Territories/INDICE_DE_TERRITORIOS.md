---
obsidianUIMode: preview
NoteIcon: territory
NoteStatus: Active
type: index
status: Ativo
campaign_status: Ativo
visibility: Jogadores
spoiler_level: none
gm_secret: false
created_by: Sage
tags:
  - indice
  - territorio
---

# Índice de Territórios

Índice operacional dos territórios e regiões amplas de Omnisvera.

```dataview
TABLE cover, status, campaign_status, location, territory, region, leader, population
FROM "Territories"
WHERE type = "territory"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Territórios do Mestre

```dataview
TABLE status, campaign_status, territory, region, spoiler_level
FROM "Territories"
WHERE type = "territory"
AND visibility = "Mestre"
SORT file.name ASC
```

## Regra de Uso

- `Territories/` guarda regiões grandes: reino, floresta regional, mar, campos amplos e domínios.
- Pontos jogáveis menores ficam em `Locations/`.
- Se uma cena acontece ali diretamente, provavelmente é `location`.
- Se o lugar organiza fronteiras, mapa e regiões menores, provavelmente é `territory`.
