# Migration Decision Register

Registro de decisões pendentes antes de qualquer migração técnica do Omnisvera.

| decisão | contexto | opções | risco | precisa do Sage? |
| --- | --- | --- | --- | --- |
| Manter `chapters` ou criar `sessions` | `chapters` é funcional; RPG precisa sessões. | Manter `chapters`; criar `sessions`; usar ambos com ponte. | Alto: aparições quebram se remover cedo. | Sim |
| Mapear tags visuais antigas | Tags Supercharged ainda são de Disgraceland. | Manter; adicionar tags RPG; criar equivalentes e migrar depois. | Alto: quebrar cor/link/cards. | Sim |
| Definir templates RPG usados | Modelo propôs muitos templates. | Usar todos; priorizar subconjunto; adiar alguns. | Médio: complexidade excessiva. | Sim |
| Definir campos obrigatórios | Omnisvera tem campos parciais. | Mínimo por tipo; campos opcionais; validação por lote. | Alto: notas inconsistentes. | Sim |
| Separar mestre/jogador | RPG precisa visibilidade. | Um dashboard mestre; dois dashboards; filtros por campo. | Alto: vazamento de segredo. | Sim |
| Lidar com mídia órfã | 35 possíveis órfãs e 69 refs não resolvidas. | Congelar; auditar manualmente; criar índice de uso. | Alto: apagar arte útil. | Sim |
| Tratar tags `loyalist`, `rancher`, `third` etc. | Tags têm valor técnico e semântica legada. | Preservar; mapear; esconder visualmente; migrar em fase final. | Alto: visual quebra. | Sim |
| Definir Home/dashboard | Home pode servir mestre, jogadores ou ambos. | Mestre apenas; jogadores apenas; duas Homes. | Alto: vazamento ou ruído. | Sim |
| Campos Old Dragon no frontmatter | RPG usa Old Dragon; campos dedicados ausentes. | YAML dedicado; corpo da ficha; híbrido. | Médio: consultas mecânicas ficam limitadas. | Sim |
| `thumbnail` versus `portrait` | `thumbnail` já alimenta cards; `portrait` é desejado. | Manter thumbnail; adicionar portrait; mapear ambos. | Alto: cards quebram. | Sim |
| `cover` versus `map_image` | Cover já existe; mapa precisa campo próprio. | Manter cover; adicionar map_image; usar Leaflet config. | Alto: mapas/covers misturam funções. | Sim |
| Reino/região/local | Taxonomia geográfica ainda ambígua. | Definir hierarchy; aceitar legado; criar subtype. | Médio/alto: mapas e cards inconsistentes. | Sim |
| Quest/Rumor/Handout como notas | Modelo RPG sugere templates próprios. | Criar notas; usar campos em sessão; híbrido. | Médio: excesso de granularidade. | Sim |
| Limpeza de Disgraceland legado | Legado ainda serve como template técnico. | Manter congelado; remover só depois; arquivar. | Alto: perder referência técnica. | Sim |

## Decisões bloqueadoras

As seguintes decisões bloqueiam migração em lote:

1. `chapters`/`sessions`.
2. Tags visuais antigas versus tags RPG.
3. Visibilidade mestre/jogador.
4. Política de mídia.
5. Campos obrigatórios por template.

## Decisões não bloqueadoras imediatas

Estas podem ser adiadas se a camada de compatibilidade for criada:

- Nome final de todos os subtipos RPG.
- Campos avançados de Old Dragon.
- Política completa de token/VTT.
- Calendário religioso completo.
- Rumores como notas separadas ou campo.
