# Triple Comparison Index

Esta pasta compara três camadas já documentadas:

1. Disgraceland técnico original: arquitetura funcional usada como base de referência.
2. Modelo RPG desejado: modelo operacional proposto para um vault de RPG de mesa.
3. Omnisvera atual: estado técnico real auditado no vault atual.

Esta comparação não executa migração, não corrige notas e não recomenda remoções imediatas. O objetivo é identificar preservações, perdas, simplificações, pontes técnicas necessárias e decisões pendentes do Sage antes de qualquer alteração no Omnisvera.

## Fontes usadas

- `Workflow/Legacy/Disgraceland/_audit/DISGRACELAND_OBSIDIAN_DEPENDENCY_MAP.md`
- `Workflow/Legacy/Disgraceland/_audit/DISGRACELAND_TECHNICAL_CONTRACTS.md`
- `Workflow/Legacy/Disgraceland/_audit/templates/DISGRACELAND_TEMPLATE_INDEX.md`
- `Workflow/Legacy/Disgraceland/_audit/templates/*.md`
- `Workflow/RPG_SYSTEM_DESIGN/*.md`
- `Workflow/_audit/Omnisvera/*.md`

## Arquivos gerados

| arquivo | função |
| --- | --- |
| `DISGRACELAND_TO_OMNISVERA_GAP_ANALYSIS.md` | Compara a infraestrutura técnica Disgraceland com Omnisvera atual. |
| `RPG_MODEL_TO_OMNISVERA_GAP_ANALYSIS.md` | Compara o modelo RPG desejado com Omnisvera atual. |
| `FRONTMATTER_COMPATIBILITY_MATRIX.md` | Matriz de campos herdados, atuais e desejados. |
| `TEMPLATE_COMPATIBILITY_MATRIX.md` | Matriz de templates técnicos e lacunas RPG. |
| `VISUAL_TAG_COMPATIBILITY_MATRIX.md` | Matriz das tags visuais legadas e tags RPG futuras. |
| `DATAVIEW_DATACARDS_COMPATIBILITY_MATRIX.md` | Matriz de dependências de consultas e cards. |
| `MEDIA_COMPATIBILITY_MATRIX.md` | Matriz de mídia, referências e riscos. |
| `MAP_CALENDAR_COMPATIBILITY_MATRIX.md` | Matriz de Leaflet, Calendarium, mapas e calendário. |
| `PLAYER_MASTER_VISIBILITY_GAP.md` | Lacuna específica entre informação de mestre e jogador. |
| `MIGRATION_DECISION_REGISTER.md` | Registro de decisões pendentes do Sage. |
| `SAFE_MIGRATION_ROADMAP.md` | Roteiro seguro, sem execução, para migração futura. |

## Principais achados

- A base técnica principal foi preservada parcialmente: Dataview, DataCards, Supercharged Links, Style Settings, Leaflet, Calendarium, Homepage e snippets continuam presentes.
- O sistema visual legado ainda carrega tags com semântica de Disgraceland (`loyalist`, `rancher`, `third`, `pirate`, `widow`, `murray`, `steeltown`, `water`, `story`). Elas ainda têm valor técnico e não devem ser removidas antes de equivalentes RPG.
- Omnisvera começou a introduzir campos RPG (`type`, `subtype`, `visibility`, `life_status`, `level`), mas ainda não tem contrato completo de visibilidade mestre/jogador.
- `chapters` ainda é o campo funcional de aparições. `sessions` não aparece como campo operacional auditado.
- A mídia atual é um ponto crítico: a auditoria do Omnisvera encontrou 75 mídias, 69 referências não resolvidas e 35 mídias possivelmente órfãs.
- Os templates RPG já começaram a existir em parte, mas Quest, Rumor, Encounter, Handout, Campaign Arc e Media ainda precisam de contrato técnico antes de migração ampla.

## Visão geral por área

| área | Disgraceland | RPG desejado | Omnisvera atual | status | risco |
| --- | --- | --- | --- | --- | --- |
| Plugins | Pilha completa funcional | Reusar pilha com finalidade RPG | Pilha principal preservada | preservado parcialmente | Médio: configuração pode divergir. |
| Snippets/CSS | Visual específico Disgraceland | Visual RPG com compatibilidade | Snippets antigos e `omnisvera-profile` coexistem | modificado | Alto: CSS antigo pode carregar semântica errada. |
| Supercharged Links | Tags por facção/lore visual | Tags por tipo, facção, região e status narrativo | Tags legadas ainda configuradas | preservado tecnicamente | Alto: remover quebra cor/link. |
| Frontmatter | Campos narrativos e visuais estáveis | Campos RPG com visibilidade e mecânica | Híbrido parcial | preservado parcialmente | Alto: campos críticos inconsistentes. |
| Personagens | Template único robusto | PC, NPC, antagonista e criatura | Templates RPG parciais existem | melhorado parcialmente | Médio/alto: notas reais podem divergir. |
| Facções | Cards por tag/faction/leader/status | Facções ativas e influência RPG | Parcial | preservado parcialmente | Médio: tags antigas podem conflitar. |
| Territórios | Cards por cover/region/leader/population | Regiões, reinos, settlements e dungeons | Parcial | modificado | Médio: fronteiras e tipos não normalizados. |
| Locais | Cards por cover/territory/info | Local, dungeon, assentamento | Parcial | preservado parcialmente | Médio: tipo/localização precisa contrato. |
| Lore/Religião | Tags e cards dedicados | Lore público/secreto, culto/religião | Parcial | preservado parcialmente | Médio: visibilidade incompleta. |
| Sessões/Capítulos | `chapters` e capítulos narrativos | `sessions`, arcos, aparições | `chapters` continua; `sessions` ausente | lacuna | Alto: aparições podem quebrar se renomear. |
| Dashboard | Home com Dataview/DataCards | Dashboard mestre/jogador filtrado | Dashboard existe, escopo ambíguo | suporta parcialmente | Alto: risco de vazar segredo. |
| Mapas | Leaflet com imagem e marcadores | Mapas por escala e links para notas | Leaflet existe | preservado parcialmente | Alto: renomear notas quebra marcadores. |
| Calendário | Calendarium com eventos | Calendário diegético + sessões | Calendarium existe | preservado parcialmente | Médio: vínculo com sessões incompleto. |
| Mídia | `zz_media` grande e referenciada | política de thumbnail/cover/portrait/map/handout | `zz_media` menor, refs quebradas | alto risco | Alto: não apagar sem validação cruzada. |
| Visibilidade | Não era requisito central | Mestre/jogador/público/segredo | Campo `visibility` parcial | lacuna | Alto: dashboards sem filtro podem vazar conteúdo. |

## Pontos que exigem decisão do Sage

- Definir se `chapters` continua como campo oficial ou se haverá ponte para `sessions`.
- Definir o mapa semântico das tags antigas para tags RPG.
- Definir campos obrigatórios mínimos por template RPG.
- Definir se a Home será dashboard do mestre, dos jogadores ou terá versões separadas.
- Definir política de visibilidade antes de publicar/filtrar dashboards.
- Definir política de mídia antes de apagar, mover ou renomear qualquer arquivo em `zz_media`.
- Definir se Old Dragon terá campos dedicados (`old_dragon_class`, `old_dragon_race`, `level`) ou se ficará em conteúdo textual.
