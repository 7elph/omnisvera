---
obsidianUIMode: preview
NoteIcon: magic
NoteStatus: Active
status: Ativo
visibility: gm
cover:
tags:
  - magic
  - index
---

# Magias e Poderes

Este índice reúne magias, habilidades raciais e poderes narrativos. Cada nota registra sua fonte e indica quando o efeito é autoral.

```dataview
TABLE magic_type, class, level, source, authorial, NoteStatus
FROM "Magic"
WHERE file.name != this.file.name
SORT magic_type ASC, file.name ASC
```

## Categorias

- **Magia de classe:** segue uma lista e progressão do sistema.
- **Habilidade racial:** pertence a uma raça ou linhagem.
- **Poder de personagem:** exceção vinculada a um personagem.
- **Poder narrativo:** existe na ficção, mas ainda não possui mecânica.
