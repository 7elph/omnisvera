---
obsidianUIMode: preview
NoteIcon: spell
NoteStatus: Draft
type: index
status: Rascunho
visibility: Mestre
spoiler_level: medium
gm_secret: true
created_by: Sage
campaign_status: Em revisao
tags:
  - indice
  - magia
---

# Índice de Magias

Este índice organiza magias por uso de campanha.

Não reproduzir texto integral de livros ou materiais protegidos. Cada nota de magia deve conter apenas estrutura própria, resumo original e campos de controle.

## Magias Liberadas

```dataview
TABLE level, status, campaign_status, danger_level
FROM "Rules/Spells"
WHERE type = "spell"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT level ASC, file.name ASC
```

## Magias do Mestre

```dataview
TABLE level, status, campaign_status, danger_level
FROM "Rules/Spells"
WHERE type = "spell"
SORT level ASC, file.name ASC
```

## Regra de Uso

- Criar notas de magia apenas quando forem usadas em mesa ou relevantes para a lore.
- Magias podem ter função mecânica, narrativa ou ritualística.
- Quando vierem de livros, registrar apenas referência interna de uso e resumo próprio.
- Não copiar descrições completas, tabelas extensas ou texto protegido.
