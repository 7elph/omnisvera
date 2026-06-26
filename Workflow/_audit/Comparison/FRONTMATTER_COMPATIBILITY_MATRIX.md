# Frontmatter Compatibility Matrix

Matriz de compatibilidade entre campos do Disgraceland, campos desejados no modelo RPG e campos observados no Omnisvera atual.

Legenda curta:

- `sim`: presente/funcional na camada.
- `parcial`: presente com uso incompleto, irregular ou sem contrato.
- `não`: não observado como campo funcional.
- `desejado`: proposto no modelo RPG, mas não aplicado.

| campo | Disgraceland | RPG desejado | Omnisvera atual | uso técnico | risco | recomendação futura |
| --- | --- | --- | --- | --- | --- | --- |
| `obsidianUIMode` | sim | herdado | sim | Define modo de abertura/visual. | Baixo/médio | Preservar em notas que já usam. |
| `NoteIcon` | sim | herdado | sim | Ícones e convenção visual. | Médio | Não remover sem validar Icon Folder/snippets. |
| `NoteStatus` | sim | herdado/adaptado | sim | Estado editorial/template. | Médio | Manter até existir status editorial novo. |
| `type` | raro | desejado | parcial | Tipo técnico de nota. | Médio | Usar como ponte futura, sem substituir tags agora. |
| `subtype` | não | desejado | parcial | Subtipo RPG. | Médio | Contratar valores permitidos antes de lote. |
| `status` | sim | desejado | sim | Estado narrativo/operacional em cards. | Alto | Não renomear sem atualizar Dataview/DataCards. |
| `life_status` | não | desejado | parcial | Vida/morte/desaparecido. | Médio | Padronizar sem apagar `status`. |
| `visibility` | não | desejado | parcial | Controle mestre/jogador. | Alto | Definir enum antes de dashboard público. |
| `canon_status` | não | desejado | não | Canon, rascunho, legado. | Médio | Campo útil, precisa decisão. |
| `spoiler_level` | não | desejado | não | Gravidade do segredo. | Alto | Criar antes de filtros de jogador. |
| `player_known` | não | desejado | não | Se jogadores conhecem. | Alto | Criar junto com `visibility`. |
| `gm_secret` | não | desejado | não | Segredo do mestre. | Alto | Evitar usar em cards sem filtro. |
| `thumbnail` | sim | herdado crítico | sim | DataCards/personagens/facções. | Alto | Não trocar por `cover` sem camada de compatibilidade. |
| `cover` | sim | herdado crítico | sim | Cards, Home, territórios, lore. | Alto | Manter como campo separado de `thumbnail`. |
| `portrait` | não | desejado | parcial/desconhecido | Retrato principal RPG. | Médio | Pode complementar, não substituir `thumbnail`. |
| `map_image` | não | desejado | não | Imagem base de mapa. | Alto | Criar depois de validar Leaflet. |
| `handout_image` | não | desejado | não | Imagem liberada para jogadores. | Alto | Exige `handout_status`/visibilidade. |
| `token_image` | não | desejado | não | Token de VTT/mesa. | Médio | Novo campo opcional. |
| `location` | sim | desejado | sim | Local atual/origem, Dataview. | Alto | Preservar e normalizar depois. |
| `territory` | sim | desejado | sim | Território/região em cards e consultas. | Alto | Não colapsar com `region` sem plano. |
| `region` | sim em territórios | desejado | sim/parcial | Região ampla. | Médio | Definir hierarquia `territory`/`region`. |
| `district` | sim | desejado | sim/parcial | Distrito/local menor. | Médio | Preservar onde existe. |
| `faction` | sim | desejado | sim | Facção, cards, agrupamento. | Alto | Não substituir por tag sem ponte. |
| `religion` | sim | desejado | sim/parcial | Religião/culto. | Médio | Separar religião, culto e crença se necessário. |
| `role` | sim | desejado | sim/parcial | Papel narrativo. | Médio | Preservar em personagens. |
| `chapters` | sim crítico | herdado/ponte | sim | Aparições por capítulo. | Alto | Não remover antes de `sessions` compatível. |
| `sessions` | não | desejado | não | Aparições por sessão RPG. | Alto | Criar ponte com `chapters`. |
| `arcs` | não | desejado | não/parcial | Arcos de campanha. | Médio | Novo campo após taxonomia de sessão. |
| `tags` | sim crítico | crítico | sim | Supercharged, Dataview, DataCards, organização. | Alto | Não remover/renomear em lote. |
| `cssclasses` | sim/parcial | herdado | sim | CSS por nota. | Alto visual | Preservar até auditoria visual. |
| `banner` | sim | herdado visual | sim | Home/dashboard/capas. | Médio | Preservar. |
| `banner-x` | sim | herdado visual | sim | Ajuste visual de banner. | Médio | Preservar. |
| `banner-y` | sim | herdado visual | sim | Ajuste visual de banner. | Médio | Preservar. |
| `banner-height` | sim | herdado visual | sim | Altura do banner. | Médio | Preservar. |
| `content-start` | sim | herdado visual | sim | Layout com banner. | Médio | Preservar. |
| `banner-fade` | sim | herdado visual | sim | Fade do banner. | Médio | Preservar. |
| `date` | sim | desejado | sim/parcial | Capítulos, sessões, cards. | Médio | Definir formato por tipo. |
| `description` | sim | desejado | sim/parcial | Resumo em cards. | Médio | Manter para DataCards. |
| `info` | sim | desejado | sim/parcial | Resumo curto de locais/lore. | Médio | Não remover sem ajustar cards. |
| `leader` | sim | desejado | sim/parcial | Facções/territórios. | Médio | Preservar. |
| `population` | sim | desejado | sim/parcial | Territórios/assentamentos. | Médio | Preservar. |
| `old_dragon_class` | não | desejado | não | Mecânica de personagem. | Médio | Decidir se entra no YAML. |
| `old_dragon_race` | não | desejado | não | Mecânica de raça. | Médio | Decidir se entra no YAML. |
| `level` | não | desejado | parcial | Nível do personagem. | Médio | Padronizar com sistema Old Dragon. |
| `danger_level` | não | desejado | não | Perigo de encontro/antagonista/local. | Médio | Criar apenas após template. |
| `hooks` | não | desejado | não | Ganchos conectados. | Médio | Pode ser campo ou notas próprias. |
| `rumors` | não | desejado | não | Rumores disponíveis. | Médio | Decidir entre lista YAML e template Rumor. |

## Campos críticos em conflito

- `thumbnail` versus `cover`: ambos têm usos técnicos distintos e não devem ser unificados sem atualizar DataCards.
- `chapters` versus `sessions`: `chapters` é funcional hoje; `sessions` é desejado, mas ausente.
- `status` versus `life_status`: `status` é amplo; `life_status` é específico para vida/morte e precisa coexistir até estabilizar.
- `visibility` parcial versus ausência de `spoiler_level`, `player_known`, `gm_secret`: não há filtro seguro completo para jogador.
- `type`/`subtype` parcial versus tags: campos novos não substituem tags visuais ainda.
