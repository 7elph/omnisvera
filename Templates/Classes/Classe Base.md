---
type: class
status: Rascunho
rules_status: Official
campaign_status: Em revisao
visibility: Mestre
spoiler_level: medium
gm_secret: true
revealed_in:
created_by: Sage

name:
aliases: []

system: Old Dragon 2E
class_group:
primary_attribute:
hit_die:
armor_allowed:
weapons_allowed:
magic_type:

role_in_party:
narrative_role:
danger_level:

related_characters: []
related_factions: []
related_items: []
related_lore: []
related_races: []

thumbnail:
cover:
chapters: []

tags:
  - classe
  - old-dragon
---

# Nome da Classe

> [!WARNING] Estado da classe
> Esta nota separa regra, uso em campanha e integração narrativa em Omnisvera.

## Visão Geral

<!-- Resumo da classe em 2-3 parágrafos -->

## Estado da Regra

| Campo | Informação |
|---|---|
| Sistema |  |
| Estado da regra |  |
| Disponibilidade na campanha |  |
| Integração com cânone |  |

## Identidade da Classe

<!-- Como a classe é vista no mundo de Omnisvera -->

## Papel no Grupo

<!-- Função tática em aventura -->

## Papel no Mundo

<!-- Função social e narrativa na sociedade -->

## Requisitos / Tendências

<!-- Atributos recomendados, restrições de raça, etc. -->

## Características Mecânicas

| Campo | Valor |
|---|---|
| Pontos de Vida |  |
| Base de Ataque |  |
| Jogada de Proteção |  |

## Progressão

<!-- Tabela de níveis ou resumo de evolução -->

## Habilidades de Classe

<!-- Lista detalhada de habilidades por nível -->

## Equipamentos Permitidos

<!-- Armas, armaduras, itens mágicos -->

## Limitações

<!-- O que a classe não pode fazer -->

## Capacidades Narrativas

<!-- Habilidades descritivas separadas de mecânicas -->

## Relação com Raças

<!-- Quais raças se combinam bem -->

## Relação com Facções

<!-- Quais facções valorizam esta classe -->

## Personagens desta Classe

```dataview
TABLE thumbnail, race, status, location, faction
FROM "Characters"
WHERE class = this.file.link OR contains(classes, this.file.link)
SORT file.name ASC
```

## Especializações / Variações

<!-- Subclasses ou variantes (se existirem) -->

```dataview
TABLE rules_status, campaign_status, visibility, danger_level
FROM "Classes"
WHERE parent_class = this.file.link
SORT file.name ASC
```

## Interpretação em Mesa

<!-- Dicas de roleplay para jogadores -->

## Diferenças em Omnisvera

<!-- Adaptações específicas da campanha -->

## Pendências do Sage

<!-- Itens pendentes de confirmação -->

## Links relevantes

<!-- Wikilinks para notas relacionadas -->

## Uso em Mesa

- Como apresentar:
- O que os jogadores sabem:
- O que apenas o mestre sabe:
- Como entra em cena:
- Ganchos:
- Consequências possíveis:
