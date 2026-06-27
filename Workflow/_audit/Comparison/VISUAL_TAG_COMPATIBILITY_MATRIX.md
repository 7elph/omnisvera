> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Visual Tag Compatibility Matrix

Comparação das tags visuais herdadas de Disgraceland, possíveis tags RPG futuras e estado observado no Omnisvera atual.

## Tags Supercharged herdadas

| tag | Disgraceland | Omnisvera atual | uso DataCards/Dataview | semântica atual | risco se removida | equivalente RPG provável |
| --- | --- | --- | --- | --- | --- | --- |
| `steeltown` | Visual/grupo legado. | Configurada. | Possível. | Facção/região Disgraceland. | Alto visual. | Região/facção futura, se houver. |
| `individual` | Visual para personagem individual. | Configurada. | Possível. | Tipo/personagem legado. | Alto visual. | `character` ou `npc`. |
| `lore` | Tipo de nota e visual. | Configurada. | Sim/provável. | Lore. | Alto. | `lore`. |
| `religion` | Tipo de nota e visual. | Configurada. | Sim/provável. | Religião. | Alto. | `religion` ou `cult`. |
| `territory` | Tipo de nota e visual. | Configurada. | Sim/provável. | Território. | Alto. | `territory`/`region`. |
| `loyalist` | Facção visual. | Configurada. | Possível. | Facção Disgraceland. | Alto. | Facção RPG a definir. |
| `widow` | Facção visual. | Configurada. | Possível. | Facção Disgraceland. | Alto. | Facção RPG a definir. |
| `pirate` | Facção visual. | Configurada. | Possível. | Facção Disgraceland. | Alto. | Facção marítima/bandido, se existir. |
| `rancher` | Facção visual. | Configurada. | Possível. | Facção Disgraceland. | Alto. | Facção RPG a definir. |
| `third` | Facção visual. | Configurada. | Possível. | Facção Disgraceland. | Alto. | Facção RPG a definir. |
| `murray` | Família/grupo visual. | Configurada. | Possível. | Grupo Disgraceland. | Alto. | Casa/clã/família futura. |
| `water` | Grupo/tema visual. | Configurada. | Possível. | Semântica legada. | Alto. | Região/elemento futura. |
| `story` | Capítulo/história. | Configurada. | Sim/provável. | Narrativa/capítulo. | Alto. | `session` ou `story`. |

## Tags RPG propostas

| tag | função desejada | existe tecnicamente? | deve ter cor? | observação |
| --- | --- | --- | --- | --- |
| `character` | Tipo base de personagem. | Sim/provável em notas. | Sim | Pode substituir parcialmente `individual`, mas não agora. |
| `player` | Personagem jogador. | Parcial/desconhecido. | Sim | Necessário para dashboard de jogadores. |
| `npc` | NPC geral. | Parcial/desconhecido. | Sim | Útil para separação rápida. |
| `antagonist` | Ameaça/antagonista. | Parcial/desconhecido. | Sim | Pode alimentar cards de mestre. |
| `faction` | Tipo facção. | Sim/provável. | Sim | Deve coexistir com tags de facção específicas. |
| `location` | Local. | Sim/provável. | Sim | Separar de `territory`. |
| `session` | Sessão/capítulo RPG. | Não como contrato. | Sim | Depende de decisão `chapters`/`sessions`. |
| `quest` | Quest/gancho. | Não como contrato. | Opcional | Só depois de template. |
| `item` | Item/artefato. | Parcial/desconhecido. | Opcional | Útil para cards de recompensa. |
| `handout` | Conteúdo liberável. | Não como contrato. | Sim | Precisa visibilidade. |
| `secret` | Conteúdo de mestre. | Não como contrato. | Sim/alerta | Alto risco se usado em dashboard público. |
| `public` | Conteúdo público. | Não como contrato. | Sim | Útil para filtro de jogador. |

## Problema central

As tags antigas ainda são tecnicamente valiosas porque controlam visual e possivelmente consultas. Ao mesmo tempo, seus nomes carregam lore de Disgraceland. Remover ou renomear agora quebraria a camada visual antes de existir equivalência RPG.

## Regras de compatibilidade futura

- Criar tags RPG novas sem remover as antigas no mesmo passo.
- Atualizar Supercharged Links por adição, não por substituição destrutiva.
- Validar `supercharged-links-gen.css` como saída gerada; não editar diretamente.
- Só remover tags antigas depois que DataCards, Dataview, links e visual forem validados no Obsidian.
- Para facções, preferir manter `tags` como camada visual e `faction` como campo semântico até contrato final.
