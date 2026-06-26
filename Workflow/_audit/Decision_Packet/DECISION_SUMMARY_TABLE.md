# Decision Summary Table

| ID | decisão | opções | recomendação técnica | risco | precisa do Sage? | bloqueia migração? |
| --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | Aparições: `chapters`/`sessions` | Manter `chapters`; trocar por `sessions`; espelhar ambos | Manter `chapters` e adicionar `sessions` com consultas compatíveis | Alto | Parcial | Sim |
| DEC-002 | Tags visuais antigas vs tags RPG | Preservar; remover; usar em paralelo | Preservar antigas e adicionar tags RPG em paralelo | Alto | Sim | Sim |
| DEC-003 | Templates RPG usados agora | Todos; conjunto mínimo; adiar alguns | Priorizar conjunto mínimo operacional | Médio | Sim | Sim, para o mínimo |
| DEC-004 | Campos obrigatórios por tipo | Rígidos; mínimos; nenhum | Definir campos mínimos por tipo | Alto | Parcial | Sim |
| DEC-005 | Separar mestre/jogador | Mestre apenas; dashboard filtrado; notas separadas | Tratar dashboards como mestre até haver filtros | Alto | Sim | Sim |
| DEC-006 | Política de imagens | Só campos antigos; campos especializados; substituir | Manter `thumbnail`/`cover` e adicionar campos especializados | Alto | Parcial | Sim |
| DEC-007 | Campos Old Dragon | YAML; corpo; híbrido | Não tornar obrigatório no primeiro lote | Médio | Parcial | Não |
| DEC-008 | Home/dashboard | Mestre; jogadores; separados | Home atual como mestre; jogadores só depois de visibilidade | Alto | Sim | Sim |
| DEC-009 | Mídia órfã e refs quebradas | Congelar; indexar; limpar | Congelar e validar antes de apagar | Alto | Parcial | Não para compatibilidade; sim para limpeza |
| DEC-010 | Tags antigas como ponte | Preservar; remover; substituir gradual | Preservar como ponte até o fim da migração | Alto | Sim | Sim |
| DEC-011 | `status` e `life_status` | Só `status`; ambos; substituir | Manter `status` e adicionar `life_status` onde fizer sentido | Médio | Parcial | Médio |
| DEC-012 | `type/subtype` com tags | Só tags; só campos; ambos | Usar ambos durante compatibilidade | Alto | Parcial | Sim |
| DEC-013 | Dashboards sem vazamento | Sem público; whitelist; filtros | Dashboard público só com filtro explícito ou whitelist | Alto | Sim | Sim |
| DEC-014 | Ordem de templates ausentes | Todos; prioritários; adiar | Criar primeiro Handout, Quest/Hook, Session, Settlement/Location-Dungeon e Media Reference | Médio | Sim | Médio |

## Decisões de prioridade alta

1. DEC-001
2. DEC-002
3. DEC-004
4. DEC-005
5. DEC-006
6. DEC-008
7. DEC-012
8. DEC-013

## Decisões que podem ser tratadas como defaults técnicos temporários

- DEC-007: Old Dragon opcional no primeiro lote.
- DEC-009: não apagar mídia.
- DEC-011: manter `status` e adicionar `life_status`.
- DEC-010: preservar tags antigas como ponte.
