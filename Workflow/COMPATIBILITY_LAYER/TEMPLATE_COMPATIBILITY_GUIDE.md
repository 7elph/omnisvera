# Template Compatibility Guide

Este guia define como templates devem evoluir sem aplicar mudanças nas notas atuais.

Regra central: templates novos devem preservar campos herdados e adicionar campos RPG sem remover compatibilidade.

## Prioridade 1 — Character

Campos antigos preservados:

- `NoteIcon`
- `NoteStatus`
- `thumbnail`
- `cover`
- `status`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`
- `tags`
- `cssclasses`

Campos novos recomendados:

- `type: character`
- `subtype`
- `visibility`
- `spoiler_level`
- `player_known`
- `gm_secret`
- `revealed_in`
- `sessions`
- `portrait`
- `life_status`
- `old_dragon_class`
- `old_dragon_race`
- `level`

Tags antigas preservadas:

- `individual` quando existir.
- tags visuais antigas associadas.

Tags novas permitidas:

- `character`
- `player`
- `npc`
- `npc-important`
- `npc-minor`
- `antagonist`

Risco de migração: alto se `chapters`, `thumbnail` ou tags antigas forem removidos.

## Prioridade 2 — Faction

Campos antigos preservados:

- `thumbnail`
- `cover`
- `status`
- `leader`
- `location`
- `territory`
- `tags`

Campos novos recomendados:

- `type: faction`
- `subtype`
- `visibility`
- `player_known`
- `sessions`

Tags antigas preservadas:

- qualquer tag visual de facção legado.

Tags novas permitidas:

- `faction`
- tag específica da facção RPG.

Risco de migração: médio/alto se a facção depender de tag antiga para cor ou card.

## Prioridade 3 — Territory/Region

Campos antigos preservados:

- `cover`
- `region`
- `leader`
- `population`
- `territory`
- `tags`

Campos novos recomendados:

- `type: territory`
- `subtype: region | kingdom | settlement`
- `visibility`
- `map_image`

Tags antigas preservadas:

- `territory`
- `steeltown` ou outras tags regionais antigas, se existirem.

Tags novas permitidas:

- `territory`
- `region`
- `kingdom`
- `settlement`

Risco de migração: médio se reino, região e assentamento forem misturados sem `subtype`.

## Prioridade 4 — Location

Campos antigos preservados:

- `cover`
- `territory`
- `location`
- `info`
- `tags`

Campos novos recomendados:

- `type: location`
- `subtype: poi | dungeon | settlement | ruin`
- `visibility`
- `map_image`
- `danger_level`
- `hooks`

Tags antigas preservadas:

- `location` se existir.
- tags regionais antigas se usadas visualmente.

Tags novas permitidas:

- `location`
- `dungeon`
- `settlement`
- `ruin`

Risco de migração: médio se locais secretos aparecerem em dashboard público.

## Prioridade 5 — Session

Campos antigos preservados:

- `chapters`
- `tags`
- `date`
- `description`
- `cover`

Campos novos recomendados:

- `type: session`
- `subtype`
- `sessions`
- `arcs`
- `visibility`
- `player_known`

Tags antigas preservadas:

- `story`

Tags novas permitidas:

- `session`
- `story`

Risco de migração: alto se `chapters` for removido antes da ponte.

## Prioridade 6 — Lore

Campos antigos preservados:

- `cover`
- `info`
- `tags`
- `NoteIcon`
- `NoteStatus`

Campos novos recomendados:

- `type: lore`
- `subtype`
- `visibility`
- `spoiler_level`
- `player_known`
- `gm_secret`
- `revealed_in`

Tags antigas preservadas:

- `lore`

Tags novas permitidas:

- `lore`
- `public`
- `secret`

Risco de migração: alto se lore secreta aparecer em cards públicos.

## Prioridade 7 — Handout

Campos antigos preservados:

- `thumbnail`
- `cover`
- `tags`

Campos novos recomendados:

- `type: handout`
- `subtype`
- `visibility`
- `player_known`
- `gm_secret`
- `revealed_in`
- `handout_image`
- `media_status`

Tags antigas preservadas:

- nenhuma remoção automática.

Tags novas permitidas:

- `handout`
- `public`
- `secret`

Risco de migração: alto por exposição acidental aos jogadores.

## Prioridade 8 — Quest/Hook

Campos antigos preservados:

- `status`
- `location`
- `territory`
- `faction`
- `tags`

Campos novos recomendados:

- `type: quest`
- `subtype: hook | quest`
- `visibility`
- `player_known`
- `sessions`
- `hooks`

Tags antigas preservadas:

- qualquer tag visual associada à facção/local.

Tags novas permitidas:

- `quest`
- `hook`

Risco de migração: médio se ganchos secretos aparecerem em dashboard geral.

## Regra final

Nenhum template novo deve exigir que notas antigas removam campos no primeiro lote.
