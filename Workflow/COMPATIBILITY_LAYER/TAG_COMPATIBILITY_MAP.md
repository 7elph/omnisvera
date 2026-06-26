# Tag Compatibility Map

Tags antigas devem ser preservadas como ponte técnica. Elas podem alimentar Supercharged Links, cor de links, DataCards, Dataview e agrupamento visual.

Regra central: a coluna “remover agora?” é sempre “não”.

| tag antiga | função técnica | possível tag RPG | remover agora? | observação |
| --- | --- | --- | --- | --- |
| `loyalist` | Cor/link visual, agrupamento legado, possível consulta por tag. | `coroa-nimalia`, `faction`, tag de facção futura. | não | Preservar até existir equivalente configurado no Supercharged. |
| `rancher` | Cor/link visual, agrupamento legado. | `faction`, tag de facção rural/territorial futura. | não | Sem mapeamento narrativo final. |
| `third` | Cor/link visual, agrupamento legado. | `faction`, tag de grupo urbano/criminal futura. | não | Não remover sem revisar consultas. |
| `pirate` | Cor/link visual, agrupamento marítimo/legado. | `pirate`, `raider`, `faction`. | não | Pode continuar útil se houver piratas/bandidos. |
| `widow` | Cor/link visual, facção legado. | `faction`, tag de organização futura. | não | Preservar como ponte. |
| `murray` | Cor/link visual, família/grupo legado. | `house`, `clan`, `family`, tag de grupo futuro. | não | Pode virar padrão para casas/clãs. |
| `steeltown` | Cor/link visual, região/facção legado. | `region`, `settlement`, `faction`. | não | Preservar até definir equivalente geográfico. |
| `water` | Cor/link visual, tema/região legado. | `water`, `sea`, `region`. | não | Pode mapear para costa/mar/rio no futuro. |
| `story` | Narrativa/capítulo/card. | `session`, `chapter`, `story`. | não | Importante para ponte de capítulos/sessões. |
| `individual` | Personagem individual no legado. | `character`, `npc`, `player`. | não | Pode coexistir com `character`. |
| `lore` | Tipo de nota e visual. | `lore`. | não | Deve permanecer; é compatível com RPG. |
| `religion` | Tipo de nota e visual. | `religion`, `cult`. | não | Deve permanecer; pode receber subtag futura. |
| `territory` | Tipo de nota e visual. | `territory`, `region`, `kingdom`. | não | Deve permanecer; é compatível com RPG. |

## Tags RPG novas permitidas

Estas tags podem ser adicionadas em paralelo, sem remover as antigas:

- `character`
- `player`
- `npc`
- `npc-important`
- `npc-minor`
- `antagonist`
- `faction`
- `territory`
- `region`
- `location`
- `settlement`
- `session`
- `quest`
- `hook`
- `handout`
- `lore`
- `religion`
- `public`
- `secret`

## Regra para Supercharged Links

- Não editar `supercharged-links-gen.css` diretamente.
- Criar/alterar visual por Supercharged Links e Style Settings.
- Adicionar tags novas antes de alterar consultas.
- Validar links coloridos no Obsidian depois de qualquer mudança.

## Regra para Dataview/DataCards

- Não quebrar consultas `FROM #tag`.
- Quando uma tag RPG substituir uma antiga no futuro, manter consulta temporária com ambas.
- Exemplo futuro:

```dataview
TABLE thumbnail, status, faction
FROM #character OR #individual
SORT file.name ASC
```
