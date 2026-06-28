# Omnisvera — Guia de Visibilidade e Spoiler

Fonte da verdade relacionada: [[OMNISVERA_SYSTEM_TAXONOMY]]

## Campos usados

| Campo | Uso |
|---|---|
| `visibility` | Define se a nota é do Mestre, Jogadores ou Público |
| `spoiler_level` | Define intensidade do spoiler |
| `gm_secret` | Define se o conteúdo é segredo do mestre |

## Valores oficiais

| Campo | Valores |
|---|---|
| `visibility` | Mestre / Jogadores / Público |
| `spoiler_level` | none / light / medium / heavy |
| `gm_secret` | true / false |

## Regra prática

| Tipo de conteúdo | visibility | spoiler_level | gm_secret |
|---|---|---|---|
| Conteúdo seguro para jogadores | Público | none | false |
| Conteúdo conhecido pelo grupo | Jogadores | light | false |
| Conteúdo do mestre | Mestre | medium | true |
| Segredo central da campanha | Mestre | heavy | true |
| Rumor liberável | Jogadores | light | false |
| Nota técnica do mestre | Mestre | none | true |

## Regra da Home dos Jogadores

A Home dos Jogadores só deve mostrar notas com:

```dataview
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
```

## Campos rejeitados

Não usar como padrão novo:

- `player_known`
- `sessions`
- `life_status`
- `handout_image`
