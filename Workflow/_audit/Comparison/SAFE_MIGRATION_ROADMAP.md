# Safe Migration Roadmap

Roteiro seguro para uma migração futura. Este documento não executa alterações.

## Fase 1 — Congelar auditorias

- Manter os relatórios de Disgraceland, modelo RPG e Omnisvera como baseline.
- Não editar relatórios antigos durante a migração; criar adendos se necessário.
- Registrar commits separados para cada etapa documental.

## Fase 2 — Validar decisões do Sage

- Resolver decisões bloqueadoras do `MIGRATION_DECISION_REGISTER.md`.
- Definir campos obrigatórios mínimos.
- Definir escopo da Home: mestre, jogadores ou ambos.
- Definir política de mídia.
- Definir ponte `chapters`/`sessions`.

## Fase 3 — Criar camada de compatibilidade

- Adicionar campos novos sem remover campos antigos.
- Manter `thumbnail` e `cover`.
- Manter `chapters` enquanto `sessions` não estiver validado.
- Manter tags antigas enquanto tags RPG não tiverem Supercharged/DataCards equivalentes.

## Fase 4 — Atualizar Supercharged Links sem remover tags antigas

- Adicionar tags RPG novas.
- Configurar cores/pesos por Style Settings.
- Não editar `supercharged-links-gen.css` diretamente.
- Validar links coloridos no Obsidian.

## Fase 5 — Atualizar templates sem migrar notas ainda

- Criar/ajustar templates RPG finais.
- Validar frontmatter mínimo.
- Incluir campos de visibilidade.
- Incluir placeholders de mídia sem quebrar `thumbnail`/`cover`.

## Fase 6 — Adicionar campos novos sem remover antigos

- Adicionar `sessions` mantendo `chapters`.
- Adicionar `visibility` padronizado.
- Adicionar `player_known`, `spoiler_level`, `revealed_in` e `handout_status` se aprovados.
- Adicionar campos Old Dragon se aprovados.

## Fase 7 — Criar Dataviews compatíveis

- Consultas devem aceitar campos antigos e novos durante transição.
- Dashboards públicos devem filtrar visibilidade.
- Cards devem continuar funcionando com `thumbnail` e `cover`.
- Consultas por aparição devem aceitar `chapters` e `sessions`.

## Fase 8 — Validar Home/dashboard

- Decidir se Home é do mestre ou dos jogadores.
- Criar dashboard separado se necessário.
- Testar cards de personagem, facção, território, local, sessão e handout.
- Garantir que segredo não apareça em dashboard público.

## Fase 9 — Validar mídia

- Resolver referências não resolvidas antes de limpeza.
- Mapear possíveis órfãos manualmente.
- Não apagar mídia sem validação cruzada.
- Definir uso de `portrait`, `map_image`, `handout_image` e `token_image`.

## Fase 10 — Validar mapas/calendário

- Exportar e revisar marcadores Leaflet.
- Validar links de marcador para notas.
- Validar imagem base.
- Ligar sessões/datas ao Calendarium sem remover eventos existentes.

## Fase 11 — Migrar um lote pequeno de notas

- Escolher poucas notas representativas.
- Preferir uma nota de personagem, facção, território, local, lore e sessão.
- Validar visualmente no Obsidian.
- Registrar erros antes de migrar o restante.

## Fase 12 — Testar no Obsidian

- Abrir Home/dashboard.
- Abrir cards.
- Abrir mapa.
- Abrir calendário.
- Verificar Supercharged Links.
- Verificar mobile se o uso em mesa depender disso.

## Fase 13 — Migrar o restante

- Migrar por tipo de nota, não tudo de uma vez.
- Fazer commits pequenos por categoria.
- Rodar auditorias de links/campos após cada lote.

## Fase 14 — Limpar legado somente no final

- Só remover campos antigos após consultas novas estarem validadas.
- Só remover tags antigas após Supercharged/DataCards/Dataview equivalentes.
- Só apagar mídia após validação cruzada.
- Só remover Disgraceland legado depois que não for mais referência técnica.

## Regras que não devem ser quebradas

- Não remover campo antigo no mesmo passo em que adiciona campo novo.
- Não trocar `thumbnail` por `cover` sem camada de compatibilidade.
- Não remover `chapters` antes de `sessions`.
- Não editar CSS gerado automaticamente.
- Não renomear nota usada por Leaflet sem atualizar mapa.
- Não apagar mídia possivelmente órfã sem análise cruzada.
- Não misturar migração técnica com criação de lore.
