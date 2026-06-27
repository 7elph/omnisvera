> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG SYSTEM INDEX

Índice do modelo RPG operacional baseado na arquitetura técnica auditada do Disgraceland.

Não compara com Omnisvera. Não aplica alterações.

## Documentos

| documento | função | decisões principais | depende de | será usado em |
| --- | --- | --- | --- | --- |
| `RPG_VAULT_OPERATING_MODEL.md` | Define o que o vault RPG precisa fazer na prática | separa preparação, consulta em sessão, dashboard, revelações, mapas e handouts | contratos técnicos do Disgraceland | desenho do sistema alvo |
| `RPG_TEMPLATE_TAXONOMY.md` | Define tipos ideais de template RPG | adiciona PC, NPC, antagonista, quest, rumor, handout, encontro, item e mídia | templates Disgraceland | futura matriz de templates |
| `RPG_FRONTMATTER_PROPOSAL.md` | Propõe vocabulário de campos RPG | separa herdados, adaptados, novos, visuais, Dataview, DataCards e mestre/jogador | frontmatter auditado | futura proposta de schema |
| `RPG_VISUAL_TAG_SYSTEM.md` | Define famílias de tags visuais para RPG | tags como API visual: tipo, facção, região, status, segredo/público | Supercharged Links, Style Settings | futura configuração visual |
| `RPG_DATAVIEW_DATACARDS_REQUIREMENTS.md` | Define consultas necessárias | exemplos para personagens, facções, quests, rumores, handouts, sessões e segredos | Dataview, DataCards | futuro dashboard de mestre |
| `RPG_PLAYER_MASTER_VISIBILITY_MODEL.md` | Define separação mestre/jogador | `visibility`, `spoiler_level`, `player_known`, `revealed_in`, `gm_notes` | Dataview/DataCards | controle de informação |
| `RPG_MEDIA_AND_HANDOUT_MODEL.md` | Define mídia e handouts | separa `thumbnail`, `cover`, `portrait`, `map_image`, `handout_image`, `token_image` | `zz_media`, DataCards, Leaflet | política de mídia |
| `RPG_MAP_AND_CALENDAR_REQUIREMENTS.md` | Define requisitos de mapas/calendário | múltiplas escalas de mapa, Leaflet, eventos, datas em jogo e timeline | Leaflet, Calendarium | sistema de geografia/tempo |
| `RPG_MIGRATION_PRINCIPLES.md` | Define princípios de migração segura | compatibilidade antes de remoção; validação visual; commits pequenos | contratos técnicos | plano futuro de migração |
| `RPG_SYSTEM_INDEX.md` | Índice do modelo | resume todos os documentos e próxima etapa | todos os documentos acima | navegação |

## Decisões principais do modelo

1. O vault RPG deve ser operacional durante mesa, não apenas enciclopédico.
2. Tags continuam sendo infraestrutura visual, não só organização.
3. Frontmatter é a API interna do vault.
4. `thumbnail`, `cover`, `portrait`, `map_image` e `handout_image` têm funções diferentes.
5. Informação de mestre/jogador precisa de campos próprios.
6. `chapters` deve ganhar compatibilidade com `sessions`, não ser removido diretamente.
7. Mapa e calendário são sistemas técnicos com links frágeis.
8. Handouts, rumores e quests precisam virar tipos próprios.
9. Migração futura deve criar compatibilidade antes de remover legado.
10. Validação visual no Obsidian é etapa obrigatória.

## Próxima etapa depois deste modelo

A próxima etapa será mapear o Omnisvera atual com a mesma profundidade, sem modificar nada, para depois comparar:

1. Disgraceland técnico;
2. modelo RPG desejado;
3. Omnisvera atual.

Só depois disso será criado um plano de migração.

## Critérios para considerar este modelo revisado

O modelo precisa ser validado pelo Sage quanto a:

- taxonomia de tipos;
- campos candidatos;
- separação mestre/jogador;
- compatibilidade com uso real de mesa;
- relação com sistema Old Dragon;
- prioridade dos dashboards;
- política de mídia e handouts;
- regras de segurança para segredos.

## O que este modelo não faz

- Não define schema final.
- Não cria templates de Obsidian.
- Não altera notas.
- Não altera CSS.
- Não altera plugins.
- Não move mídia.
- Não compara com Omnisvera.
- Não executa migração.
