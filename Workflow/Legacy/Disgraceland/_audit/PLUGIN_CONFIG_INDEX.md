# PLUGIN CONFIG INDEX

Gerado em: 2026-06-26 07:40.

## community-plugins.json

```json
[
  "dataview",
  "obsidian-icon-folder",
  "chronos",
  "calendarium",
  "obsidian-leaflet-plugin",
  "homepage",
  "templater-obsidian",
  "advanced-progress-bars",
  "obsidian-charts",
  "obsidian-minimal-settings",
  "highlightr-plugin",
  "obsidian42-brat",
  "supercharged-links-obsidian",
  "data-cards",
  "vault-full-statistics",
  "obsidian-regex-replace",
  "media-extended",
  "open-vscode",
  "phrasesync",
  "obsidian-style-settings"
]
```

## Índice dos plugins

| plugin | habilitado | arquivos | configuração | função provável | campos/propriedades usadas | risco de quebra | exemplos |
| --- | --- | --- | --- | --- | --- | --- | --- |
| advanced-progress-bars | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/advanced-progress-bars/data.json | Barras de progresso customizadas. | — | Baixo/indireto. | — |
| automatic-table-of-contents | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| calendarium | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/calendarium/data.json | Calendário ficcional e eventos ligados a capítulos. | event.note, date | Médio/alto: eventos dependem do JSON e notas ligadas. | CALENDAR.md, Home.md |
| chronos | sim | manifest.json, main.js, styles.css | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| copilot | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| data-cards | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/data-cards/data.json | Renderiza consultas em cards; depende de thumbnail/cover/imageProperty. | thumbnail, cover, status, location, description, date, info, region, leader, population | Alto: campos de imagem/tags alimentam cards. | CULTURE.md, DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md, DISGRACELAND/04 - Glowing Darkness.md, DISGRACELAND/05 - Sight Unseen.md, DISGRACELAND/06 - Showdown In Gage Park.md, DISGRACELAND/07 - The Spotlight Lies.md +29 |
| dataview | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/dataview/data.json | Consulta frontmatter/tags/pastas em blocos ```dataview```. | Alignment, Community-Size, Government, NoteIcon, NoteStatus, banner, banner-fade, banner-height, banner-x, banner-y +32 | Alto: renomear campos/tags/pastas quebra consultas. | Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md, Characters/Individual/Geo Huxley.md, Characters/Individual/Hella.md +76 |
| highlightr-plugin | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/highlightr-plugin/data.json | Estilos de highlight. | — | Baixo/indireto. | — |
| homepage | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/homepage/data.json | Define a página Home do vault. | Home.md | Médio: mudar Home afeta entrada do vault. | Home.md |
| local-backup | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| media-extended | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/media-extended/data.json | Extensões para mídia/áudio/vídeo. | — | Baixo/indireto. | — |
| notebook-navigator | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| obsidian-charts | sim | manifest.json, main.js, styles.css | — | Blocos de gráficos. | — | Baixo/indireto. | — |
| obsidian-icon-folder | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian-icon-folder/data.json | Gerencia ícones visuais de pastas/notas; provável relação com NoteIcon. | NoteIcon | Médio/alto visual. | .trash/City Forces/Blueforce.md, CALENDAR.md, Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md +127 |
| obsidian-leaflet-plugin | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian-leaflet-plugin/data.json | Mapa com imagem base, marcadores, grupos e links para notas. | link, layer, zz_media/Tribucia.png | Alto: renomear notas/imagem base quebra mapa. | TRIBUCIA MAP.md |
| obsidian-minimal-settings | sim | manifest.json, data.json, main.js | .obsidian/plugins/obsidian-minimal-settings/data.json | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| obsidian-regex-replace | sim | manifest.json, main.js, styles.css | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| obsidian-style-settings | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian-style-settings/data.json | Guarda valores de cor/peso de snippets e plugins. | tags, supercharged uid | Alto para visual: contém valores de Supercharged Links. | — |
| obsidian42-brat | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian42-brat/data.json | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| open-vscode | sim | manifest.json, main.js | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| pexels-banner | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| phrasesync | sim | manifest.json, main.js, styles.css | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| smart-composer | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| supercharged-links-obsidian | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/supercharged-links-obsidian/data.json | Estiliza links por tags/propriedades via snippet gerado. | tags | Alto: tags controlam cor/peso de links. | Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md, Characters/Individual/Geo Huxley.md, Characters/Individual/Hella.md +126 |
| templater-obsidian | sim | manifest.json, main.js, styles.css | — | Templates para criação de notas. | — | Baixo/indireto. | — |
| vault-full-statistics | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/vault-full-statistics/data.json | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |
| waveform-player | não | — | — | Plugin instalado; função inferida pelo manifesto/config. | — | Baixo/indireto. | — |

## Configurações-chave


### dataview

Manifesto: `.obsidian/plugins/dataview/manifest.json`. Nome: `Dataview`. Versão: `0.5.68`.

Config: `.obsidian/plugins/dataview/data.json`. Chaves: renderNullAs, taskCompletionTracking, taskCompletionUseEmojiShorthand, taskCompletionText, taskCompletionDateFormat, recursiveSubTaskCompletion, warnOnEmptyResult, refreshEnabled, refreshInterval, defaultDateFormat, defaultDateTimeFormat, maxRecursiveRenderDepth, tableIdColumnName, tableGroupColumnName, showResultCount, allowHtml, inlineQueryPrefix, inlineJsQueryPrefix, inlineQueriesInCodeblocks, enableInlineDataview +5.


### data-cards

Manifesto: `.obsidian/plugins/data-cards/manifest.json`. Nome: `DataCards`. Versão: `1.0.4`.

Config: `.obsidian/plugins/data-cards/data.json`. Chaves: preset, imageProperty, imageHeight, imageFit, properties, exclude, scrollableProperties, contentHeight, showLabels, cardSpacing, enableShadows, propertiesAlign, titleAlign, fontSize, truncateText, booleanDisplayMode, showBooleanLabels, booleanTrueText, booleanFalseText, enableClickableCards +15.


### supercharged-links-obsidian

Manifesto: `.obsidian/plugins/supercharged-links-obsidian/manifest.json`. Nome: `Supercharged Links`. Versão: `0.12.1`.

Config: `.obsidian/plugins/supercharged-links-obsidian/data.json`. Seletores: 13. `targetTags`: True. `activateSnippet`: True.


### obsidian-style-settings

Manifesto: `.obsidian/plugins/obsidian-style-settings/manifest.json`. Nome: `Style Settings`. Versão: `1.0.9`.

Config: `.obsidian/plugins/obsidian-style-settings/data.json`. Chaves: supercharged-links@@ce91-5784-color, supercharged-links@@ce91-5784-weight, supercharged-links@@f884-7b00-color, supercharged-links@@f884-7b00-weight, supercharged-links@@e997-0713-color, supercharged-links@@e997-0713-weight, supercharged-links@@7e5f-283b-color, supercharged-links@@3623-52e1-color, supercharged-links@@3623-52e1-weight, supercharged-links@@4740-17da-color, supercharged-links@@4740-17da-weight, supercharged-links@@7457-fe20-color, supercharged-links@@7457-fe20-weight, supercharged-links@@15ae-9b1f-color, supercharged-links@@15ae-9b1f-weight, supercharged-links@@7e5f-283b-weight, supercharged-links@@7eac-9a5f-color, supercharged-links@@7eac-9a5f-weight, supercharged-links@@6e9a-b654-color, supercharged-links@@6e9a-b654-weight +19.


### obsidian-icon-folder

Manifesto: `.obsidian/plugins/obsidian-icon-folder/manifest.json`. Nome: `Iconize`. Versão: `2.14.7`.

Config: `.obsidian/plugins/obsidian-icon-folder/data.json`. Chaves: settings.


### calendarium

Manifesto: `.obsidian/plugins/calendarium/manifest.json`. Nome: `Calendarium`. Versão: `2.0.0`.

Config: `.obsidian/plugins/calendarium/data.json`. Calendários: 1. Eventos: 22.


### obsidian-leaflet-plugin

Manifesto: `.obsidian/plugins/obsidian-leaflet-plugin/manifest.json`. Nome: `Leaflet`. Versão: `6.0.5`.

Config: `.obsidian/plugins/obsidian-leaflet-plugin/data.json`. Mapas: 1. Marcadores: 82. Ícones: 13.


### homepage

Manifesto: `.obsidian/plugins/homepage/manifest.json`. Nome: `Homepage`. Versão: `4.2.2`.

Config: `.obsidian/plugins/homepage/data.json`. Chaves: version, homepages, separateMobile.


### templater-obsidian

Manifesto: `.obsidian/plugins/templater-obsidian/manifest.json`. Nome: `Templater`. Versão: `2.12.0`.

Sem `data.json` detectado.


### highlightr-plugin

Manifesto: `.obsidian/plugins/highlightr-plugin/manifest.json`. Nome: `Highlightr`. Versão: `1.2.2`.

Config: `.obsidian/plugins/highlightr-plugin/data.json`. Chaves: highlighterStyle, highlighterMethods, highlighters, highlighterOrder.


### advanced-progress-bars

Manifesto: `.obsidian/plugins/advanced-progress-bars/manifest.json`. Nome: `Advanced Progress Bars`. Versão: `1.1.2`.

Config: `.obsidian/plugins/advanced-progress-bars/data.json`. Chaves: APB_title, APB_total, APB_progressBarPercentage, APB_widthToggle, APB_width, APB_height, APB_endcapToggle, APB_marksToggle, APB_autoMarksToggle, APB_manualMarks, APB_marksColor, APB_marksLightColor, APB_marksWidth, APB_titleToggle, APB_titleColor, APB_titleLightColor, APB_percentageToggle, APB_percentageColor, APB_percentageLightColor, APB_fractionToggle +62.


### obsidian-charts

Manifesto: `.obsidian/plugins/obsidian-charts/manifest.json`. Nome: `Charts`. Versão: `3.9.0`.

Sem `data.json` detectado.


### media-extended

Manifesto: `.obsidian/plugins/media-extended/manifest.json`. Nome: `Media Extended`. Versão: `3.2.6`.

Config: `.obsidian/plugins/media-extended/data.json`. Chaves: defaultVolume, devices, defaultMxLinkClick, linkHandler, speedStep, loadStrategy, timestampTemplate, screenshotTemplate, screenshotEmbedTemplate, insertBefore, timestampOffset, biliDefaultQuality, screenshotFormat, enableSubtitle, urlMappingData.


## Campos detectados em Dataview/DataCards

| campo | Dataview | DataCards | função provável |
| --- | --- | --- | --- |
| chapters | 75 | 0 | Lista de aparições; consultada por Dataview com file.name. |
| cover | 0 | 15 | Imagem de capa usada por DataCards, Home, territórios e locais. |
| date | 2 | 7 | Data de capítulo/story; usada em cards recentes. |
| description | 0 | 7 | Descrição curta de capítulo/card. |
| district | 1 | 0 | Distrito mostrado no dashboard de personagens. |
| faction | 8 | 0 | Facção exibida e usada para agrupamento. |
| file.folder | 1 | 0 | Campo de frontmatter do template; não classificado como descartável. |
| file.mtime | 2 | 0 | Campo de frontmatter do template; não classificado como descartável. |
| file.name | 78 | 0 | Campo de frontmatter do template; não classificado como descartável. |
| file.path | 1 | 0 | Campo de frontmatter do template; não classificado como descartável. |
| info | 0 | 6 | Resumo curto para cards de Locations. |
| leader | 0 | 1 | Líder mostrado em cards de facções/territórios. |
| location | 7 | 23 | Localização usada em dashboards e consultas de residentes. |
| population | 0 | 1 | População mostrada em cards de territórios. |
| region | 0 | 1 | Região mostrada em cards de territórios. |
| religion | 3 | 0 | Religião exibida no dashboard de personagens. |
| role | 1 | 0 | Papel mostrado no dashboard de personagens. |
| status | 8 | 26 | Status narrativo e campo consultado/exibido. |
| tags | 3 | 0 | Organização, Dataview/DataCards e Supercharged Links. |
| territory | 1 | 2 | Território exibido/consultado. |
| thumbnail | 3 | 22 | Imagem pequena usada por DataCards/Home/personagens/facções. |
| width | 3 | 0 | Campo de frontmatter do template; não classificado como descartável. |