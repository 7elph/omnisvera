# Sage Decision Packet

Este pacote transforma a comparação técnica em decisões humanas claras antes da criação da camada de compatibilidade do Omnisvera.

Escopo: documentação de decisão. Não executa migração, não altera notas, não muda templates, não edita CSS, não edita JSON de plugins e não toca em mídia.

## DEC-001 — Aparições: manter `chapters`, criar `sessions` ou espelhar ambos

Contexto: Disgraceland usa `chapters` para aparições. Omnisvera ainda preserva `chapters`. O modelo RPG precisa de sessões.

Por que importa: personagens, sessões, dashboards e histórico de campanha dependem de um campo estável para aparições.

Opções:

- Manter apenas `chapters`.
- Criar apenas `sessions` e migrar tudo.
- Espelhar ambos durante transição: manter `chapters` e adicionar `sessions`.

Risco de cada opção:

- Manter apenas `chapters`: preserva compatibilidade, mas mantém semântica menos adequada para RPG.
- Criar apenas `sessions`: alto risco de quebrar Dataview e histórico.
- Espelhar ambos: maior trabalho inicial, menor risco técnico.

Recomendação técnica segura: manter `chapters`, adicionar `sessions` e criar consultas compatíveis com ambos.

Depende de decisão narrativa do Sage: parcialmente, para definir se “capítulo” e “sessão” terão significados diferentes.

Pode ser decidido tecnicamente sem afetar lore: sim, se for apenas camada de compatibilidade.

Bloqueia camada de compatibilidade: sim.

## DEC-002 — Tags visuais antigas versus tags RPG

Contexto: tags como `loyalist`, `rancher`, `third`, `pirate`, `widow`, `murray`, `steeltown`, `water` e `story` ainda podem controlar Supercharged Links, DataCards e Dataview.

Por que importa: remover ou renomear tags antes de criar equivalentes quebra cor de links, agrupamentos e consultas.

Opções:

- Preservar tags antigas como ponte.
- Remover tags antigas e criar tags RPG.
- Usar tags antigas e novas em paralelo.

Risco de cada opção:

- Preservar apenas antigas: mantém semântica de Disgraceland.
- Remover agora: alto risco visual e funcional.
- Usar em paralelo: aumenta redundância temporária, mas é mais seguro.

Recomendação técnica segura: preservar tags antigas e adicionar tags RPG em paralelo.

Depende de decisão narrativa do Sage: sim, para mapear facções/grupos legados para facções/regiões RPG.

Pode ser decidido tecnicamente sem afetar lore: parcialmente. A ponte pode ser técnica; o mapeamento final não.

Bloqueia camada de compatibilidade: sim.

## DEC-003 — Templates RPG usados agora

Contexto: o modelo RPG propôs muitos templates; Omnisvera já tem alguns parciais.

Por que importa: criar todos de uma vez pode gerar complexidade. Criar poucos demais pode deixar lacunas operacionais.

Opções:

- Criar todos os templates RPG propostos.
- Priorizar um conjunto mínimo.
- Adiar templates menos usados.

Risco de cada opção:

- Todos: alto custo e maior chance de inconsistência.
- Mínimo: menor risco, mas exige decisões de prioridade.
- Adiar: seguro, desde que não bloqueie consultas essenciais.

Recomendação técnica segura: priorizar templates mínimos: Player Character, NPC Importante, NPC Menor, Antagonista, Facção, Território/Região, Local/Dungeon, Sessão, Lore, Religião, Handout.

Depende de decisão narrativa do Sage: sim, para priorizar o que será usado em mesa.

Pode ser decidido tecnicamente sem afetar lore: parcialmente.

Bloqueia camada de compatibilidade: sim, ao menos para o conjunto mínimo.

## DEC-004 — Campos obrigatórios por tipo de nota

Contexto: Omnisvera já usa campos como `thumbnail`, `cover`, `status`, `type`, `subtype`, `visibility`, `faction`, `territory`, `chapters`, mas de forma parcial.

Por que importa: sem campos mínimos, Dataview/DataCards não ficam confiáveis.

Opções:

- Campos obrigatórios rígidos por template.
- Campos mínimos pequenos e campos opcionais.
- Nenhum campo obrigatório no primeiro lote.

Risco de cada opção:

- Rígido: pode travar migração e exigir correção manual extensa.
- Mínimo: equilibra consistência e velocidade.
- Nenhum obrigatório: mantém inconsistência.

Recomendação técnica segura: definir campos mínimos por tipo e expandir depois.

Depende de decisão narrativa do Sage: parcialmente, para campos de lore e visibilidade.

Pode ser decidido tecnicamente sem afetar lore: sim, para campos técnicos (`tags`, `type`, `thumbnail`, `cover`, `visibility`).

Bloqueia camada de compatibilidade: sim.

## DEC-005 — Separação mestre/jogador

Contexto: `visibility` aparece parcialmente, mas faltam `spoiler_level`, `player_known`, `gm_secret`, `revealed_in` e `handout_status`.

Por que importa: dashboards e cards podem vazar segredos.

Opções:

- Tratar todos os dashboards como mestre por enquanto.
- Criar dashboard de jogador só depois de filtros.
- Criar notas separadas públicas e secretas.

Risco de cada opção:

- Mestre apenas: seguro, mas sem entrega para jogadores.
- Dashboard filtrado: melhor destino, exige contrato.
- Notas separadas: seguro, mas aumenta duplicação.

Recomendação técnica segura: considerar tudo dashboard do mestre até criar filtros de visibilidade; só depois criar dashboard dos jogadores.

Depende de decisão narrativa do Sage: sim.

Pode ser decidido tecnicamente sem afetar lore: parcialmente. A regra de segurança pode ser técnica.

Bloqueia camada de compatibilidade: sim.

## DEC-006 — Política de imagens: `thumbnail`, `cover`, `portrait`, `map_image`, `handout_image`

Contexto: `thumbnail` e `cover` já têm funções técnicas diferentes. O modelo RPG quer campos especializados.

Por que importa: DataCards depende de `thumbnail`/`cover`; Leaflet e handouts precisam campos próprios.

Opções:

- Manter só `thumbnail` e `cover`.
- Adicionar campos especializados sem remover os antigos.
- Substituir `thumbnail` por `portrait`.

Risco de cada opção:

- Manter só antigos: compatível, mas pouco expressivo.
- Adicionar especializados: seguro, com redundância controlada.
- Substituir: alto risco de quebrar cards.

Recomendação técnica segura: manter `thumbnail` e `cover`; adicionar `portrait`, `map_image` e `handout_image` apenas quando necessário.

Depende de decisão narrativa do Sage: não para compatibilidade; sim para decidir imagem pública/secreta.

Pode ser decidido tecnicamente sem afetar lore: sim.

Bloqueia camada de compatibilidade: sim.

## DEC-007 — Campos Old Dragon no frontmatter

Contexto: `level` aparece parcialmente; `old_dragon_class` e `old_dragon_race` não estão consolidados.

Por que importa: campos mecânicos permitem consultas e dashboards, mas podem engessar fichas ainda em ajuste.

Opções:

- Criar campos dedicados no YAML.
- Manter mecânica no corpo da ficha.
- Usar híbrido: campos essenciais no YAML, detalhes no corpo.

Risco de cada opção:

- YAML completo: exige padronização cedo.
- Corpo apenas: limita consultas.
- Híbrido: melhor equilíbrio, mas precisa contrato.

Recomendação técnica segura: não tornar campos Old Dragon obrigatórios no primeiro lote; usar `level` como campo simples e decidir `old_dragon_class`/`old_dragon_race` depois.

Depende de decisão narrativa do Sage: parcialmente.

Pode ser decidido tecnicamente sem afetar lore: sim.

Bloqueia camada de compatibilidade: não, se for opcional no início.

## DEC-008 — Home/dashboard do mestre e/ou dos jogadores

Contexto: Home/dashboard já existe, mas não há contrato claro de público-alvo.

Por que importa: Home agrega Dataview, DataCards, mídia e tags. Sem filtro, pode revelar conteúdo.

Opções:

- Home única para o mestre.
- Home única para jogadores.
- Home do mestre e dashboard separado de jogadores.

Risco de cada opção:

- Mestre apenas: seguro.
- Jogadores apenas: risco alto enquanto não houver filtros.
- Separadas: mais trabalho, melhor controle.

Recomendação técnica segura: Home atual deve ser tratada como dashboard do mestre; dashboard de jogadores só depois de visibilidade.

Depende de decisão narrativa do Sage: sim.

Pode ser decidido tecnicamente sem afetar lore: parcialmente.

Bloqueia camada de compatibilidade: sim.

## DEC-009 — Mídia órfã e referências quebradas

Contexto: a auditoria encontrou 75 mídias no Omnisvera, 69 referências não resolvidas e 35 possíveis órfãs.

Por que importa: apagar mídia agora pode destruir assets úteis; referências quebradas podem vir de YAML, embeds, HTML, CSS ou Leaflet.

Opções:

- Não apagar nada até validação cruzada.
- Criar índice de uso de mídia.
- Limpar órfãs automaticamente.

Risco de cada opção:

- Não apagar: seguro, mas mantém sujeira.
- Índice: melhor próximo passo técnico.
- Limpeza automática: alto risco.

Recomendação técnica segura: congelar mídia e criar índice/validação antes de qualquer limpeza.

Depende de decisão narrativa do Sage: parcialmente, para decidir assets desejados.

Pode ser decidido tecnicamente sem afetar lore: sim.

Bloqueia camada de compatibilidade: sim para limpeza; não para adicionar campos.

## DEC-010 — Tags antigas como ponte

Contexto: tags antigas ainda têm valor técnico mesmo quando a lore mudou.

Por que importa: elas conectam visual, queries e agrupamento.

Opções:

- Preservar como ponte técnica.
- Remover ao criar tags RPG.
- Arquivar e substituir gradualmente.

Risco de cada opção:

- Preservar: mantém nomes feios/legados temporariamente.
- Remover: alto risco.
- Substituir gradualmente: seguro, mas exige controle.

Recomendação técnica segura: preservar tags antigas como ponte até o final da migração.

Depende de decisão narrativa do Sage: sim, para equivalências finais.

Pode ser decidido tecnicamente sem afetar lore: sim, como regra temporária.

Bloqueia camada de compatibilidade: sim.

## DEC-011 — `status` e `life_status`

Contexto: `status` já existe e pode significar estado narrativo/editorial; `life_status` aparece parcialmente como campo mais específico.

Por que importa: dashboards precisam distinguir “ativo/inativo” de “vivo/morto/desaparecido”.

Opções:

- Usar apenas `status`.
- Adicionar `life_status` e manter `status`.
- Substituir `status` por `life_status`.

Risco de cada opção:

- Apenas `status`: ambíguo.
- Ambos: seguro, mas exige contrato.
- Substituir: quebra cards/queries.

Recomendação técnica segura: manter `status`; adicionar `life_status` para personagens/criaturas quando necessário.

Depende de decisão narrativa do Sage: parcialmente, para valores de estado.

Pode ser decidido tecnicamente sem afetar lore: sim.

Bloqueia camada de compatibilidade: médio.

## DEC-012 — `type/subtype` convivendo com tags visuais

Contexto: `type` e `subtype` aparecem parcialmente. Tags ainda controlam visual e consultas.

Por que importa: campos semânticos são melhores para consulta; tags são necessárias para visual.

Opções:

- Usar só tags.
- Usar só `type/subtype`.
- Usar ambos: tags para visual/agrupamento, `type/subtype` para semântica.

Risco de cada opção:

- Só tags: mantém ambiguidade.
- Só campos: quebra Supercharged e consultas por tag.
- Ambos: redundância temporária controlada.

Recomendação técnica segura: usar ambos durante compatibilidade.

Depende de decisão narrativa do Sage: não para a regra técnica; sim para nomes finais.

Pode ser decidido tecnicamente sem afetar lore: sim.

Bloqueia camada de compatibilidade: sim.

## DEC-013 — Política de dashboards para não vazar segredos

Contexto: DataCards e Dataview podem listar notas sem considerar `visibility`.

Por que importa: um dashboard de jogadores pode revelar NPCs, locais, handouts ou imagens secretas.

Opções:

- Não criar dashboard público ainda.
- Criar dashboard público apenas com whitelist.
- Criar filtro por `visibility`/`player_known`/`handout_status`.

Risco de cada opção:

- Sem dashboard público: seguro.
- Whitelist: seguro, mas manual.
- Filtro: melhor destino, exige campos confiáveis.

Recomendação técnica segura: dashboard público só com filtro explícito ou whitelist.

Depende de decisão narrativa do Sage: sim.

Pode ser decidido tecnicamente sem afetar lore: parcialmente.

Bloqueia camada de compatibilidade: sim.

## DEC-014 — Ordem de criação dos templates ausentes

Contexto: templates ausentes/incompletos incluem Quest/Hook, Rumor, Encounter, Handout, Campaign Arc, Media Reference, Settlement e Dungeon.

Por que importa: criar tudo sem prioridade aumenta manutenção; criar tarde demais bloqueia sessões.

Opções:

- Criar todos antes da compatibilidade.
- Criar apenas os que bloqueiam dashboard/sessão.
- Adiar todos.

Risco de cada opção:

- Todos: risco de overengineering.
- Prioritários: bom equilíbrio.
- Adiar todos: mantém lacunas.

Recomendação técnica segura: criar primeiro Handout, Quest/Hook, Session, Settlement/Location-Dungeon e Media Reference; deixar Encounter/Rumor/Campaign Arc para segunda rodada se não forem necessários imediatamente.

Depende de decisão narrativa do Sage: sim.

Pode ser decidido tecnicamente sem afetar lore: parcialmente.

Bloqueia camada de compatibilidade: médio.

## Síntese de bloqueio

Bloqueiam a primeira camada de compatibilidade:

- DEC-001: `chapters`/`sessions`.
- DEC-002/DEC-010: tags visuais antigas como ponte.
- DEC-004: campos mínimos.
- DEC-005/DEC-013: visibilidade e política de dashboard.
- DEC-006: política básica de imagens.
- DEC-008: escopo da Home/dashboard.

Não bloqueiam a primeira camada se tratados como opcionais:

- DEC-007: campos Old Dragon completos.
- DEC-014: todos os templates avançados.
- DEC-009: limpeza de mídia, desde que nada seja apagado.
