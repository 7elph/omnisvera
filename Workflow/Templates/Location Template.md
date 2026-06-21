---
obsidianUIMode: preview
NoteIcon: location
NoteStatus: Template
status: Ativa
visibility: shared
territory:
district:
leader:
population:
info:
cover:
tags:
  - template
  - location
---

# NOME DA LOCALIZAÇÃO

> [!NOTE|clean no-i right]+ NOME
> Adicionar imagem quando estiver disponível.

## Visão geral

Descrição curta do lugar.

## Localização

**Território:**

**Região ou distrito:**

**Acesso:**

## Aparência

Atmosfera, arquitetura e elementos reconhecíveis.

## Pessoas e grupos

```dataview
TABLE status, role, faction
FROM "Characters"
WHERE contains(string(location), this.file.name)
SORT file.name ASC
```

## Pontos de interesse

- _Ponto de interesse._

## Rumores

- _Rumor conhecido._

> [!gm]- Verdade do mestre
> Segredos, perigos e acontecimentos ainda não descobertos.
