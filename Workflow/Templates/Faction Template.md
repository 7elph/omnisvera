---
obsidianUIMode: preview
NoteIcon: faction
NoteStatus: Template
status: Ativa
visibility: gm
leader:
headquarters:
territory:
alignment:
tags:
  - template
  - faction
---

# NOME DA FACÇÃO

## Visão geral

Descrição curta da função da facção no cenário.

## Identidade

**Tipo:**

**Liderança:**

**Sede:**

**Área de atuação:**

**Símbolo:**

## Objetivos

- _Objetivo confirmado._

## Organização

Descrever estrutura, recrutamento e recursos.

## Relações

| Grupo | Relação | Estado |
|:--|:--|:--|
| | | |

## Conhecimento público

O que personagens comuns podem saber.

> [!gm]- Verdade do mestre
> Segredos, contradições e planos ocultos.

## Membros

```dataview
TABLE status, location, occupation
FROM "Characters"
WHERE contains(string(faction), this.file.name)
SORT file.name ASC
```
