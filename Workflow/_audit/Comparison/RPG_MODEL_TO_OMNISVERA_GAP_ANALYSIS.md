> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG Model to Omnisvera Gap Analysis

Comparação entre o modelo operacional RPG desejado e o Omnisvera atual. Esta análise verifica capacidade técnica, não conteúdo narrativo.

## Classificação usada

- já suporta
- suporta parcialmente
- não suporta
- precisa campo novo
- precisa template novo
- precisa Dataview/DataCards
- precisa decisão do Sage

## Matriz de capacidades RPG

| capacidade RPG | modelo desejado | Omnisvera atual | status | lacuna | próximo tipo de decisão |
| --- | --- | --- | --- | --- | --- |
| Uso durante sessão | Consulta rápida, dashboard limpo, mobile e links estáveis. | Dashboards e consultas existem. | suporta parcialmente | Falta separar visão mestre/jogador e priorizar consulta de mesa. | Sage |
| Dashboard do mestre | Painel com segredo, NPCs, facções, ganchos, sessão atual. | Home e Workflow têm consultas. | suporta parcialmente | Escopo do dashboard não está contratado. | Sage |
| Dashboard dos jogadores | Somente informação pública/liberada. | Não há contrato claro. | precisa campo novo | Requer filtros de `visibility`, `player_known` ou equivalente. | Sage |
| Personagens jogadores | Template próprio, mecânica e narrativa. | Template de personagem jogador existe em estrutura. | suporta parcialmente | Campos Old Dragon e sessões ainda não consolidados. | Sage |
| NPCs importantes | Template com retrato, facção, local, papel e segredos. | Há template/estrutura parcial. | suporta parcialmente | Visibilidade e aparições precisam contrato. | Sage |
| NPCs menores | Template mais leve. | Template parcial existe. | suporta parcialmente | Precisa validar campos mínimos. | Sage |
| Antagonistas | Template com perigo, objetivos e segredos. | Template de antagonista existe. | suporta parcialmente | `danger_level` e filtros ainda não são operacionais. | Sage |
| Facções | Agrupamento por tags, cards, status e relações. | Facções existem com campos herdados. | suporta parcialmente | Tags antigas ainda carregam semântica Disgraceland. | Sage |
| Regiões/territórios | Reinos/regiões com cover, leader, population, mapa. | Territórios existem. | suporta parcialmente | Taxonomia reino/região/fronteira precisa decisão. | Sage |
| Cidades/vilas/assentamentos | Template de settlement separado de território. | Parcial/ambíguo. | precisa template novo | Local e território podem estar misturados. | Sage |
| Locais/dungeons | Locais exploráveis, perigos, mapa, conexões. | Locations existem. | suporta parcialmente | Dungeon como subtipo ainda precisa contrato. | Sage |
| Quests/ganchos | Estados aberto/ativo/resolvido e links para NPC/local. | Não há contrato auditado. | precisa template novo | Campo `hooks`/quest não operacional. | Sage |
| Rumores | Informação liberável, origem e confiabilidade. | Não há contrato auditado. | precisa template novo | Precisa status e visibilidade. | Sage |
| Encontros | Preparação mecânica e narrativa de mesa. | Não há contrato auditado. | precisa template novo | Campos de dificuldade/perigo ausentes. | Sage |
| Handouts | Mídia pública, status liberado e controle de jogador. | Não há contrato claro. | precisa template novo | `handout_status` e `handout_image` ausentes. | Sage |
| Mapas | Escalas múltiplas, marcadores e links. | Leaflet existe. | suporta parcialmente | Regras de escala/map_image e renomeação precisam contrato. | Sage |
| Calendário | Datas diegéticas, sessões, eventos futuros e históricos. | Calendarium existe. | suporta parcialmente | Vínculo sessão-data não consolidado. | Sage |
| Visibilidade mestre/jogador | Público, jogadores, mestre, segredo e revelação. | `visibility` aparece parcialmente. | precisa campo novo | Faltam `spoiler_level`, `player_known`, `gm_secret`, `revealed_in`, `handout_status`. | Sage |
| Campos Old Dragon | Classe, raça, nível, mecânica. | `level` existe parcialmente; campos dedicados não auditados. | precisa campo novo | `old_dragon_class` e `old_dragon_race` ausentes. | Sage |
| Aparições por sessão | `sessions`, arcos e aparições. | `chapters` existe; `sessions` ausente. | precisa ponte | Não remover `chapters` antes de compatibilidade. | Sage |
| Mídia pública/secreta | thumbnail, cover, portrait, map, token e handout. | `thumbnail`/`cover` existem; refs quebradas. | suporta parcialmente | Campos especializados e política de mídia ausentes. | Sage |

## Suportes já aproveitáveis

- Dataview e DataCards podem sustentar listas por facção, região, status e tipo.
- Leaflet e Calendarium já existem como base técnica.
- `visibility` já aparece em parte do vault, mas sem contrato final.
- Templates de personagem RPG parecem ter começado a ser definidos.

## Lacunas críticas

- Falta contrato mestre/jogador antes de dashboards públicos.
- Falta decidir `chapters` versus `sessions`.
- Falta padronizar mídia sem apagar referências existentes.
- Falta camada de equivalência entre tags visuais antigas e tags RPG.
- Falta definir se campos mecânicos Old Dragon entram em frontmatter ou corpo da nota.

## Conclusão operacional

Omnisvera já tem infraestrutura suficiente para evoluir para um vault RPG, mas ainda não deve receber migração ampla. A prioridade é definir contratos de compatibilidade: campos, tags visuais, visibilidade e mídia.
