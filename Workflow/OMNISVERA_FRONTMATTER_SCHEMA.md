---
type: workflow
subtype: standard
work_status: Active
canon_status: Reference
visibility: Mestre
created_by: IA
requires_review: true
tags:
  - workflow
  - standard
  - frontmatter
  - character
---

# Esquema de Frontmatter — Personagens Omnisvera

Este documento define o esquema de frontmatter para notas de personagem no vault Omnisvera.

## Frontmatter Base Obrigatório

Todas as notas de personagem devem incluir este frontmatter base:

```yaml
---
type: character
subtype: player_character
NoteIcon: character
work_status: Em desenvolvimento
canon_status: Draft
visibility: Mestre
created_by: Sage
requires_review: true

name:
epithet:
aliases: []

race:
class:
life_status:
role:

origin:
location:
territory:
faction: []
faith: []

thumbnail:
portrait:
cover:

arcs: []
chapters: []

tags:
  - character
---
```

## Explicação dos Campos

### Campos de Tipo e Status

#### type
- **Tipo:** string
- **Valor:** `character`
- **Função:** Identifica a nota como personagem
- **Obrigatório:** Sim
- **Exemplo:** `type: character`

#### subtype
- **Tipo:** string
- **Valores:** `player_character`, `major_npc`, `minor_npc`, `antagonist`, `creature`
- **Função:** Define o subtipo de personagem
- **Obrigatório:** Sim
- **Exemplo:** `subtype: player_character`

#### NoteIcon
- **Tipo:** string
- **Valores:** `character`, `monster`, `group`, `user`
- **Função:** Ícone visual da nota no Obsidian
- **Obrigatório:** Sim
- **Exemplo:** `NoteIcon: character`

#### work_status
- **Tipo:** string
- **Valores:** `Em desenvolvimento`, `Revisão`, `Finalizado`
- **Função:** Estado editorial da nota
- **Obrigatório:** Sim
- **Exemplo:** `work_status: Em desenvolvimento`

#### canon_status
- **Tipo:** string
- **Valores:** `Draft`, `Working Canon`, `Confirmed`
- **Função:** Estado canônico do conteúdo
- **Obrigatório:** Sim
- **Exemplo:** `canon_status: Draft`

#### visibility
- **Tipo:** string
- **Valores:** `Mestre`, `Jogadores`, `Público`
- **Função:** Nível de acesso à nota
- **Obrigatório:** Sim
- **Exemplo:** `visibility: Mestre`

#### created_by
- **Tipo:** string
- **Valores:** `Sage`, `IA`, `Jogador`
- **Função:** Quem criou a nota
- **Obrigatório:** Sim
- **Exemplo:** `created_by: Sage`

#### requires_review
- **Tipo:** boolean
- **Valores:** `true`, `false`
- **Função:** Indica se a nota precisa de revisão
- **Obrigatório:** Sim
- **Exemplo:** `requires_review: true`

### Campos de Identidade

#### name
- **Tipo:** string
- **Função:** Nome completo do personagem
- **Obrigatório:** Sim
- **Exemplo:** `name: Varkh Nimalis`

#### epithet
- **Tipo:** string
- **Função:** Epíteto ou apelido famoso
- **Obrigatório:** Não
- **Exemplo:** `epithet: O Corvo da Maré Baixa`

#### aliases
- **Tipo:** array de strings
- **Função:** Lista de apelidos alternativos
- **Obrigatório:** Não
- **Exemplo:** `aliases: ["Varkh", "Corvo"]`

### Campos de Caracterização

#### race
- **Tipo:** string
- **Função:** Raça do personagem
- **Obrigatório:** Sim
- **Exemplo:** `race: Kenku`

#### class
- **Tipo:** string
- **Função:** Classe ou profissão
- **Obrigatório:** Para PCs, opcional para NPCs
- **Exemplo:** `class: Ladino`

#### life_status
- **Tipo:** string
- **Valores:** `Vivo`, `Morto`, `Desaparecido`, `Desconhecido`
- **Função:** Estado narrativo do personagem
- **Obrigatório:** Sim
- **Exemplo:** `life_status: Vivo`

#### role
- **Tipo:** string
- **Função:** Papel na história ou sociedade
- **Obrigatório:** Sim
- **Exemplo:** `role: Ladrão e alquimista de rua`

### Campos de Localização

#### origin
- **Tipo:** string (wikilink)
- **Função:** Local de origem
- **Obrigatório:** Não
- **Exemplo:** `origin: "[[Maré Baixa]]"`

#### location
- **Tipo:** string (wikilink)
- **Função:** Local atual
- **Obrigatório:** Não
- **Exemplo:** `location: "[[Nimalis]]"`

#### territory
- **Tipo:** string (wikilink)
- **Função:** Território de origem ou residência
- **Obrigatório:** Não
- **Exemplo:** `territory: "[[Nimalia]]"`

### Campos de Afiliação

#### faction
- **Tipo:** array de strings (wikilinks)
- **Função:** Lista de facções ou grupos
- **Obrigatório:** Não
- **Exemplo:** `faction: ["[[Guardiões do Véu Cinzento]]"]`

#### faith
- **Tipo:** array de strings (wikilinks)
- **Função:** Lista de religiões ou crenças
- **Obrigatório:** Não
- **Exemplo:** `faith: ["[[Igreja das Chamas]]"]`

### Campos de Mídia

#### thumbnail
- **Tipo:** string (caminho)
- **Função:** Imagem miniatura para cards e dashboards
- **Obrigatório:** Não, mas recomendado
- **Exemplo:** `thumbnail: zz_media/characters/th_varkh.png`

#### portrait
- **Tipo:** string (caminho)
- **Função:** Imagem principal do personagem para corpo da nota
- **Obrigatório:** Não, mas recomendado
- **Exemplo:** `portrait: zz_media/characters/varkh.png`

#### cover
- **Tipo:** string (caminho)
- **Função:** Imagem de banner ou capa
- **Obrigatório:** Não
- **Exemplo:** `cover: zz_media/covers/varkh_banner.png`

### Campos de Narrativa

#### arcs
- **Tipo:** array de strings
- **Função:** Lista de arcos narrativos do personagem
- **Obrigatório:** Não
- **Exemplo:** `arcs: ["Investigação de remédios falsos", "Busca por identidade"]`

#### chapters
- **Tipo:** array de strings
- **Função:** Lista de capítulos onde o personagem aparece
- **Obrigatório:** Não, mas recomendado para PCs e NPCs importantes
- **Exemplo:** `chapters: ["00 - O Corvo da Maré Baixa"]`

### Campos de Tags

#### tags
- **Tipo:** array de strings
- **Função:** Tags auxiliares para filtros
- **Obrigatório:** Sim
- **Exemplo:** `tags: [character, kenku, nimalia]`

## Subtipos e Campos Específicos

### player_character

Campos obrigatórios adicionais:
- `class` - Classe do personagem
- `chapters` - Lista de aparições

### major_npc

Campos obrigatórios adicionais:
- `role` - Função narrativa
- `chapters` - Lista de aparições (se aplicável)

### minor_npc

Campos obrigatórios adicionais:
- `role` - Função em cena
- `chapters` - Opcional

### antagonist

Campos obrigatórios adicionais:
- `role` - Papel antagonista
- `arcs` - Arcos antagonistas
- `chapters` - Lista de aparições

### creature

Campos obrigatórios adicionais:
- `race` - Tipo de criatura
- `life_status` - Estado vital
- `role` - Papel ecossistêmico ou narrativo

## Valores Padrão

Para campos não obrigatórios, use valores padrão:

```yaml
aliases: []
faction: []
faith: []
arcs: []
chapters: []
```

## Wikilinks em Frontmatter

Use wikilinks para referências a outras notas:

```yaml
origin: "[[Maré Baixa]]"
location: "[[Nimalis]]"
territory: "[[Nimalia]]"
faction: ["[[Guardiões do Véu Cinzento]]"]
faith: ["[[Igreja das Chamas]]"]
```

## Regras de Nomenclatura

- Use camelCase para nomes de campos
- Use português para valores narrativos
- Use inglês apenas para termos técnicos consolidados
- Seja consistente com valores (ex: sempre "Vivo", nunca "vivo")

## Exemplo Completo

```yaml
---
type: character
subtype: player_character
NoteIcon: character
work_status: Em desenvolvimento
canon_status: Draft
visibility: Mestre
created_by: Sage
requires_review: true

name: Varkh Nimalis
epithet: O Corvo da Maré Baixa
aliases: ["Varkh", "Corvo"]

race: Kenku
class: Ladino
life_status: Vivo
role: Ladrão e alquimista de rua

origin: "[[Maré Baixa]]"
location: "[[Nimalis]]"
territory: "[[Nimalia]]"
faction: []
faith: []

thumbnail: zz_media/characters/th_varkh.png
portrait: zz_media/characters/varkh.png
cover: zz_media/covers/varkh_banner.png

arcs: ["Investigação de remédios falsos", "Busca por identidade"]
chapters: ["00 - O Corvo da Maré Baixa"]

tags:
  - character
  - kenku
  - nimalia
---
```

## Documentos Relacionados

- `Workflow/OMNISVERA_NOTE_STANDARD.md` - Padrão geral de notas
- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` - Sistema de dashboards
- `Workflow/OMNISVERA_MEDIA_STANDARD.md` - Padrão de mídia
- `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md` - Guia de templates
