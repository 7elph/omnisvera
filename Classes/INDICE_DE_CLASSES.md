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

## Classes Especiais

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
- `Homem de Armas` não é classe ativa separada; usar [[Guerreiro]].
- [[Guerreiro]] usa a mecânica marcial básica do material de mesa, com o nome operacional confirmado pelo Sage.
- `Especialista de Armas` é o nome operacional da especialização marcial focada em uma arma.
- [[Paladino]] é especialização/caminho de [[Guerreiro]], não classe-base separada.
- [[Hemomante]] é classe ativa de [[Raziel]], ligada à raça/condição [[Vampiro]].
- [[Vampiro]] é raça/condição em `Races/`, não classe.
- PDFs de regras não devem ser commitados; as notas guardam a consulta mecânica necessária para mesa.
