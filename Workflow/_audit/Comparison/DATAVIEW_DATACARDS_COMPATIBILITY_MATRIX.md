> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Dataview and DataCards Compatibility Matrix

Comparação das dependências de consulta entre Disgraceland, modelo RPG desejado e Omnisvera atual.

## Resumo quantitativo

| camada | Dataview | DataCards | observação |
| --- | ---: | ---: | --- |
| Disgraceland | 84 | 37 | Sistema original muito orientado por consultas. |
| Omnisvera atual | 41 | 18 | Consultas preservadas em menor volume. |
| RPG desejado | Conceitual | Conceitual | Precisa consultas por sessão, visibilidade, quest, rumor e handout. |

## Matriz de dependências

| dependência | Disgraceland | RPG desejado | Omnisvera atual | risco | ponte necessária |
| --- | --- | --- | --- | --- | --- |
| `thumbnail` | Campo central para cards de personagens/facções. | Manter para cards compactos. | Usado por Dataview/DataCards. | Alto | Não substituir por `portrait` sem compatibilidade. |
| `cover` | Campo central para cards de lore/território/local. | Manter para cards grandes e banners. | Usado por DataCards. | Alto | Não unificar com `thumbnail`. |
| `chapters` | Aparições por capítulo. | Ponte para `sessions`. | Ainda presente; `sessions` ausente. | Alto | Criar consulta que aceite ambos. |
| `sessions` | Ausente. | Campo desejado para RPG. | Ausente. | Alto | Adicionar sem remover `chapters`. |
| `tags` | Supercharged, `FROM #tag`, Home. | Tipo, facção, região, visibilidade. | Presentes e críticas. | Alto | Adicionar tags RPG sem remover antigas. |
| `location` | Personagens/locais. | Consulta por localização. | Presente. | Médio/alto | Normalizar valores. |
| `territory` | Territórios/locais/personagens. | Região/reino/local. | Presente. | Médio/alto | Definir hierarquia com `region`. |
| `faction` | Personagens/facções. | Agrupamento de facção. | Presente. | Alto | Manter campo mesmo que tags existam. |
| `status` | Cards e listas. | Estado narrativo/operacional. | Presente. | Alto | Separar de `life_status` sem quebrar cards. |
| `date` | Capítulos/Story. | Sessões/calendário. | Presente parcial. | Médio | Definir formato e granularidade. |
| `description` | Cards de história/lore. | Resumo de dashboard. | Presente parcial. | Médio | Preservar para DataCards. |
| Pastas | `from "Characters"`, `from "DISGRACELAND"`. | Consultas por tipo e pasta RPG. | Consultas por pastas atuais. | Alto | Evitar mover pastas antes de atualizar queries. |
| `FROM #tag` | Muito usado com tags visuais. | Deve continuar, mas com tags RPG. | Ainda relevante. | Alto | Tags antigas e novas precisam coexistir. |
| `from "Characters"` | Consulta personagens. | Personagens por subtipo. | Ainda existe. | Médio | Pode precisar filtro `type/subtype`. |
| `from "DISGRACELAND"` | Capítulos legados. | Substituir por sessões/arcos futuramente. | Não é destino final. | Alto | Não remover até consultas novas existirem. |

## Consultas RPG necessárias

Estas consultas ainda devem ser desenhadas antes de migração:

- Personagens por facção.
- Personagens por região/território.
- NPCs vivos, mortos ou desaparecidos.
- Aparições por sessão/capítulo aceitando `chapters` e `sessions`.
- Facções ativas.
- Locais por território.
- Quests abertas.
- Rumores disponíveis.
- Handouts liberados.
- Segredos ainda não revelados.
- Sessões por arco.
- Imagens por tipo e status.

## Riscos específicos

- Cards quebram se `imageProperty` apontar para campo não preenchido.
- Dashboards podem vazar segredo se consultarem `FROM #secret` ou notas sem filtro de `visibility`.
- Mover `Characters`, `Factions`, `Territories` ou `Locations` antes de atualizar queries quebra blocos por pasta.
- Trocar tags antigas por novas de uma vez quebra `FROM #tag` e Supercharged Links.

## Ponte mínima recomendada

Documentalmente, a ponte futura deve aceitar:

- `thumbnail` e `cover` como campos distintos.
- `chapters` e `sessions` durante transição.
- tags antigas e tags RPG simultaneamente.
- `status` e `life_status` simultaneamente.
- filtros explícitos de `visibility` antes de qualquer dashboard para jogador.
