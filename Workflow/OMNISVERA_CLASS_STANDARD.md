# Omnisvera — Padrão de Classes

> [!IMPORTANT]
> Este documento segue a taxonomia oficial atual do Sage.
> Fonte da verdade: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].

## Função

Define o padrão operacional para classes de RPG em Omnisvera.

Classes novas devem usar `Classes/`.

`Classes/` é a pasta operacional oficial. A pasta `Rules/Classes` foi removida para evitar duplicação.

## Frontmatter recomendado

```yaml
---
type: class
status: Rascunho
rules_status:
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
level:
danger_level:

thumbnail:
cover:
chapters: []

tags:
  - classe
  - old-dragon
---
```

## Campos

| campo | uso |
|---|---|
| `type` | Filtro auxiliar. Valor esperado: `class`. |
| `status` | Estado geral da nota. |
| `rules_status` | Estado da regra: oficial, adaptada, caseira ou pendente. |
| `campaign_status` | Uso atual na campanha. |
| `visibility` | Mestre, Jogadores ou Público. |
| `spoiler_level` | Risco de spoiler. |
| `gm_secret` | Se contém informação restrita ao mestre. |
| `revealed_in` | Capítulo ou momento em que foi revelado. |
| `created_by` | Autor/responsável pela nota. |
| `level` | Nível ou faixa mecânica quando fizer sentido. |
| `danger_level` | Risco narrativo/mecânico associado. |
| `thumbnail` | Imagem pequena para cards. |
| `cover` | Imagem ampla/capa. |
| `chapters` | Capítulos, partes ou crônicas relacionadas. |
| `tags` | Infraestrutura técnica e visual. |

## Estrutura da nota

```md
# Nome da Classe

## Visão Geral

## Papel no Grupo

## Papel no Mundo

## Notas de Mecânica

## Personagens relacionados
```

## Consulta de personagens relacionados

```dataview
TABLE thumbnail, race, status, location, faction
FROM "Characters"
WHERE class = this.file.link
SORT file.name ASC
```

## Índice de classes

```dataview
TABLE thumbnail, status, rules_status, campaign_status
FROM "Classes"
WHERE type = "class"
SORT file.name ASC
```

## Regras de conteúdo protegido

Não copiar texto integral de livros, sites pagos ou materiais protegidos.

Notas de classe devem conter:

- resumo próprio;
- campos de controle;
- interpretação para Omnisvera;
- referência breve à origem quando necessário, sem reprodução extensa.

## Pendências

- Manter `Classes/` como pasta oficial até uma eventual migração futura para português BR.
- Não recriar `Rules/Classes`.
