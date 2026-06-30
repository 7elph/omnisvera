# Omnisvera — Sistema de Dashboards

> [!IMPORTANT]
> Este documento segue a taxonomia oficial atual do Sage.
> Fonte da verdade: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].

## Função

Define como dashboards operacionais devem funcionar no vault Omnisvera.

Este arquivo é documentação técnica. Ele não é Home operacional.

## Homes oficiais

| arquivo | função |
|---|---|
| `Home.md` | Home dos Jogadores. |
| `Home_Mestre.md` | Área/dashboard do Mestre. |

`Home_Jogadores.md` não existe mais na raiz. A Home dos jogadores é `Home.md`.

O plugin Homepage deve abrir `Home`.

## Regra de segurança para dashboards

Dashboards de jogador devem ser conservadores.

Uma consulta pública só deve exibir notas com:

```dataview
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
```

Dashboards do mestre podem exibir conteúdo de preparação, pendências e relatórios técnicos.

## Campos aceitos em dashboards

Campos recomendados:

- `thumbnail`;
- `cover`;
- `status`;
- `visibility`;
- `spoiler_level`;
- `gm_secret`;
- `revealed_in`;
- `campaign_status`;
- `quest_status`;
- `handout_status`;
- `level`;
- `danger_level`;
- `hooks`;
- `rumors`;
- `chapters`;
- `date`;
- `description`;
- `location`;
- `territory`;
- `district`;
- `faction`;
- `religion`;
- `role`;
- `leader`;
- `population`;
- `region`.

`type` pode ser usado como filtro auxiliar, mas não é obrigatório em todas as notas existentes.

## Capítulos e crônicas

`chapters` é o eixo funcional para capítulos, story e partes jogadas da campanha.

Exemplo:

```dataview
TABLE date, description
FROM #story
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT date ASC
```

## Personagens dos jogadores

```dataview
TABLE thumbnail, status, location, territory, faction
FROM "Characters"
WHERE contains(tags, "player") OR contains(tags, "jogador")
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Territórios

A tag visual oficial para territórios é `territorio`.

```dataview
TABLE cover, region, leader, population
FROM "Territories"
WHERE NoteStatus != "Placeholder"
SORT file.name ASC
```

## Religiões

A tag visual oficial para religiões é `religiao`.

```dataview
TABLE cover, status, description
FROM #religiao
SORT file.name ASC
```

## Classes

Classes operacionais devem ficar em `Classes`.

```dataview
TABLE thumbnail, status, rules_status, campaign_status
FROM "Classes"
WHERE type = "class"
SORT file.name ASC
```

## Raças

Raças operacionais devem ficar em `Races`.

```dataview
TABLE thumbnail, status, campaign_status, visibility
FROM "Races"
WHERE type = "race"
SORT file.name ASC
```

## Tags visuais oficiais migradas

| função | tag atual |
|---|---|
| Personagem | `personagem` |
| Território | `territorio` |
| Religião | `religiao` |
| Coroa de Nimalia | `coroa-de-nimalia` |
| Guilda dos Mercadores | `guilda-dos-mercadores` |
| Conclave dos Errantes | `conclave-dos-errantes` |
| Guardiões do Véu Cinzento | `guardioes-do-veu-cinzento` |
| Sentinelas de Leth'valora | `sentinelas-de-lethvalora` |
| Nobreza de Nimalia | `nobreza-de-nimalia` |
| Mar da Neblina | `mar-da-neblina` |
| Nimalia | `nimalia` |

`story` permanece como tag operacional temporária para história/capítulo/campanha. Não converter para `sessions`.

## Regras de manutenção

- Não exibir relatórios de legado na Home dos jogadores.
- Não tratar documentação histórica como dashboard operacional.
- Não depender de campos ausentes em massa.
- Não remover `thumbnail`, `cover`, `status`, `chapters` ou `tags`.
- Não renomear pastas sem atualizar Dataview, DataCards, links e plugins.
