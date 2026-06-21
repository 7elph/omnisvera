---
obsidianUIMode: preview
NoteIcon: home
NoteStatus: Active
status: Ativo
visibility: shared
cover:
tags:
  - template
  - index
---

# NOME DO ÍNDICE

Breve orientação sobre o conteúdo desta área.

## Conteúdo

```datacards
TABLE cover, info, status
FROM "PASTA"
WHERE NoteStatus != "Archived"
SORT file.name ASC

// Settings
preset: grid
columns: 5
imageProperty: cover
cardSpacing: 4
```

## Em desenvolvimento

```dataview
TABLE NoteStatus, status
FROM "PASTA"
WHERE NoteStatus = "Draft" OR NoteStatus = "Placeholder"
SORT file.name ASC
```
