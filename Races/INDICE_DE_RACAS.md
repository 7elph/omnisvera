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
  - indice-raca
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
- [[Meio-Elfo]] — categoria especial usada por [[Vezemir]], combinando bases de Humano e Elfo
- [[Anão]]
- [[Dragonborn]]
- [[Kenku]] — raça jogável de [[Varkh Nimalis]], dentro do guarda-chuva antropo
- [[Vampiro]] — raça/condição de [[Raziel]]

## Em Revisão / Bônus Futuro

- [[Halfling]]

## Regra de Uso

- `Races/` é a pasta oficial de raças.
- Não usar `Rules/Races`.
- Não copiar regras completas de livros; manter apenas síntese própria e decisões do Sage.
- Raças ainda não aprovadas podem permanecer como `Em revisão`.
- [[Antropo]] é o nome canônico de Omnisvera para beastfolk.
- Homem-Tigre é referência mecânica para antropos felinos, não nome canônico do cenário.
