> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Blockers Before Compatibility Layer

Lista de itens que precisam ser decididos ou tratados antes da primeira alteração técnica da camada de compatibilidade.

## Bloqueadores altos

| item | classificação | por que bloqueia | pode ser resolvido tecnicamente? | depende do Sage? |
| --- | --- | --- | --- | --- |
| `chapters`/`sessions` | bloqueador alto | Aparições e consultas dependem disso. | Sim, com ponte. | Parcial |
| Tags visuais antigas | bloqueador alto | Supercharged Links/DataCards/Dataview podem depender delas. | Sim, preservando como ponte. | Sim, para equivalência final |
| Visibilidade mestre/jogador | bloqueador alto | Sem isso, dashboards podem vazar segredos. | Parcial | Sim |
| Dashboard/Home | bloqueador alto | Home pode misturar conteúdo público e secreto. | Parcial | Sim |
| `thumbnail`/`cover`/`portrait` | bloqueador alto | Cards quebram se campos de imagem forem trocados. | Sim | Parcial |
| Política de dashboard público | bloqueador alto | Sem filtros/whitelist, há risco de exposição. | Parcial | Sim |
| Campos obrigatórios mínimos | bloqueador alto | Sem mínimos, compatibilidade fica imprevisível. | Sim | Parcial |

## Bloqueadores médios

| item | classificação | por que importa | pode ser resolvido tecnicamente? | depende do Sage? |
| --- | --- | --- | --- | --- |
| Templates ausentes | bloqueador médio | Quest, Handout, Session e Media Reference podem ser necessários cedo. | Parcial | Sim |
| Old Dragon | bloqueador médio | Campos mecânicos ajudam consultas, mas podem esperar. | Sim | Parcial |
| `status`/`life_status` | bloqueador médio | Estados narrativos e vida/morte não devem se confundir. | Sim | Parcial |
| `type/subtype` com tags | bloqueador médio | Precisa coexistência antes de substituir queries/tags. | Sim | Parcial |
| Mapa/Leaflet | bloqueador médio | Links e imagens podem quebrar se houver renomeação futura. | Sim | Parcial |
| Calendarium/sessões | bloqueador médio | Datas e sessões precisam conexão futura. | Sim | Parcial |

## Não bloqueadores imediatos

| item | classificação | condição para não bloquear |
| --- | --- | --- |
| Limpeza de mídia órfã | não bloqueador | Não apagar nada agora. |
| Campos Old Dragon avançados | não bloqueador | Não torná-los obrigatórios no primeiro lote. |
| Templates avançados de Rumor/Encounter/Campaign Arc | não bloqueador | Podem vir em segunda rodada. |
| Remoção de tags antigas | não bloqueador | Não remover antes da ponte. |
| Remoção de Disgraceland legado | não bloqueador | Manter como referência técnica congelada. |

## Pode ser resolvido tecnicamente

- Adicionar `sessions` mantendo `chapters`.
- Adicionar `life_status` mantendo `status`.
- Adicionar `portrait` mantendo `thumbnail`.
- Adicionar tags RPG mantendo tags antigas.
- Criar filtros defensivos em Dataview/DataCards.
- Tratar Home atual como dashboard do mestre.
- Congelar mídia e criar índice antes de limpeza.

## Depende do Sage

- Significado final de capítulo versus sessão.
- Equivalência narrativa das tags antigas.
- Quais templates RPG serão usados agora.
- Valores permitidos de `visibility`.
- O que será público para jogadores.
- Quais mídias são canônicas, provisórias ou descartáveis.
- Se Old Dragon deve ser consultável via YAML.
- Se Home será mestre, jogadores ou separada.

## Ordem recomendada antes da primeira alteração técnica

1. Confirmar que `chapters` será preservado enquanto `sessions` é adicionado.
2. Confirmar que tags antigas serão preservadas como ponte.
3. Confirmar que a Home atual é dashboard do mestre por enquanto.
4. Confirmar campos mínimos por tipo de nota.
5. Confirmar política mínima de visibilidade.
6. Confirmar política de imagem: `thumbnail` e `cover` ficam separados.
7. Confirmar que mídia não será apagada nesta fase.
8. Confirmar quais templates mínimos serão criados primeiro.
