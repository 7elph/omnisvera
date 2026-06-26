# Dataview Compatibility Rules

Estas regras definem como criar ou alterar consultas Dataview sem quebrar compatibilidade com Disgraceland e com o Omnisvera atual.

## Regras centrais

- Preservar consultas por `chapters`.
- Criar consultas futuras que aceitem `sessions`.
- Não quebrar consultas `FROM #tag`.
- Não remover tags antigas.
- Não alterar pastas sem atualizar consultas.
- Não depender exclusivamente de campos que ainda não existem em massa.
- Para dashboards de jogador, filtrar visibilidade explicitamente.

## Consulta herdada segura

```dataview
TABLE status, location, faction
FROM "Characters"
WHERE contains(tags, "character")
SORT file.name ASC
```

## Consulta futura com `sessions`

```dataview
TABLE status, location, faction, sessions
FROM "Characters"
WHERE contains(tags, "character")
SORT file.name ASC
```

## Consulta compatível com tags antigas e novas

```dataview
TABLE thumbnail, status, faction
FROM "Characters"
WHERE contains(tags, "character") OR contains(tags, "individual")
SORT file.name ASC
```

## Consulta pública segura

```dataview
TABLE thumbnail, status, location
FROM "Characters"
WHERE contains(tags, "character")
AND (visibility = "Público" OR visibility = "Jogadores" OR player_known = true)
SORT file.name ASC
```

## Aparições por capítulo/sessão

Durante transição, não remover `chapters`. Consultas futuras devem aceitar os dois conceitos.

Modelo de frontmatter:

```yaml
chapters:
  - 01 - Nome do Capítulo
sessions:
  - Sessão 01
```

## Regras por campo

| campo | regra |
| --- | --- |
| `chapters` | Preservar em consultas herdadas. |
| `sessions` | Adicionar em consultas novas sem remover `chapters`. |
| `tags` | Continuar aceitando tags antigas e novas. |
| `thumbnail` | Usar para cards/listagens compactas. |
| `cover` | Usar para cards amplos/lore/territórios. |
| `visibility` | Obrigatório em dashboard de jogador. |
| `status` | Não substituir por `life_status`. |
| `life_status` | Complementar para personagens. |
| `type/subtype` | Usar como filtro estrutural novo, não como substituto imediato de tags. |

## Anti-padrões

- `FROM #npc` sem manter ponte com tags antigas quando necessário.
- Consulta pública sem filtro de `visibility`.
- Consulta que assume `sessions` preenchido em todas as notas.
- Consulta que usa `portrait` como imagem de card sem fallback para `thumbnail`.
- Consulta por pasta depois de mover notas sem atualizar `FROM`.
