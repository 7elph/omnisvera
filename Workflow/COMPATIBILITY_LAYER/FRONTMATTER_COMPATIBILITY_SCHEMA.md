> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Frontmatter Compatibility Schema

Este schema define os campos que devem coexistir durante a transição do Omnisvera para o modelo RPG.

Regra central: não remover campos antigos no mesmo passo em que campos novos são adicionados.

## Campos herdados que devem ser preservados

Estes campos podem alimentar Dataview, DataCards, Supercharged Links, snippets, Home/dashboard ou convenções herdadas. Eles não devem ser removidos durante a camada de compatibilidade.

| campo | função | regra de compatibilidade |
| --- | --- | --- |
| `obsidianUIMode` | Modo visual da nota. | Preservar onde existir. |
| `NoteIcon` | Ícone/convenção visual. | Preservar até validação de Icon Folder/snippets. |
| `NoteStatus` | Estado editorial/template herdado. | Preservar até existir substituto documentado. |
| `thumbnail` | Imagem de cards/listagens/DataCards. | Não substituir por `cover` ou `portrait`. |
| `cover` | Capa/visual amplo/cards de território/lore/local. | Manter separado de `thumbnail`. |
| `status` | Estado narrativo/operacional/editorial amplo. | Manter; complementar com `life_status` quando necessário. |
| `location` | Localização atual/origem. | Preservar para consultas. |
| `territory` | Território/região associada. | Preservar para consultas e cards. |
| `district` | Distrito ou subdivisão. | Preservar onde existir. |
| `faction` | Facção associada. | Preservar mesmo quando tags forem adicionadas. |
| `religion` | Religião/culto/crença. | Preservar onde existir. |
| `role` | Papel narrativo. | Preservar em personagens e NPCs. |
| `chapters` | Aparições herdadas. | Manter como compatibilidade. |
| `tags` | Tags visuais, técnicas e organizacionais. | Não remover; adicionar tags novas em paralelo. |
| `cssclasses` | Classes CSS por nota. | Preservar até validação visual. |

## Campos RPG novos permitidos

Estes campos podem ser adicionados gradualmente, sem remover os herdados.

| campo | função RPG | obrigatório no primeiro lote? | observação |
| --- | --- | --- | --- |
| `type` | Tipo estrutural da nota. | Recomendado | Não substitui tags. |
| `subtype` | Subtipo estrutural. | Recomendado por template | Não substitui tags. |
| `visibility` | Escopo mestre/jogador/público. | Recomendado | Necessário para dashboards seguros. |
| `spoiler_level` | Nível de spoiler. | Opcional inicial | Útil para conteúdo público futuro. |
| `player_known` | Se os jogadores conhecem. | Opcional inicial | Booleano. |
| `gm_secret` | Se contém segredo do mestre. | Opcional inicial | Booleano. |
| `revealed_in` | Sessão/capítulo em que foi revelado. | Opcional inicial | Pode apontar para sessão. |
| `sessions` | Aparições por sessão RPG. | Recomendado | Deve coexistir com `chapters`. |
| `arcs` | Arcos de campanha. | Opcional | Pode vir depois. |
| `portrait` | Retrato de personagem. | Opcional | Não substitui `thumbnail`. |
| `map_image` | Imagem base de mapa. | Opcional | Usar em mapas/locais específicos. |
| `handout_image` | Imagem liberável para jogadores. | Opcional | Exige visibilidade/handout. |
| `token_image` | Token de mesa/VTT. | Opcional | Não obrigatório. |
| `life_status` | Vivo, morto, desaparecido etc. | Recomendado para personagens | Não substitui `status`. |
| `old_dragon_class` | Classe Old Dragon. | Opcional | Não obrigatório no primeiro lote. |
| `old_dragon_race` | Raça Old Dragon. | Opcional | Não obrigatório no primeiro lote. |
| `level` | Nível. | Opcional | Útil para jogadores e ameaças. |
| `danger_level` | Perigo de ameaça/local/encontro. | Opcional | Pode vir depois. |
| `hooks` | Ganchos ligados. | Opcional | Pode ser lista ou link. |
| `rumors` | Rumores ligados. | Opcional | Pode ser lista ou link. |

## Exemplo compatível para personagem

```yaml
---
obsidianUIMode: preview
NoteIcon:
NoteStatus:
type: character
subtype: npc_important
thumbnail: zz_media/exemplo-thumb.png
cover: zz_media/exemplo-cover.png
portrait: zz_media/exemplo-portrait.png
status: Active
life_status: Alive
visibility: Mestre
spoiler_level: heavy
player_known: false
gm_secret: true
revealed_in:
location:
territory:
district:
faction:
religion:
role:
chapters:
  - 01 - Nome do Capítulo
sessions:
  - Sessão 01
old_dragon_class:
old_dragon_race:
level:
tags:
  - character
  - individual
  - npc
cssclasses:
---
```

## Regras de migração futura

- Adicionar campos novos primeiro.
- Atualizar queries para aceitar antigo e novo.
- Validar visualmente.
- Só discutir remoção de campo antigo em fase final.
- Não transformar campos opcionais em obrigatórios sem piloto validado.
