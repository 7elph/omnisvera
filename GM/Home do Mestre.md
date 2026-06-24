---
obsidianUIMode: preview
banner: "[[zz_media/maps/earthropo.png]]"
banner-x: 50
banner-y: 40
banner-height: 280
content-start: 271
banner-fade: -35
NoteIcon: home
NoteStatus: Active
status: Ativo
visibility: gm
tags:
  - home
  - gm
---

# 🜂 OMNISVERA — MESTRE

> [!warning] Área privada
> Esta página reúne segredos, preparação e decisões de continuidade. Ela não constitui controle real de acesso: compartilhar o vault inteiro ainda permite que outras notas sejam abertas.

> [!cards|5]
> **CÂNONE**
> [![[zz_media/ui/card-guia.webp|sban htiny ctr p+t]]](../Workflow/CANON.md)
>
> **DECISÕES**
> [![[zz_media/ui/card-cronicas.webp|sban htiny ctr]]](../Workflow/CONSOLIDATION_DECISIONS.md)
>
> **PREPARAÇÃO**
> [![[zz_media/ui/card-notas.webp|sban htiny ctr]]](../Workflow/OUTLINES.md)
>
> **LORE**
> [![[zz_media/ui/card-boletim.webp|sban htiny ctr]]](../LORE.md)
>
> **MAPA DO MESTRE**
> [![[zz_media/ui/card-mapa.webp|sban htiny ctr]]](Mapa%20de%20Earthropo%20—%20Mestre.md)

## Estado da campanha

- **Data inicial:** 3 de Ventara de 2377.
- **Nível inicial:** 1.
- **Ponto de encontro:** [[Nimalis]].
- **Personagens:** [[Players/Characters/Vezemir]], [[Players/Characters/Varkh Nimalis]] e [[Players/Characters/Raziel]].
- **Tom:** exploração, mistério, ruínas e horror ocasional; política como pano de fundo.

## Preparação imediata

```dataview
TABLE NoteStatus, status, file.folder
FROM "/"
WHERE NoteStatus = "Draft" OR NoteStatus = "Placeholder"
AND !contains(file.path, "Workflow/Templates")
AND !contains(file.path, "Workflow/Legacy")
SORT file.folder ASC, file.name ASC
```

## Lore reservada

```datacards
TABLE cover, info, status
FROM #lore
WHERE visibility = "gm"
SORT file.name ASC

// Settings
preset: grid
columns: 5
imageProperty: cover
cardSpacing: 4
```

## Personagens e NPCs

```dataview
TABLE thumbnail, role, status, location, faction
FROM "Characters"
SORT role ASC, file.name ASC
```

## Ferramentas

- [[Workflow/TEMPLATES|Templates]]
- [[Workflow/GEOGRAPHY|Geografia]]
- [[Workflow/RULES_SOURCES|Fontes de regras]]
- [[Workflow/MIGRATION_LEDGER|Migração]]
- [[Workflow/DELETION_REVIEW|Revisão de exclusões]]
- [[Workflow/LOCAL_ASSISTANT_PROTOCOL|Assistente local]]
