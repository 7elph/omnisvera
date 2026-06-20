---
obsidianUIMode: preview
NoteIcon: chart
NoteStatus: Active
status: Active
tags:
  - workflow
  - report
  - omnisvera
---

# Relatório do Vault

## Conteúdo ativo por categoria

```dataview
TABLE WITHOUT ID
length(filter(rows, (row) => contains(row.file.tags, "character"))) AS "Personagens",
length(filter(rows, (row) => contains(row.file.tags, "faction"))) AS "Facções",
length(filter(rows, (row) => contains(row.file.tags, "location"))) AS "Localizações",
length(filter(rows, (row) => contains(row.file.tags, "territory"))) AS "Territórios",
length(filter(rows, (row) => contains(row.file.tags, "religion"))) AS "Religiões"
FROM "/"
WHERE !contains(file.name, "Legacy - Disgraceland")
GROUP BY true
```

## Notas por estado editorial

```dataview
TABLE WITHOUT ID
NoteStatus AS "Estado",
length(rows) AS "Quantidade"
FROM "/"
WHERE NoteStatus
AND !contains(file.name, "Legacy - Disgraceland")
GROUP BY NoteStatus
SORT NoteStatus ASC
```

## Placeholders e rascunhos

```dataview
TABLE status, info, file.mtime AS "Modificada"
FROM "/"
WHERE NoteStatus = "Placeholder" OR NoteStatus = "Draft"
AND !contains(file.name, "Legacy - Disgraceland")
SORT file.path ASC
```

## Controle

- [[CANON]]
- [[MIGRATION_LEDGER]]
- [[ASSISTANT_HANDOFF]]
- [[Format Audit Report]]
