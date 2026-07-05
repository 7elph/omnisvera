---
obsidianUIMode: preview
NoteIcon: class
NoteStatus: Active
type: index
status: Ativo
visibility: Jogadores
spoiler_level: none
gm_secret: false
created_by: Sage
campaign_status: Ativo
tags:
  - indice
  - indice-classe
---

# Índice de Classes

Índice operacional das classes usadas em Omnisvera.

## Classes Ativas

- [[Alquimista]]
- [[Clérigo]]
- [[Guerreiro]]
- [[Ladrão]]
- [[Mago]]

## Classes Autorais / Especiais

- [[Hemomante]]

## Especializações / Caminhos

- [[Paladino]] — especialização/caminho de [[Guerreiro]]

```dataview
TABLE status, rules_status, campaign_status, visibility, thumbnail
FROM "Classes"
WHERE type = "class"
AND NoteStatus != "Placeholder"
AND file.name != "Vampiro"
SORT file.name ASC
```

## Regra de Uso

- `Classes/` é a pasta oficial de classes.
- Não usar `Rules/Classes`.
- Não reproduzir texto integral de livros ou suplementos.
- `Homem de Armas` não é classe ativa separada; usar [[Guerreiro]].
- [[Paladino]] é especialização/caminho de [[Guerreiro]], não classe-base separada.
- Classes especiais, como [[Hemomante]], ficam em revisão do mestre até estabilização.
- [[Vampiro]] é raça/condição em `Races/`, não classe.
