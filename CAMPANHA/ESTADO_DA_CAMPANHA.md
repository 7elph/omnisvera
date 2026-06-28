---
obsidianUIMode: preview
NoteIcon: story
NoteStatus: Active
type: story
visibility: Mestre
spoiler_level: heavy
gm_secret: true
status: Ativo
campaign_status: Ativo
created_by: MIA
tags:
  - story
  - campanha
---

# Estado da Campanha

> [!NOTE]
> Painel manual do Mestre para acompanhar o estado atual da campanha.

## Capítulo Atual

## Próxima Sessão

## Personagens em Foco

```dataview
TABLE status, location, faction
FROM #personagem
WHERE visibility = "Mestre" OR visibility = "Jogadores" OR visibility = "Público"
SORT file.name ASC
LIMIT 12
```

## Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM #quest
WHERE quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM #rumor
SORT file.name ASC
```

## Facções em Movimento

```dataview
TABLE status, location, territory
FROM #faccao OR #faction
SORT file.name ASC
```

## Locais em Foco

```dataview
TABLE territory, status, danger_level
FROM #local OR #location OR #territorio
SORT file.name ASC
LIMIT 12
```

## Itens Revelados

```dataview
TABLE status, location
FROM #item OR #artefato
SORT file.name ASC
```

## Segredos Pendentes

-

## Consequências Recentes

-

## Notas para a Próxima Sessão

-
