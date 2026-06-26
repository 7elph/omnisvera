# DISGRACELAND TEMPLATE INDEX

Este índice resume os contratos técnicos de template do vault legado Disgraceland.

Escopo: `Workflow/Legacy/Disgraceland`.

Não há comparação com Omnisvera neste documento.

## Tabela de templates

| template | tipo de nota | pasta | campos críticos | plugins envolvidos | risco de migração |
| --- | --- | --- | --- | --- | --- |
| `CHARACTER_TEMPLATE_CONTRACT.md` | Personagem | `Characters/**` | `tags`, `thumbnail`, `status`, `location`, `territory`, `district`, `faction`, `religion`, `role`, `chapters` | Dataview, DataCards, Supercharged Links | Alto: `chapters`, `thumbnail` e tags visuais quebram aparições/cards/cores |
| `FACTION_TEMPLATE_CONTRACT.md` | Facção | `Factions` | `tags`, `thumbnail`, `leader`, `status`, `location`, `faction` | DataCards, Supercharged Links, Style Settings | Alto: tag principal alimenta DataCards e link styling |
| `TERRITORY_TEMPLATE_CONTRACT.md` | Território | `Territories` | `tags`, `cover`, `leader`, `region`, `population`, `Alignment`, `Government`, `size` | Dataview, DataCards, Supercharged Links | Alto: Home e residentes dependem de tags/campos |
| `LOCATION_TEMPLATE_CONTRACT.md` | Local | `Locations` | `tags`, `cover`, `territory`, `district`, `info`, `status` | DataCards, Supercharged Links | Médio/alto: Home depende de `#location`, `cover`, `territory`, `info` |
| `LORE_TEMPLATE_CONTRACT.md` | Lore | `Lore` | `tags`, `cover`, `info`, `NoteIcon`, `status`, `location`, `faction`, `cssclasses` | Supercharged Links, DataCards quando aplicável | Médio: estrutura varia; tags e callouts não devem ser normalizados cegamente |
| `RELIGION_TEMPLATE_CONTRACT.md` | Religião | `Religion` | `tags`, `cssclasses`, `NoteIcon`, `cover` quando existir | Supercharged Links, Style Settings, snippets | Médio/alto: `religion` e `cssclasses` afetam visual |
| `CHAPTER_TEMPLATE_CONTRACT.md` | Capítulo/B-Side | `DISGRACELAND/**` | `tags`, `cover`, `date`, `description`, `cssclasses` | DataCards, Dataview, Calendarium | Alto: nome do arquivo e tags de capítulo alimentam aparições/elenco |
| `HOME_DASHBOARD_TEMPLATE_CONTRACT.md` | Dashboard | `Home.md` | `banner*`, `cover`, `thumbnail`, `status`, `role`, `district`, `territory`, `faction`, `religion`, `date`, `description`, `info` | Homepage, Dataview, DataCards, Calendarium | Muito alto: Home agrega vários sistemas |
| `CALENDAR_TEMPLATE_CONTRACT.md` | Calendário | `CALENDAR.md` + Calendarium JSON | `obsidianUIMode`, `NoteIcon`, `cover`, `tag`, eventos JSON | Calendarium, Style Settings | Alto: eventos apontam para notas específicas |
| `MAP_TEMPLATE_CONTRACT.md` | Mapa | `TRIBUCIA MAP.md` + Leaflet JSON | `width`, `height`, `scale`, `distance`, `cover`, `tags`, `image`, `id` | Leaflet | Muito alto: marcadores dependem de links e imagem base |
| `MEDIA_REFERENCE_TEMPLATE_CONTRACT.md` | Referência de mídia | `zz_media` + notas | `thumbnail`, `cover`, `banner`, embeds, HTML img, Leaflet image | DataCards, Dataview, Leaflet, Homepage | Alto: mover/converter/apagar mídia quebra visual |

## Campos críticos por família

Personagens:

- `tags`
- `thumbnail`
- `status`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`

Facções:

- `tags`
- `thumbnail`
- `leader`
- `status`
- `location`
- `faction`

Territórios:

- `tags`
- `cover`
- `leader`
- `region`
- `population`
- `Alignment`
- `Government`
- `reputation`
- `politics`
- `size`
- `religion`
- `exports`
- `imports`

Locais:

- `tags`
- `cover`
- `territory`
- `district`
- `info`
- `status`

Lore/religião:

- `tags`
- `cover`
- `info`
- `cssclasses`
- `NoteIcon`

Capítulos:

- `tags`
- `cover`
- `date`
- `description`
- `cssclasses`

Home:

- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`

Mapa/calendário:

- `tag`
- `width`
- `height`
- `scale`
- `distance`
- `image`
- `id`

## Lacunas conhecidas

- Alguns campos vazios podem ser placeholders de template e não devem ser removidos automaticamente.
- Algumas imagens aparentemente órfãs podem ser usadas por CSS, Canvas, JSON de plugin ou HTML.
- Algumas tags inline não aparecem apenas no frontmatter.
- `CALENDAR.md` usa `tag`, singular, e isso deve ser preservado até validação.
- Facções podem ter inconsistências em `faction`, mas o campo ainda é técnico.
- Lore é menos uniforme; contrato deve preservar variações.

## Ordem segura de migração futura

Sem comparar com Omnisvera ainda, a ordem lógica de análise futura é:

1. Validar templates do Disgraceland.
2. Mapear templates atuais do Omnisvera.
3. Comparar campos.
4. Comparar tags.
5. Comparar snippets.
6. Comparar DataCards/Dataview.
7. Criar equivalências semânticas.
8. Criar camada de compatibilidade.
9. Migrar notas.
10. Validar visualmente no Obsidian.
11. Só então remover legado.

## Regra geral

Nada em Disgraceland deve ser considerado “só conteúdo” até passar pelos contratos técnicos. Campos, tags, pastas, nomes de arquivos, imagens e snippets funcionam juntos como uma API interna do vault.
