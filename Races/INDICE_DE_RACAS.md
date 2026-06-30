---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Active
type: index
status: Ativo
visibility: Jogadores
spoiler_level: none
gm_secret: false
created_by: Sage
campaign_status: Ativo
tags:
  - indice
  - raca
---

# Índice de Raças

Índice operacional das raças usadas em Omnisvera.

```dataview
TABLE status, campaign_status, visibility, territory, region
FROM "Races"
WHERE type = "race"
AND NoteStatus != "Placeholder"
SORT file.name ASC
```

## Raças Confirmadas

- [[Antropo]]
- [[Humano]]
- [[Elfo]]
- [[Meio-Elfo]]
- [[Anão]]
- [[Dragonborn]]
- [[Kenku]]
- [[Vampiro]]

## Em Revisão / Bônus Futuro

- [[Halfling]]

## Regra de Uso

- `Races/` é a pasta oficial de raças.
- Não usar `Rules/Races`.
- Não copiar regras completas de livros; manter apenas síntese própria e decisões do Sage.
- Raças ainda não aprovadas podem permanecer como `Em revisão`.
