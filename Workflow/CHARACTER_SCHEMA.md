---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Ativo
visibility: gm
tags:
  - workflow
  - schema
  - character-system
---

# Schema de personagens

## Templates

- Jogador: [[Workflow/Templates/Player Character Template]]
- NPC completo: [[Workflow/Templates/Character Template]]
- NPC mínimo: [[Workflow/Templates/NPC Placeholder Template]]

## Propriedades comuns

| Propriedade | Função |
|:--|:--|
| `NoteStatus` | Estado editorial da nota. |
| `status` | Estado do personagem no mundo. |
| `visibility` | `player`, `shared` ou `gm`. |
| `thumbnail` | Retrato usado em consultas. |
| `location` | Localização atual. |
| `territory` | Território atual. |
| `faction` | Afiliação atual. |
| `religion` | Religião, quando definida. |
| `class` | Classe mecânica. |
| `race` | Raça. |
| `level` | Nível, sempre em minúsculas. |
| `role` | `player` ou `npc`. |
| `occupation` | Cargo ou profissão de NPC. |
| `chapters` | Lista de capítulos. |

## Atributos de jogadores

Os valores mecânicos ficam no frontmatter para poderem ser reutilizados por Dataview:

```yaml
forca:
destreza:
constituicao:
inteligencia:
sabedoria:
carisma:
classe_armadura:
pontos_vida:
bonus_ataque:
jogada_protecao:
movimento:
```

Exemplo de consulta:

```text
`= [[Vezemir]].forca`
```

As fichas usam uma tabela no início da nota e podem ser vinculadas diretamente por seção, como `[[Vezemir#Atributos]]`.

## Ordem das fichas de jogadores

1. Retrato.
2. Atributos.
3. Visão geral.
4. História e marcos.
5. Atualidade.
6. Personalidade.
7. Habilidades.
8. Segredos do mestre.
9. Equipamentos.
10. Aparência.
11. Consultas de itens.
12. Regras específicas e capítulos.

## Personagens atuais

| Personagem | Classe | Situação mecânica |
|:--|:--|:--|
| [[Players/Characters/Vezemir]] | Guerreiro | Atributos transcritos; poderes autorais em teste. |
| [[Players/Characters/Varkh Nimalis]] | Alquimista | Atributos da Ficha do Jão; classe em adaptação. |
| [[Players/Characters/Raziel]] | Ladrão / Assassino | Atributos ainda não fornecidos; vampiro e hemomante pendentes. |

## Regra de segurança

- Não inventar atributos ausentes.
- Não usar cargo ou título como `role`.
- Segredos ficam em callout `gm` e em notas com `visibility: gm`.
- Para material compartilhado, usar os resumos em `Players/Characters/`.
