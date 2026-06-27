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
  - class
---

# Padrão de Notas de Classe — Omnisvera

Este documento define o padrão oficial para notas de Classe no vault Omnisvera.

## Princípios Fundamentais

Omnisvera segue estes princípios para notas de Classe:

1. **Classe não é facção** - Classe é mecânica de RPG, facção é organização social.
2. **Classe não é cargo social** - Classe define capacidades, não posição hierárquica.
3. **Classe não é apenas regra** - Classe deve ter identidade narrativa e interpretação.
4. **Classe deve separar mecânica, lore e interpretação** - Cada aspecto em seção distinta.
5. **Classe deve indicar fonte de regra** - Sistema de RPG e origem da mecânica.
6. **Classe deve indicar se é oficial, adaptada ou autoral** - Estado da regra.
7. **Classe deve indicar se é permitida na campanha** - Disponibilidade para jogadores.
8. **Classe deve se conectar a personagens** - Dataview lista personagens da classe.
9. **Classe deve se conectar a facções, itens e lore** - Quando fizer sentido narrativo.
10. **Disgraceland é apenas referência técnica/visual** - Não molde mecânico.

## Regra Crítica de Estados

Nunca use `status` nem `NoteStatus`.

Use sempre:

```yaml
work_status: Em desenvolvimento
rules_status: Official
campaign_status: Pending
canon_status: Draft
```

**Significados:**

- `work_status`: Estado editorial da nota (Em desenvolvimento, Active, Archived, Needs Review)
- `rules_status`: Relação com o sistema de regras (Official, Adapted, Homebrew, Pending Review)
- `campaign_status`: Disponibilidade na campanha (Allowed, Restricted, Pending, Banned, NPC Only)
- `canon_status`: Integração com o cânone/lore de Omnisvera (Draft, Reference, Confirmed, Deprecated)

## Valores Recomendados

### work_status

- `Em desenvolvimento` - Nota está sendo criada ou revisada
- `Active` - Nota está completa e em uso
- `Archived` - Nota não está mais em uso
- `Needs Review` - Nota precisa de revisão

### rules_status

- `Official` - Regra oficial do sistema de RPG (ex: Old Dragon 2E)
- `Adapted` - Regra oficial adaptada para Omnisvera
- `Homebrew` - Regra criada para Omnisvera
- `Pending Review` - Regra aguardando aprovação do Sage

### campaign_status

- `Allowed` - Classe disponível para jogadores
- `Restricted` - Classe disponível com restrições
- `Pending` - Classe aguardando aprovação para uso
- `Banned` - Classe não permitida na campanha
- `NPC Only` - Classe disponível apenas para NPCs

### canon_status

- `Draft` - Conteúdo em desenvolvimento, não confirmado
- `Reference` - Documento de referência, não cânone
- `Confirmed` - Conteúdo confirmado como cânone
- `Deprecated` - Conteúdo obsoleto

## Frontmatter Base para Classe

Todas as notas de Classe devem incluir este frontmatter base:

```yaml
---
type: class
subtype: base_class
work_status: Em desenvolvimento
rules_status: Official
campaign_status: Pending
canon_status: Draft
visibility: Mestre
created_by: Sage
requires_review: true

name:
aliases: []

system: Old Dragon 2E
source:
source_type: official

class_group:
primary_attribute:
hit_die:
armor_allowed:
weapons_allowed:
magic_type:

role_in_party:
narrative_role:

related_characters: []
related_factions: []
related_items: []
related_lore: []
related_races: []

thumbnail:
icon:
cover:

tags:
  - class
---
```

## Explicação dos Campos

### Campos de Tipo e Status

#### type
- **Tipo:** string
- **Valor:** `class`
- **Função:** Identifica a nota como Classe
- **Obrigatório:** Sim
- **Exemplo:** `type: class`

#### subtype
- **Tipo:** string
- **Valores:** `base_class`, `specialization`, `narrative_archetype`, `homebrew_class`, `legacy_class`
- **Função:** Define o subtipo de Classe
- **Obrigatório:** Sim
- **Exemplo:** `subtype: base_class`

#### work_status
- **Tipo:** string
- **Valores:** `Em desenvolvimento`, `Active`, `Archived`, `Needs Review`
- **Função:** Estado editorial da nota
- **Obrigatório:** Sim
- **Exemplo:** `work_status: Active`

#### rules_status
- **Tipo:** string
- **Valores:** `Official`, `Adapted`, `Homebrew`, `Pending Review`
- **Função:** Relação com o sistema de regras
- **Obrigatório:** Sim
- **Exemplo:** `rules_status: Official`

#### campaign_status
- **Tipo:** string
- **Valores:** `Allowed`, `Restricted`, `Pending`, `Banned`, `NPC Only`
- **Função:** Disponibilidade na campanha
- **Obrigatório:** Sim
- **Exemplo:** `campaign_status: Allowed`

#### canon_status
- **Tipo:** string
- **Valores:** `Draft`, `Reference`, `Confirmed`, `Deprecated`
- **Função:** Integração com o cânone/lore de Omnisvera
- **Obrigatório:** Sim
- **Exemplo:** `canon_status: Confirmed`

#### visibility
- **Tipo:** string
- **Valores:** `Mestre`, `Jogadores`, `Público`
- **Função:** Nível de acesso à nota
- **Obrigatório:** Sim
- **Exemplo:** `visibility: Jogadores`

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
- **Exemplo:** `requires_review: false`

### Campos de Identidade

#### name
- **Tipo:** string
- **Função:** Nome completo da Classe
- **Obrigatório:** Sim
- **Exemplo:** `name: Guerreiro`

#### aliases
- **Tipo:** array de strings
- **Função:** Lista de nomes alternativos (ex: edições anteriores)
- **Obrigatório:** Não
- **Exemplo:** `aliases: ["Homem de Armas"]`

### Campos de Sistema de Regras

#### system
- **Tipo:** string
- **Função:** Sistema de RPG
- **Obrigatório:** Sim
- **Exemplo:** `system: Old Dragon 2E`

#### source
- **Tipo:** string (URL ou wikilink)
- **Função:** Fonte da regra
- **Obrigatório:** Sim
- **Exemplo:** `source: https://olddragon.com.br/classes/guerreiro`

#### source_type
- **Tipo:** string
- **Valores:** `official`, `adapted`, `homebrew`
- **Função:** Tipo de fonte
- **Obrigatório:** Sim
- **Exemplo:** `source_type: official`

### Campos de Caracterização Mecânica

#### class_group
- **Tipo:** string
- **Valores:** `martial`, `magic`, `skill`, `hybrid`
- **Função:** Grupo da Classe
- **Obrigatório:** Não
- **Exemplo:** `class_group: martial`

#### primary_attribute
- **Tipo:** string
- **Função:** Atributo principal
- **Obrigatório:** Não
- **Exemplo:** `primary_attribute: Força`

#### hit_die
- **Tipo:** string
- **Função:** Dado de vida
- **Obrigatório:** Não
- **Exemplo:** `hit_die: 10`

#### armor_allowed
- **Tipo:** string
- **Função:** Armaduras permitidas
- **Obrigatório:** Não
- **Exemplo:** `armor_allowed: todas`

#### weapons_allowed
- **Tipo:** string
- **Função:** Armas permitidas
- **Obrigatório:** Não
- **Exemplo:** `weapons_allowed: todas`

#### magic_type
- **Tipo:** string
- **Função:** Tipo de magia
- **Obrigatório:** Não
- **Exemplo:** `magic_type: nenhum`

### Campos de Papel

#### role_in_party
- **Tipo:** string
- **Função:** Papel tático em aventura
- **Obrigatório:** Não
- **Exemplo:** `role_in_party: Tanque, dano corpo a corpo`

#### narrative_role
- **Tipo:** string
- **Função:** Papel social e narrativo
- **Obrigatório:** Não
- **Exemplo:** `narrative_role: Combatente experiente, protetor`

### Campos de Relações

#### related_characters
- **Tipo:** array de strings (wikilinks)
- **Função:** Personagens desta Classe
- **Obrigatório:** Não
- **Exemplo:** `related_characters: ["[[Vezemir]]"]`

#### related_factions
- **Tipo:** array de strings (wikilinks)
- **Função:** Facções que valorizam esta Classe
- **Obrigatório:** Não
- **Exemplo:** `related_factions: ["[[Guardiões do Véu Cinzento]]"]`

#### related_items
- **Tipo:** array de strings (wikilinks)
- **Função:** Itens típicos desta Classe
- **Obrigatório:** Não
- **Exemplo:** `related_items: ["[[Grisalma]]"]`

#### related_lore
- **Tipo:** array de strings (wikilinks)
- **Função:** Lore relacionado à Classe
- **Obrigatório:** Não
- **Exemplo:** `related_lore: ["[[Leth'valora]]"]`

#### related_races
- **Tipo:** array de strings (wikilinks)
- **Função:** Raças que se combinam bem
- **Obrigatório:** Não
- **Exemplo:** `related_races: ["[[Humano]]", "[[Meio-elfo]]"]`

### Campos de Mídia

#### thumbnail
- **Tipo:** string (caminho)
- **Função:** Imagem miniatura para cards e dashboards
- **Obrigatório:** Não, mas recomendado
- **Exemplo:** `thumbnail: zz_media/classes/th_guerreiro.png`

#### icon
- **Tipo:** string (emoji)
- **Função:** Ícone visual
- **Obrigatório:** Não
- **Exemplo:** `icon: ⚔️`

#### cover
- **Tipo:** string (caminho)
- **Função:** Imagem de banner ou capa
- **Obrigatório:** Não
- **Exemplo:** `cover: zz_media/classes/guerreiro.png`

### Campos de Tags

#### tags
- **Tipo:** array de strings
- **Função:** Tags auxiliares para filtros
- **Obrigatório:** Sim
- **Exemplo:** `tags: [class, martial, old-dragon-2]`

## Subtipos Oficiais

### base_class

Classe-base oficial do sistema de RPG.

- **Uso:** Classes fundamentais (Guerreiro, Ladrão, Mago, Clérigo)
- **Requisitos:** `rules_status: Official` ou `Adapted`
- **Exemplo:** Guerreiro, Ladrão

### specialization

Subclasse ou especialização de uma classe-base.

- **Uso:** Variações de classe (Paladino, Ranger, Assassino)
- **Requisitos:** Campo `parent_class` obrigatório
- **Exemplo:** Paladino (especialização de Guerreiro)

### narrative_archetype

Papel narrativo que não é classe mecânica.

- **Uso:** Papéis sociais e narrativos (Mercenário, Caçador de Ruínas)
- **Requisitos:** `rules_status: Homebrew`, `campaign_status: Pending`
- **Nota:** Não substitui Classe mecânica
- **Exemplo:** Mercenário, Guardião Exilado

### homebrew_class

Classe criada especificamente para Omnisvera.

- **Uso:** Classes originais da campanha
- **Requisitos:** `rules_status: Homebrew`
- **Exemplo:** (nenhum ainda)

### legacy_class

Classe de edição anterior mantida para compatibilidade.

- **Uso:** Termos legados (Homem de Armas)
- **Requisitos:** `canon_status: Reference`
- **Exemplo:** Homem de Armas

## Estrutura de Pastas

Classes são organizadas em:

```
Classes/
├── [Nome da Classe].md  # Classes-base
└── [Nome da Classe]/    # Especializações (se existirem)
    └── [Especialização].md
```

**Exemplos:**

- `Classes/Guerreiro.md` - Classe-base
- `Classes/Guerreiro/Paladino.md` - Especialização (se implementado)

## Seções Obrig para Classe Base

Todas as notas de Classe base devem incluir:

1. **Visão Geral** - Resumo da Classe
2. **Fonte e Estado da Regra** - Sistema, fonte e estado
3. **Identidade da Classe** - Como a Classe é vista no mundo
4. **Papel no Grupo** - Função tática em aventura
5. **Papel no Mundo** - Função social e narrativa
6. **Características Mecânicas** - PV, BA, JP, restrições
7. **Progressão** - Tabela de níveis ou resumo
8. **Habilidades de Classe** - Lista detalhada de habilidades
9. **Equipamentos Permitidos** - Armas, armaduras, itens
10. **Limitações** - O que a Classe não pode fazer
11. **Capacidades Narrativas** - Habilidades descritivas
12. **Relação com Raças** - Quais raças se combinam bem
13. **Relação com Facções** - Quais facções valorizam esta Classe
14. **Personagens desta Classe** - Dataview de personagens
15. **Especializações / Variações** - Subclasses se existirem
16. **Interpretação em Mesa** - Dicas de roleplay
17. **Diferenças em Omnisvera** - Adaptações da campanha
18. **Pendências do Sage** - Itens pendentes de confirmação
19. **Links relevantes** - Wikilinks para notas relacionadas

## Relação com Personagens

Personagens devem referenciar Classes com wikilink:

```yaml
class: "[[Guerreiro]]"
```

Para casos futuros de multiclasse, usar:

```yaml
classes:
  - "[[Guerreiro]]"
  - "[[Ladrão]]"
```

## Dataview para Personagens por Classe

**Uso:** Em notas de Classe para listar personagens desta Classe

```dataview
TABLE thumbnail, race, life_status, location, faction
FROM "Characters"
WHERE class = this.file.link OR contains(classes, this.file.link)
SORT file.name ASC
```

**Nota:** Esta consulta deve ser incluída em todas as notas de Classe.

**Nota:** Esta consulta precisa ser testada futuramente no Obsidian.

## Dataview para Especializações

**Uso:** Em notas de Classe base para listar especializações

```dataview
TABLE work_status, rules_status, campaign_status, canon_status
FROM "Classes"
WHERE parent_class = this.file.link
SORT file.name ASC
```

**Nota:** Esta consulta precisa ser testada futuramente no Obsidian.

## Referência Disgraceland

O vault Disgraceland (`Workflow/Legacy/Disgraceland/`) foi usado como referência técnica/visual para:

- Campo `role` no frontmatter (para papel narrativo separado de classe)
- Seção `Role In Disgraceland` (para função narrativa)
- Seção `Abilities` narrativa (para capacidades descritivas)
- Dataview com thumbnails (para dashboard de Classes)
- Uso de wikilinks em propriedades (para conexão com facções/religiões)

Disgraceland não possui estrutura formal de Classes e não deve servir como modelo mecânico.

## Documentos Relacionados

- `Workflow/OMNISVERA_NOTE_STANDARD.md` - Padrão geral de notas
- `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` - Esquema de frontmatter
- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` - Sistema de dashboards
- `Workflow/OMNISVERA_MEDIA_STANDARD.md` - Padrão de mídia
- `Templates/Classes/` - Templates prontos para cada subtipo
