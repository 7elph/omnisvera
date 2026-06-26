# OMNISVERA OBSIDIAN DEPENDENCY MAP

Gerado em: 2026-06-26 14:06.

Escopo: vault Omnisvera atual. Sem comparação com Disgraceland ou modelo RPG. Sem correções aplicadas.

## Escopo obrigatório

| caminho | existe |
| --- | --- |
| .obsidian | sim |
| .obsidian/plugins | sim |
| .obsidian/snippets | sim |
| Characters | sim |
| Factions | sim |
| Territories | sim |
| Locations | sim |
| Lore | sim |
| Religion | sim |
| Narrative | não |
| CAMPANHA | não |
| Templates | sim |
| Workflow | sim |
| Home.md | sim |
| OMNISVERA.md | sim |
| TIMELINE.md | sim |
| MAPA DE NIMALIA.md | sim |
| zz_media | sim |

## Resumo estrutural

| área | quantidade |
| --- | --- |
| Calendar/Timeline | 2 |
| Characters | 14 |
| Classes | 6 |
| EARTHROPO | 5 |
| Factions | 9 |
| Home/Dashboard | 1 |
| Index | 1 |
| Items | 8 |
| Locations | 8 |
| Lore | 7 |
| Map | 2 |
| Other | 17 |
| Races | 7 |
| Religion | 4 |
| Templates | 8 |
| Territories | 5 |
| Workflow | 44 |
| notas Markdown auditadas | 148 |
| mídias em zz_media | 75 |
| plugins instalados | 27 |
| plugins ativos | 20 |
| snippets CSS | 13 |
| snippets ativos | 11 |
| blocos Dataview | 41 |
| blocos DataCards | 18 |
| blocos Leaflet | 2 |
| blocos Calendarium | 2 |
| marcadores Leaflet em JSON | 84 |
| eventos Calendarium | 0 |

## Campos críticos observados

| campo | encontrado | ocorrências | Dataview | DataCards | exemplos |
| --- | --- | --- | --- | --- | --- |
| thumbnail | sim | 22 | 18 | 6 | zz_media/th_dukeofd.png, zz_media/th_elarion.PNG, zz_media/th_cassian.PNG, zz_media/th_mira.PNG +1 |
| cover | sim | 46 | 1 | 12 | zz_media/t52.png, zz_media/alquimista.png, zz_media/clerigo.png, zz_media/guerreiro.png +1 |
| chapters | sim | 8 | 7 | 0 | 00 - O Retorno de Raziel, 00 - O Corvo da Maré Baixa |
| sessions | não | 0 | 0 | 0 | — |
| tags | sim | 119 | 3 | 0 | coroa, character, paladin, antropo, antagonist, chapter01, nimalia, earthropo, Category/Character, character, creature, dragon, draft, npc, character, elf, mentor, missing, mystery, chapter00, coroa, character, paladin, antropo, military, nimalia, earthropo, chapter00, chapter01 +1 |
| status | sim | 87 | 7 | 12 | Em revisão, Vivo, Em desenvolvimento, Desaparecido +1 |
| location | sim | 26 | 16 | 5 | [[Nimalia]], [[Leth'valora]], [[Maré Baixa]] +1 |
| territory | sim | 23 | 3 | 2 | [[Nimalia]], [[Floresta de Avenor]] +3 |
| faction | sim | 19 | 15 | 0 | [[Coroa de Nimalia]], [[Sentinelas de Leth'valora]] +1 |
| NoteIcon | sim | 107 | 0 | 0 | lore, magicitem, character +2 |
| NoteStatus | sim | 89 | 2 | 2 | In progress, New, Draft, Complete +1 |
| obsidianUIMode | sim | 73 | 0 | 0 | preview +4 |
| cssclasses | sim | 6 | 0 | 0 | b-sides-script, chapter, character/Raziel, character/Ancião Primordial, b-sides-script, chapter, character/Vezemir, character/Elarion Vaelthor, character/Mira Valen, character/Padre Oric, character/General Cassian Valerius, b-sides-script, chapter, character/Varkh Nimalis, character/Mestre Odran Veyl, religion +1 |
| banner | sim | 1 | 0 | 0 | [[zz_media/avenor.png]] |
| banner-x | sim | 1 | 0 | 0 | 51 |
| banner-y | sim | 1 | 0 | 0 | 34 |
| banner-height | sim | 1 | 0 | 0 | 280 |
| content-start | sim | 1 | 0 | 0 | 271 |
| banner-fade | sim | 1 | 0 | 0 | -45 |

## Plugins principais

| plugin | nome | ativo | arquivos | config | chaves config | campos/propriedades | risco | exemplos |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| advanced-progress-bars | Advanced Progress Bars | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/advanced-progress-bars/data.json | APB_title, APB_total, APB_progressBarPercentage, APB_widthToggle, APB_width, APB_height, APB_endcapToggle, APB_marksToggle, APB_autoMarksToggle, APB_manualMarks, APB_marksColor, APB_marksLightColor, APB_marksWidth, APB_titleToggle, APB_titleColor, APB_titleLightColor +66 | — | Baixo/indireto | — |
| automatic-table-of-contents | automatic-table-of-contents | não | — | — | — | — | Baixo/indireto | — |
| calendarium | Calendarium | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/calendarium/data.json | autoParse, calendars, configDirectory, dailyNotes, dateFormat, defaultCalendar, eventPreview, exit, eventFrontmatter, parseDates, version, debug, askedToMoveFC, askedAboutSync, syncBehavior, inlineEventsTag +1 | events, calendar, date | Médio/alto: calendário depende de JSON/blocos | CALENDAR.md, Home.md |
| chronos | Chronos Timeline | sim | manifest.json, main.js, styles.css | — | — | — | Baixo/indireto | — |
| copilot | copilot | não | — | — | — | — | Baixo/indireto | — |
| data-cards | DataCards | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/data-cards/data.json | preset, imageProperty, imageHeight, imageFit, properties, exclude, scrollableProperties, contentHeight, showLabels, cardSpacing, enableShadows, propertiesAlign, titleAlign, fontSize, truncateText, booleanDisplayMode +19 | NoteStatus, chapter, class, cover, date, description, info, item, leader, location +8 | Alto: cards dependem de imageProperty/campos/tags | Characters/Individual/Raziel.md, Characters/Individual/Vezemir.md, CULTURE.md, EARTHROPO/00 - As Crônicas de Névoa de Sangue.md, EARTHROPO/00 - O Bastardo de Ferro.md, EARTHROPO/00 - O Corvo da Maré Baixa.md, EARTHROPO/EARTHROPO.md, Factions/Guarda Real de Nimalia.md +10 |
| dataview | Dataview | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/dataview/data.json | renderNullAs, taskCompletionTracking, taskCompletionUseEmojiShorthand, taskCompletionText, taskCompletionDateFormat, recursiveSubTaskCompletion, warnOnEmptyResult, refreshEnabled, refreshInterval, defaultDateFormat, defaultDateTimeFormat, maxRecursiveRenderDepth, tableIdColumnName, tableGroupColumnName, showResultCount, allowHtml +9 | Alignment, Community-Size, Government, NoteIcon, NoteStatus, aliases, alignment, arcs, armor_allowed, banner +73 | Alto: consultas dependem de campos, tags e pastas | Characters/Individual/Augustus Terra Decimus.md, Characters/Individual/General Cassian Valerius.md, Home.md, Locations/Leth'valora.md, NOTES.md, Templates/Characters/Antagonista.md, Templates/Characters/Criatura.md, Templates/Characters/NPC Importante.md +33 |
| highlightr-plugin | Highlightr | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/highlightr-plugin/data.json | highlighterStyle, highlighterMethods, highlighters, highlighterOrder | — | Baixo/indireto | — |
| homepage | Homepage | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/homepage/data.json | version, homepages, separateMobile | Home.md | Médio/alto: dashboard de entrada | Home.md |
| local-backup | local-backup | não | — | — | — | — | Baixo/indireto | — |
| media-extended | Media Extended | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/media-extended/data.json | defaultVolume, devices, defaultMxLinkClick, linkHandler, speedStep, loadStrategy, timestampTemplate, screenshotTemplate, screenshotEmbedTemplate, insertBefore, timestampOffset, biliDefaultQuality, screenshotFormat, enableSubtitle, urlMappingData | — | Baixo/indireto | — |
| notebook-navigator | notebook-navigator | não | — | — | — | — | Baixo/indireto | — |
| obsidian-charts | Charts | sim | manifest.json, main.js, styles.css | — | — | — | Baixo/indireto | — |
| obsidian-icon-folder | Iconize | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian-icon-folder/data.json | settings | NoteIcon | Médio visual | CALENDAR.md, Characters/Individual/Augustus Terra Decimus.md, Characters/Individual/Dragão de Colar Dourado.md, Characters/Individual/Elarion Vaelthor.md, Characters/Individual/General Cassian Valerius.md, Characters/Individual/Kaelen, o Flagelo.md, Characters/Individual/Lorde Malakar.md, Characters/Individual/Mestre Odran Veyl.md +99 |
| obsidian-leaflet-plugin | Leaflet | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian-leaflet-plugin/data.json | mapMarkers, defaultMarker, markerIcons, color, lat, long, notePreview, layerMarkers, previousVersion, version, warnedAboutMapMarker, copyOnClick, displayMarkerTooltips, displayOverlayTooltips, configDirectory, mapViewEnabled +7 | link, layer, image | Alto: mapa depende de links e imagens | MAPA DE EARTHROPO.md, MAPA DE NIMALIA.md |
| obsidian-minimal-settings | Minimal Theme Settings | sim | manifest.json, data.json, main.js | .obsidian/plugins/obsidian-minimal-settings/data.json | lightStyle, darkStyle, lightScheme, darkScheme, editorFont, lineHeight, lineWidth, lineWidthWide, maxWidth, textNormal, textSmall, imgGrid, imgWidth, tableWidth, iframeWidth, mapWidth +16 | — | Baixo/indireto | — |
| obsidian-regex-replace | Regex Find/Replace | sim | manifest.json, main.js, styles.css | — | — | — | Baixo/indireto | — |
| obsidian-style-settings | Style Settings | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian-style-settings/data.json | supercharged-links@@ce91-5784-color, supercharged-links@@ce91-5784-weight, supercharged-links@@f884-7b00-color, supercharged-links@@f884-7b00-weight, supercharged-links@@e997-0713-color, supercharged-links@@e997-0713-weight, supercharged-links@@7e5f-283b-color, supercharged-links@@3623-52e1-color, supercharged-links@@3623-52e1-weight, supercharged-links@@4740-17da-color, supercharged-links@@4740-17da-weight, supercharged-links@@7457-fe20-color, supercharged-links@@7457-fe20-weight, supercharged-links@@15ae-9b1f-color, supercharged-links@@15ae-9b1f-weight, supercharged-links@@7e5f-283b-weight +23 | supercharged uid, snippet settings | Alto visual | — |
| obsidian42-brat | BRAT | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/obsidian42-brat/data.json | pluginList, pluginSubListFrozenVersion, themesList, updateAtStartup, updateThemesAtStartup, enableAfterInstall, loggingEnabled, loggingPath, loggingVerboseEnabled, debuggingMode, notificationsEnabled, personalAccessToken | — | Baixo/indireto | — |
| open-vscode | Open vault in VSCode | sim | manifest.json, main.js | — | — | — | Baixo/indireto | — |
| pexels-banner | pexels-banner | não | — | — | — | — | Baixo/indireto | — |
| phrasesync | PhraseSync | sim | manifest.json, main.js, styles.css | — | — | — | Baixo/indireto | — |
| smart-composer | smart-composer | não | — | — | — | — | Baixo/indireto | — |
| supercharged-links-obsidian | Supercharged Links | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/supercharged-links-obsidian/data.json | targetAttributes, targetTags, getFromInlineField, enableTabHeader, activateSnippet, enableEditor, enableFileList, enableBacklinks, enableQuickSwitcher, enableSuggestor, selectors | tags | Alto: tags podem controlar visual de links | — |
| templater-obsidian | Templater | sim | manifest.json, main.js, styles.css | — | — | — | Baixo/indireto | — |
| vault-full-statistics | Vault Full Statistics | sim | manifest.json, data.json, main.js, styles.css | .obsidian/plugins/vault-full-statistics/data.json | excludeDirectories, displayIndividualItems, showNotes, showAttachments, showFiles, showLinks, showWords, showSize, showQuality, showTags | — | Baixo/indireto | — |
| waveform-player | waveform-player | não | — | — | — | — | Baixo/indireto | — |

## Sistemas técnicos detectados

| sistema | evidência | risco técnico |
| --- | --- | --- |
| Dataview | 41 blocos | campos/pastas/tags em consultas |
| DataCards | 18 blocos | imageProperty, thumbnail/cover e tags |
| Supercharged Links | 13 seletores configurados | tags visuais |
| Style Settings | data.json presente | cores/pesos/tema |
| Leaflet | 2 blocos; 84 marcadores JSON | links e imagem base |
| Calendarium | 1 calendários; 0 eventos | eventos e datas |
| Homepage | plugin ativo | Home/dashboard |
| Mídia | 75 arquivos; 40 referenciados textualmente | referências quebradas/órfãs |