---
obsidianUIMode: preview
NoteIcon: location
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
  - location
  - local
---

# Índice de Locais

Índice operacional dos locais jogáveis de Omnisvera.

```dataview
TABLE cover, territory, location, region, district, status, danger_level
FROM "Locations"
WHERE type = "location"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT territory ASC, file.name ASC
```

## Locais do Mestre

Locais sensíveis, rascunhos ou ligados a origem de personagens ficam visíveis para o mestre.

```dataview
TABLE territory, location, region, status, spoiler_level
FROM "Locations"
WHERE type = "location"
AND visibility = "Mestre"
SORT file.name ASC
```

## Regra de Uso

- `Locations/` guarda pontos jogáveis: cidade, bairro, loja, estrada, fortaleza, ruína ou vila.
- Regiões grandes ficam em `Territories/`.
- Se uma cena pode acontecer ali diretamente, provavelmente é `location`.
- Segredos completos e bastidores devem ficar em [[ESTADO_DA_CAMPANHA]].
