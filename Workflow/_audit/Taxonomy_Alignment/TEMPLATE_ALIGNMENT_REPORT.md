# Relatório de Alinhamento de Templates

Data: 2026-06-27

Fonte da verdade:

- `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md`
- `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md`

## Escopo

Templates auditados em:

- `Templates/Characters`;
- `Templates/Classes`;
- `Templates/RPG`.

## Resultado

Os templates ativos já estavam alinhados com a taxonomia aplicada na etapa anterior.

Não foram feitas alterações em `Templates/` nesta etapa.

## Campos rejeitados

Busca por campos rejeitados nos templates ativos não encontrou recomendações de:

- `sessions`;
- `player_known`;
- `subtype`;
- `portrait`;
- `token_image`;
- `map_image`;
- `handout_image`;
- `life_status`;
- `old_dragon_class`;
- `old_dragon_race`;
- `requires_review`;
- `work_status`;
- `canon_status`;
- `source`;
- `state`.

## Ocorrências justificadas

| ocorrência | arquivos | justificativa |
|---|---|---|
| `territory` | templates de personagens, monstro, quest, raça e rumor | Campo herdado preservado pela taxonomia. Não é tag antiga. |
| `religion` | template de raça | Campo herdado preservado pela taxonomia. Não é tag antiga. |

## Estado por grupo

| grupo | status | observação |
|---|---|---|
| `Templates/Characters` | alinhado | Usa `thumbnail`, `cover`, `chapters`, `visibility`, `spoiler_level`, `gm_secret`, `campaign_status`. |
| `Templates/Classes` | alinhado | Usa `Classes` como destino operacional oficial. |
| `Templates/RPG` | alinhado | Templates de raça, classe, magia, item, monstro, quest e rumor seguem a taxonomia atual. |

## Pendências

- Decidir em etapa futura se `territory` e `religion` continuarão em inglês ou serão substituídos por campos em português.
- Não renomear campos herdados sem lote piloto e validação de Dataview/DataCards.
