> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Proposta de Schema YAML

Proposta de schemas YAML para diferentes tipos de notas no vault Omnisvera.

**Nota:** Estes schemas são propostas. Não aplique nas notas sem autorização do Sage.

## Characters

### Personagens jogadores

```yaml
---
NoteIcon: person
NoteStatus: Active | Draft | Placeholder
status: Active | Inativo | Morto | Desaparecido
visibility: player | gm | shared
class: string
race: string
level: number
alignment: string
age: number
height: string
weight: string
cover: zz_media/characters/filename.webp
thumbnail: zz_media/characters/thumbnails/filename.webp
location: string
faction: string
role: string
tags:
  - Category/Character
  - player
  - character
---
```

### NPCs

```yaml
---
NoteIcon: person
NoteStatus: Active | Draft | Placeholder
status: Active | Inativo | Morto
visibility: gm | shared
role: string
location: string
faction: string
cover: zz_media/characters/filename.webp
thumbnail: zz_media/characters/thumbnails/filename.webp
tags:
  - Category/Character
  - npc
  - character
---
```

## Classes

```yaml
---
NoteIcon: class
NoteStatus: Active | Draft
status: Active | Opcional | Legado
ruleset: string
source: string
cover: zz_media/characters/filename.webp
tags:
  - Category/Class
  - class
---
```

## Items

```yaml
---
NoteIcon: item
NoteStatus: Active | Draft
status: Active | Raro | Lendário | Mítico
type: Arma | Armadura | Artefato | Consumível | Ferramenta
rarity: Comum | Incomum | Raro | Lendário | Mítico
cover: zz_media/items/filename.webp
tags:
  - Category/Item
  - item
---
```

## Locations

```yaml
---
NoteIcon: location
NoteStatus: Active | Draft | Placeholder
status: Ativo | Abandonado | Destruído | Em construção
visibility: player | gm | shared
type: Cidade | Vila | Fortaleza | Ruína | Floresta | Montanha
territory: string
region: string
cover: zz_media/locations/filename.webp
tags:
  - Category/Location
  - location
---
```

## Factions

```yaml
---
NoteIcon: organization
NoteStatus: Active | Draft
status: Ativo | Dissolvido | Secreto
visibility: player | gm | shared
type: Governo | Guilda | Religião | Culto | Guarda
cover: zz_media/factions/filename.webp
tags:
  - Category/Faction
  - faction
---
```

## Lore

```yaml
---
NoteIcon: book
NoteStatus: Active | Draft
status: Confirmado | Em aberto | Rumor
visibility: player | gm | shared
type: Evento | Fenômeno | Conceito | História
era: string
cover: zz_media/lore/filename.webp
tags:
  - Category/Lore
  - lore
---
```

## Races

```yaml
---
NoteIcon: users
NoteStatus: Active | Draft
status: Confirmado | Em aberto
visibility: player | gm | shared
cover: zz_media/characters/filename.webp
tags:
  - Category/Race
  - race
---
```

## Religion

```yaml
---
NoteIcon: religion
NoteStatus: Active | Draft
status: Ativa | Extinta | Em desenvolvimento
visibility: player | gm | shared
type: Religião | Culto | Filosofia
cover: zz_media/factions/filename.webp
tags:
  - Category/Religion
  - religion
---
```

## Territories

```yaml
---
NoteIcon: map
NoteStatus: Active | Draft
status: Confirmado | Em aberto
visibility: player | gm | shared
type: Reino | Floresta | Montanha | Deserto | Oceano
cover: zz_media/territories/filename.webp
tags:
  - Category/Territory
  - territory
---
```

## EARTHROPO chapters

```yaml
---
NoteIcon: book-open
NoteStatus: Active | Draft
status: Jogado | Planejado | Cancelado
visibility: player | gm | shared
session: number
date: string
location: string
cover: zz_media/locations/filename.webp
tags:
  - Category/Chapter
  - story
  - earthropo
---
```

## Workflow docs

```yaml
---
NoteIcon: outline
NoteStatus: Active
status: Active
tags:
  - Category/Workflow
  - workflow
---
```

## Campos comuns

- `NoteIcon` - ícone visual da nota
- `NoteStatus` - estado da nota (Active, Draft, Placeholder)
- `status` - estado narrativo ou mecânico
- `visibility` - quem pode ver a nota (player, gm, shared)
- `cover` - imagem de capa
- `thumbnail` - imagem miniatura
- `tags` - categorias e filtros
