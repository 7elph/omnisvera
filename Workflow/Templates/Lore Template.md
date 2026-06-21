---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: Draft
status: Em desenvolvimento
visibility: gm
info:
era:
related: []
cover:
tags:
  - template
  - lore
---

# NOME DO CONCEITO

## Conhecimento público

Registrar somente rumores, versões históricas e fatos acessíveis.

## Registros e versões

- **Versão conhecida:** 
- **Fonte no mundo:** 
- **Confiabilidade:** incerta

## Relações

- _Conceito, lugar, personagem ou facção relacionada._

## Questões em aberto

- _Pergunta que não deve receber resposta inventada._

> [!gm]- Verdade do mestre
> Registrar a verdade confirmada, teorias de preparação e segredos separadamente.

## Notas relacionadas

```dataview
LIST
FROM #lore
WHERE file.name != this.file.name
AND contains(string(related), this.file.name)
SORT file.name ASC
```
