> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG FRONTMATTER PROPOSAL

Proposta de campos para uma versão RPG do sistema técnico derivado do Disgraceland.

Não aplica campos em nenhuma nota. Não decide obrigatoriedade final. Não compara com Omnisvera.

## 1. Herdados do Disgraceland

Campos que já têm contrato técnico no Disgraceland e devem ser tratados como compatibilidade:

| campo | uso herdado | observação RPG |
| --- | --- | --- |
| `obsidianUIMode` | preview/renderização | preservar quando usado por páginas visuais |
| `NoteIcon` | ícone visual | manter compatível com Icon Folder/tema |
| `NoteStatus` | status editorial | pode virar status de preparação |
| `status` | estado narrativo/card | precisa separar de `life_status` |
| `thumbnail` | imagem pequena em DataCards/Home | manter para cards |
| `cover` | imagem de card/capa | manter para territórios, sessões, locais |
| `banner` | imagem de topo | útil para dashboards |
| `banner-x` | posição visual | compatibilidade visual |
| `banner-y` | posição visual | compatibilidade visual |
| `banner-height` | altura visual | compatibilidade visual |
| `content-start` | offset visual | compatibilidade visual |
| `banner-fade` | fade visual | compatibilidade visual |
| `location` | local atual/relacionado | manter para consultas |
| `territory` | região/território | manter para geografia |
| `district` | bairro/distrito | útil em cidades |
| `faction` | facção relacionada | manter para agrupamento |
| `religion` | fé/culto | manter para personagens/religiões |
| `role` | papel narrativo | útil para NPC/PC |
| `chapters` | aparições por capítulo | compatibilidade com sistema antigo |
| `leader` | líder de facção/território | útil para cards |
| `population` | população de território | útil para assentamentos |
| `region` | região | útil para mapa |
| `date` | data de capítulo/story | reaproveitar em sessões/handouts |
| `description` | descrição curta | cards e dashboards |
| `cssclasses` | CSS por nota | preservar |
| `tags` | filtros e visual | preservar como API |

## 2. Adaptados para RPG

| campo | origem conceitual | adaptação proposta |
| --- | --- | --- |
| `chapters` | aparições em capítulo | manter como compatibilidade; adicionar `sessions` |
| `status` | vivo/ativo/aberto | usar para estado geral; criar `life_status` para vida |
| `location` | onde está | usar para localização atual ou principal |
| `territory` | território | manter para consulta regional |
| `role` | papel em história | adaptar para função em mesa: aliado, patrono, inimigo, contato |
| `description` | resumo de card | manter como texto curto de dashboard |
| `thumbnail` | card visual | manter como imagem pequena |
| `cover` | capa/card | manter como imagem grande |
| `tags` | visual/filtro | manter, mas separar tags de tipo, facção, região e status |

## 3. Novos campos necessários

Campos propostos para RPG:

| campo | função |
| --- | --- |
| `type` | tipo principal da nota: character, faction, territory, session, quest, item |
| `subtype` | subtipo: player, npc, antagonist, settlement, dungeon |
| `life_status` | alive, dead, missing, unknown, undead |
| `visibility` | Mestre, Jogadores, Público |
| `canon_status` | canon, draft, rumor, deprecated, contradiction |
| `spoiler_level` | none, light, medium, heavy |
| `player_known` | true/false |
| `gm_secret` | resumo ou booleano de segredo |
| `portrait` | retrato principal de personagem |
| `map_image` | imagem usada por mapa |
| `handout_image` | imagem entregável |
| `token_image` | token para combate/VTT |
| `sessions` | sessões em que aparece |
| `arcs` | arcos associados |
| `revealed_in` | sessão/data em que foi revelado |
| `old_dragon_class` | classe mecânica |
| `old_dragon_race` | raça mecânica |
| `level` | nível do personagem |
| `danger_level` | ameaça relativa |
| `hooks` | ganchos associados |
| `rumors` | rumores associados |
| `truth_status` | true, false, partial, unknown |
| `media_status` | active, draft, unused, archived |
| `handout_status` | hidden, ready, revealed, retired |
| `owner` | dono de item |
| `participants` | participantes de sessão/encontro |
| `in_game_date` | data diegética |
| `session_number` | número da sessão |

## 4. Campos sensíveis que exigem compatibilidade

Não remover nem substituir diretamente:

- `thumbnail`
- `cover`
- `chapters`
- `tags`
- `status`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `NoteIcon`
- `NoteStatus`
- `cssclasses`
- campos de banner

Regra: adicionar campo novo primeiro, manter campo antigo, criar consultas compatíveis, validar visualmente, só depois considerar remoção.

## 5. Campos visuais

- `thumbnail`
- `cover`
- `portrait`
- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`
- `map_image`
- `handout_image`
- `token_image`
- `cssclasses`
- `NoteIcon`

## 6. Campos usados por Dataview

Campos propostos para filtros/listas:

- `type`
- `subtype`
- `status`
- `life_status`
- `visibility`
- `canon_status`
- `spoiler_level`
- `player_known`
- `location`
- `territory`
- `region`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`
- `sessions`
- `arcs`
- `hooks`
- `rumors`
- `danger_level`
- `handout_status`
- `media_status`
- `tags`

## 7. Campos usados por DataCards

Campos de cards:

- `thumbnail`
- `cover`
- `portrait`
- `status`
- `life_status`
- `location`
- `territory`
- `region`
- `faction`
- `role`
- `description`
- `date`
- `in_game_date`
- `danger_level`
- `visibility`
- `handout_status`

## 8. Campos usados por Supercharged Links

Supercharged Links depende principalmente de tags. Campos que podem ajudar no futuro, mas não devem substituir tags sem teste:

- `type`
- `subtype`
- `faction`
- `territory`
- `region`
- `life_status`
- `visibility`

Regra: manter tags visuais até criar e validar seletores equivalentes.

## 9. Campos para mestre/jogador

| campo | função |
| --- | --- |
| `visibility` | controle principal de audiência |
| `spoiler_level` | intensidade do spoiler |
| `player_known` | se os jogadores já sabem |
| `revealed_in` | quando foi revelado |
| `gm_secret` | segredo do mestre |
| `gm_notes` | notas privadas |
| `handout_status` | controle de entrega |
| `public_summary` | resumo mostrável |
| `secret_summary` | resumo privado |

## 10. Exemplo conceitual de personagem RPG

```yaml
---
type: character
subtype: npc
NoteIcon: character
NoteStatus: Draft
status: Active
life_status: alive
visibility: Mestre
canon_status: canon
spoiler_level: medium
player_known: false
thumbnail: zz_media/th_npc.png
portrait: zz_media/npc.png
location: "[[Some Location]]"
territory: "[[Some Territory]]"
district:
faction: "[[Some Faction]]"
religion:
role: informant
chapters:
sessions:
arcs:
hooks:
rumors:
tags:
  - character
  - npc
---
```

## 11. Exemplo conceitual de sessão RPG

```yaml
---
type: session
subtype: campaign_session
status: planned
visibility: Mestre
cover: zz_media/session-cover.png
date: 2026-06-26
in_game_date:
session_number: 1
arcs:
participants:
description: Session summary for dashboard.
tags:
  - session
  - story
---
```

## 12. Observação de desenho

Campos finais só devem ser decididos depois de mapear o vault RPG real que receberá a migração. Este documento define o vocabulário candidato, não uma regra aplicada.
