> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Player and Master Visibility Gap

Análise específica da separação entre informação do mestre e informação dos jogadores.

## Estado comparado

| camada | modelo de visibilidade |
| --- | --- |
| Disgraceland | Não tinha necessidade central de separar mestre/jogador. Tags e cards eram mais narrativos/visuais. |
| RPG desejado | Precisa distinguir público, conhecido pelos jogadores, segredo do mestre, revelação futura, spoiler e handout liberado. |
| Omnisvera atual | Campo `visibility` aparece parcialmente, mas o contrato completo não está consolidado. |

## Campos esperados

| campo | RPG desejado | Omnisvera atual | status | risco |
| --- | --- | --- | --- | --- |
| `visibility` | Mestre/Jogadores/Público ou equivalente. | Parcial. | suporta parcialmente | Alto se valores não forem padronizados. |
| `spoiler_level` | `none`, `light`, `medium`, `heavy`. | Ausente. | precisa campo novo | Alto para dashboard público. |
| `player_known` | Booleano para conhecimento dos jogadores. | Ausente. | precisa campo novo | Alto para handouts/segredos. |
| `gm_secret` | Campo ou bloco para segredo do mestre. | Ausente. | precisa campo novo | Alto se consultado sem filtro. |
| `revealed_in` | Sessão/capítulo onde foi revelado. | Ausente. | precisa campo novo | Médio/alto para continuidade. |
| `handout_status` | Liberado, bloqueado, rascunho. | Ausente. | precisa campo novo | Alto para mídia. |
| `gm_notes` | Observações internas. | Ausente/parcial. | precisa decisão | Alto se misturado ao corpo público. |

## Riscos identificados

- Dashboard sem filtro pode listar notas secretas.
- DataCards por `#character`, `#location` ou `#lore` podem revelar conteúdo que deveria ser do mestre.
- Handouts podem ser publicados antes da hora se não houver `handout_status`.
- Mídia secreta pode aparecer por `cover` ou `thumbnail`.
- `visibility` isolado não resolve tudo se `player_known`, `spoiler_level` e `revealed_in` não existirem.
- Tags como `secret` e `public` podem ajudar, mas não substituem campos se forem usadas também para visual.

## Modelo mínimo futuro

Antes de criar dashboard para jogadores, o vault precisa de um contrato mínimo:

| uso | campo mínimo | observação |
| --- | --- | --- |
| Nota pública | `visibility: Público` | Pode aparecer em cards de jogadores. |
| Nota conhecida pelo grupo | `visibility: Jogadores` e/ou `player_known: true` | Exige consenso de valores. |
| Nota de mestre | `visibility: Mestre` | Nunca entra em consulta pública. |
| Segredo futuro | `spoiler_level` + `revealed_in` vazio | Não deve aparecer em Home pública. |
| Handout liberado | `handout_status: liberado` | Pode aparecer em dashboard de jogadores. |
| Mecânica interna | `visibility: Mestre` ou bloco dedicado | Evitar exposição acidental. |

## Regra de segurança

Até existir contrato de visibilidade, qualquer dashboard deve ser tratado como dashboard do mestre. Criar visualização para jogadores antes disso é risco técnico de vazamento.
