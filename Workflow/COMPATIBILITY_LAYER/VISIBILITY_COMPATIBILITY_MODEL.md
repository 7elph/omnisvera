> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Visibility Compatibility Model

Este modelo define como Omnisvera deve separar informação de mestre, jogadores e material público sem quebrar a compatibilidade atual.

## Campos aprovados

```yaml
visibility:
spoiler_level:
player_known:
gm_secret:
revealed_in:
```

## Valores sugeridos

| campo | valores iniciais | função |
| --- | --- | --- |
| `visibility` | `Mestre`, `Jogadores`, `Público` | Define quem pode ver a nota ou card. |
| `spoiler_level` | `none`, `light`, `medium`, `heavy` | Define gravidade do segredo. |
| `player_known` | `true`, `false` | Indica se os jogadores já sabem. |
| `gm_secret` | `true`, `false` | Marca conteúdo de mestre. |
| `revealed_in` | link/texto de sessão ou vazio | Indica quando foi revelado. |

## Valor inicial seguro

Para notas ainda não classificadas:

```yaml
visibility: Mestre
spoiler_level: heavy
player_known: false
gm_secret: true
revealed_in:
```

Isto evita exposição acidental em dashboards públicos.

## Regras para Home/dashboard

- Home atual = dashboard do mestre.
- Dashboard de jogador só deve existir com filtro explícito.
- DataCards públicos precisam filtrar `visibility`.
- Segredos não devem aparecer em consultas gerais.
- Conteúdo sem `visibility` deve ser tratado como `Mestre` por padrão.

## Regra para dashboards públicos

Um card público só deve aparecer se passar em pelo menos uma condição segura:

- `visibility = "Público"`
- `visibility = "Jogadores"`
- `player_known = true`
- `handout_status = "released"` em modelo futuro de handout

## Exemplo Dataview conceitual seguro

```dataview
TABLE thumbnail, status, location
FROM "Characters"
WHERE contains(tags, "character")
AND (visibility = "Público" OR visibility = "Jogadores" OR player_known = true)
SORT file.name ASC
```

## Exemplo DataCards conceitual seguro

```dataview
TABLE cover, description
FROM #lore
WHERE visibility = "Público" OR player_known = true
SORT file.name ASC
```

## Regras para segredo

- `gm_secret: true` nunca deve aparecer em dashboard de jogador.
- `spoiler_level: heavy` deve ficar restrito ao mestre.
- `revealed_in` vazio indica que ainda não foi revelado.
- `player_known: false` impede exibição pública.

## Regra de compatibilidade

Enquanto notas antigas não tiverem esses campos, elas devem ser consideradas privadas ao mestre. A ausência de campo não deve ser interpretada como público.
