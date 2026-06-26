# DISGRACELAND OBSIDIAN DEPENDENCY MAP

Gerado em: 2026-06-26 07:40.

Escopo: `Workflow/Legacy/Disgraceland`. Esta é arqueologia técnica: sem comparação com Omnisvera, sem correção e sem padronização.

## Resumo estrutural

| área | quantidade |
| --- | --- |
| Calendar/Map | 2 |
| Chapters/B-Sides | 12 |
| Characters | 75 |
| Factions | 7 |
| Home/Dashboard | 1 |
| Locations | 9 |
| Lore | 27 |
| Other | 28 |
| Religion | 5 |
| Territories | 7 |
| mídias em zz_media | 425 |
| plugins instalados | 27 |
| plugins habilitados | 20 |
| snippets CSS | 13 |
| blocos Dataview | 84 |
| blocos DataCards | 37 |
| marcadores Leaflet | 82 |
| eventos Calendarium | 22 |

## Funcionamento técnico geral

Disgraceland funciona como um vault orientado por metadados. As notas narrativas dependem de YAML, tags e mídia; a interface depende de Dataview, DataCards, Supercharged Links, snippets CSS, Calendarium, Leaflet e Homepage.

Campos como `thumbnail`, `cover`, `chapters`, `location`, `territory`, `faction`, `role`, `date`, `description`, `leader`, `population` e `region` alimentam visual e consultas. Tags como `loyalist`, `rancher`, `third`, `pirate`, `widow`, `individual`, `lore`, `religion`, `territory`, `murray`, `water` e `story` são infraestrutura visual, não apenas lore.


## Plugins e dependências principais

| plugin | habilitado | arquivos | config | função provável | campos/propriedades | risco | exemplos |
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

## Callouts usados

| callout | ocorr. | modificadores | arquivos exemplo | CSS provável |
| --- | --- | --- | --- | --- |
| note | 125 | clean no-i right (119) | .trash/Call Out Boxes/Call Out Boxes.md, Characters/Rancher Collective/Freddy Blanchard.md, Home.md, .trash/Call Out Boxes/Call Out - Call Out Box.md, .trash/Call Out Boxes/Call Out - Read Aloud.md, Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md | dgl.css |
| infobox | 19 | left (1) | .trash/Call Out Boxes/Call Out - Left Section.md, .trash/Call Out Boxes/Call Out - Right Section.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Kullen Dane.md, Characters/Individual/Salem Quinn.md, Characters/Individual/Shana.md, Characters/Individual/The Grim Man.md, Characters/Rancher Collective/Turner Anderson.md | — |
| world | 12 | — | DISGRACELAND/DISGRACELAND.md, DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md, DISGRACELAND/04 - Glowing Darkness.md, DISGRACELAND/05 - Sight Unseen.md, DISGRACELAND/06 - Showdown In Gage Park.md, DISGRACELAND/07 - The Spotlight Lies.md | world.css |
| column | 11 | — | .trash/City Forces/Blueforce.md, Factions/Third Row.md, Lore/Blackshift Massacre.md, Lore/Darrell Douglass.md, Lore/Final Force.md, Lore/Galliah, the Stillborn Star.md, Lore/Night Time with Morris Gable.md, Lore/The Wanderers.md | — |
| warning | 4 | — | .trash/Call Out Boxes/Call Out - GM Direction.md, .trash/Call Out Boxes/Call Out Boxes.md, Legacy - Disgraceland Chapter 01 - Ghosts on the Waves.md, Lore/Tetra Bomb.md | — |
| news | 3 | — | Home.md, Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md | world.css |
| charspire | 2 | toggle (2) | Legacy - Disgraceland Scratch Notes.md, Workflow/Scratch Notes.md | — |
| example | 2 | — | .trash/Call Out Boxes/Call Out - Magic Item.md, .trash/Call Out Boxes/Call Out Boxes.md | — |
| rustwater | 2 | — | Characters/Individual/Cassidy LaRue.md, Characters/The Elite & Loyalist Guard/Emily Burton.md | — |
| tip | 2 | — | .trash/Call Out Boxes/Call Out - Flavor.md, .trash/Call Out Boxes/Call Out Boxes.md | dgl.css |
| [[eo.png\ | 1 | sban htiny ctr (1) | Home.md | — |
| [[mapp.png\ | 1 | sban htiny ctr (1) | Home.md | — |
| [[news1.png\ | 1 | sban htiny ctr (1) | Home.md | — |
| [[sool.png\ | 1 | sban htiny ctr p+t (1) | Home.md | — |
| [[t2.png\ | 1 | sban htiny ctr (1) | Home.md | — |
| abstract | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |
| bug | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |
| cards | 1 | 5 (1) | Home.md | — |
| danger | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |
| failure | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |
| hollow | 1 | — | Locations/Hollow House.md | — |
| home | 1 | — | Home.md | world.css |
| info | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | dgl.css |
| question | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |
| quote | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |
| success | 1 | — | .trash/Call Out Boxes/Call Out Boxes.md | — |

## Mídia

| categoria | quantidade |
| --- | --- |
| arquivos em zz_media | 425 |
| referências resolvidas em Markdown/frontmatter | 277 |
| referências não resolvidas | 22 |
| possíveis órfãs por análise textual | 148 |

## Campos críticos

| campo | ocorr. | tipos de nota | Dataview | DataCards | função | remoção futura |
| --- | --- | --- | --- | --- | --- | --- |
| tags | 154 | Characters (75), Lore (27), Chapters/B-Sides (12), Other (11), Locations (9), Factions (7), Territories (7), Religion (5) +1 | 3 | 0 | Organização, Dataview/DataCards e Supercharged Links. | Não remover sem migração/teste. |
| NoteIcon | 135 | Characters (75), Lore (25), Locations (8), Other (7), Factions (7), Territories (7), Religion (4), Calendar/Map (2) | 0 | 0 | Ícone visual da nota/pasta; provável dependência de Icon Folder/tema. | Não remover sem migração/teste. |
| obsidianUIMode | 124 | Characters (75), Lore (25), Locations (8), Other (7), Factions (7), Calendar/Map (1), Home/Dashboard (1) | 0 | 0 | Força modo preview/visualização. | Não remover sem migração/teste. |
| NoteStatus | 123 | Characters (75), Lore (25), Locations (8), Other (7), Factions (7), Calendar/Map (1) | 0 | 0 | Estado editorial/template. | Só considerar após checar CSS/plugins/templates. |
| status | 121 | Characters (75), Lore (23), Locations (9), Other (7), Factions (6), Calendar/Map (1) | 8 | 26 | Status narrativo e campo consultado/exibido. | Não remover sem migração/teste. |
| faction | 89 | Characters (75), Factions (7), Lore (5), Other (1), Calendar/Map (1) | 8 | 0 | Facção exibida e usada para agrupamento. | Não remover sem migração/teste. |
| location | 89 | Characters (75), Factions (7), Lore (5), Other (1), Calendar/Map (1) | 7 | 23 | Localização usada em dashboards e consultas de residentes. | Não remover sem migração/teste. |
| religion | 84 | Characters (75), Territories (6), Other (1), Factions (1), Calendar/Map (1) | 3 | 0 | Religião exibida no dashboard de personagens. | Não remover sem migração/teste. |
| thumbnail | 84 | Characters (75), Factions (7), Other (1), Lore (1) | 3 | 22 | Imagem pequena usada por DataCards/Home/personagens/facções. | Não remover sem migração/teste. |
| cover | 81 | Lore (27), Characters (15), Chapters/B-Sides (12), Locations (9), Other (8), Territories (7), Calendar/Map (2), Religion (1) | 0 | 15 | Imagem de capa usada por DataCards, Home, territórios e locais. | Não remover sem migração/teste. |
| territory | 76 | Characters (67), Locations (9) | 1 | 2 | Território exibido/consultado. | Não remover sem migração/teste. |
| chapters | 75 | Characters (75) | 75 | 0 | Lista de aparições; consultada por Dataview com file.name. | Não remover sem migração/teste. |
| role | 75 | Characters (75) | 1 | 0 | Papel mostrado no dashboard de personagens. | Não remover sem migração/teste. |
| district | 71 | Characters (62), Locations (9) | 1 | 0 | Distrito mostrado no dashboard de personagens. | Não remover sem migração/teste. |
| info | 48 | Lore (27), Characters (12), Locations (9) | 0 | 6 | Resumo curto para cards de Locations. | Não remover sem migração/teste. |
| cssclasses | 21 | Chapters/B-Sides (12), Other (5), Religion (4) | 0 | 0 | Classes CSS aplicadas à nota. | Não remover sem migração/teste. |
| leader | 13 | Factions (7), Territories (6) | 0 | 1 | Líder mostrado em cards de facções/territórios. | Não remover sem migração/teste. |
| date | 12 | Chapters/B-Sides (11), Other (1) | 2 | 7 | Data de capítulo/story; usada em cards recentes. | Não remover sem migração/teste. |
| description | 12 | Chapters/B-Sides (11), Other (1) | 0 | 7 | Descrição curta de capítulo/card. | Não remover sem migração/teste. |
| Alignment | 8 | Territories (7), Calendar/Map (1) | 0 | 0 | Classificação moral/política de território. | Só considerar após checar CSS/plugins/templates. |
| exports | 7 | Territories (6), Calendar/Map (1) | 0 | 0 | Economia de território. | Só considerar após checar CSS/plugins/templates. |
| Government | 7 | Territories (6), Calendar/Map (1) | 0 | 0 | Forma de governo. | Só considerar após checar CSS/plugins/templates. |
| imports | 7 | Territories (6), Calendar/Map (1) | 0 | 0 | Economia de território. | Só considerar após checar CSS/plugins/templates. |
| politics | 7 | Territories (6), Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| population | 7 | Territories (6), Calendar/Map (1) | 0 | 1 | População mostrada em cards de territórios. | Não remover sem migração/teste. |
| region | 7 | Territories (6), Calendar/Map (1) | 0 | 1 | Região mostrada em cards de territórios. | Não remover sem migração/teste. |
| size | 7 | Territories (6), Calendar/Map (1) | 0 | 0 | Escala/tamanho do território. | Só considerar após checar CSS/plugins/templates. |
| reputation | 6 | Territories (6) | 0 | 0 | Reputação pública/narrativa. | Só considerar após checar CSS/plugins/templates. |
| banner | 1 | Home/Dashboard (1) | 0 | 0 | Banner visual da Home/nota. | Não remover sem migração/teste. |
| banner-fade | 1 | Home/Dashboard (1) | 0 | 0 | Fade visual do banner. | Não remover sem migração/teste. |
| banner-height | 1 | Home/Dashboard (1) | 0 | 0 | Altura do banner. | Não remover sem migração/teste. |
| banner-x | 1 | Home/Dashboard (1) | 0 | 0 | Posição horizontal do banner. | Não remover sem migração/teste. |
| banner-y | 1 | Home/Dashboard (1) | 0 | 0 | Posição vertical do banner. | Não remover sem migração/teste. |
| Community-Size | 1 | Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| content-start | 1 | Home/Dashboard (1) | 0 | 0 | Offset visual do conteúdo após banner. | Não remover sem migração/teste. |
| cssclass | 1 | Lore (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| distance | 1 | Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| height | 1 | Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| scale | 1 | Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| tag | 1 | Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| type | 1 | Calendar/Map (1) | 0 | 0 | Campo de frontmatter do template; não classificado como descartável. | Só considerar após checar CSS/plugins/templates. |
| width | 1 | Calendar/Map (1) | 3 | 0 | Campo de frontmatter do template; não classificado como descartável. | Não remover sem migração/teste. |

## Relatórios especializados

- `PLUGIN_CONFIG_INDEX.md`
- `CSS_SNIPPET_INDEX.md`
- `FRONTMATTER_FIELD_MATRIX.md`
- `VISUAL_TAGS_AND_SUPERCHARGED_LINKS.md`
- `DATAVIEW_AND_DATACARDS_INDEX.md`
- `CHARACTER_STRUCTURE_MAP.md`
- `FACTION_TERRITORY_LOCATION_MAP.md`
- `CALENDAR_AND_MAP_SYSTEMS.md`
- `MIGRATION_RISK_REGISTER.md`


## Home/Dashboard audit detalhado

Frontmatter visual da Home:

| campo | valor |
| --- | --- |
| obsidianUIMode | preview |
| banner | "[[zz_media/big1.png]]" |
| banner-x | 51 |
| banner-y | 34 |
| banner-height | 280 |
| content-start | 271 |
| banner-fade | -45 |

Callouts da Home:

| callout | modificador | fold |
| --- | --- | --- |
| cards | 5 |  |
| [[sool.png\ | sban htiny ctr p+t |  |
| [[eo.png\ | sban htiny ctr |  |
| [[t2.png\ | sban htiny ctr |  |
| [[news1.png\ | sban htiny ctr |  |
| [[mapp.png\ | sban htiny ctr |  |
| world |  | - |
| infobox |  |  |
| news |  | + |
| home |  | + |
| note |  | + |
| note |  | - |

Blocos t?cnicos da Home:

| tipo | primeira linha | FROM consultado |
| --- | --- | --- |
| datacards | > TABLE cover FROM #home | #home |
| calendarium | > | ? |
| datacards | >TABLE cover, date, description FROM #story | #story |
| dataview | > table | "Characters" |
| datacards | > TABLE cover, region, leader, population FROM #territory | #territory |
| datacards | > TABLE cover, territory, info FROM #location | #location |
| dataview | TABLE WITHOUT ID | "/" |

Campos obrigat?rios inferidos para a Home funcionar: `cover`, `thumbnail`, `status`, `role`, `district`, `territory`, `faction`, `religion`, `date`, `description`, `tags`, al?m das tags `home`, `story`, `territory`, `location` e `character`.


## Media reference index detalhado

| tipo de uso | ocorr?ncias |
| --- | --- |
| banner | 1 |
| cover | 81 |
| embed | 156 |
| html-img | 33 |
| thumbnail | 84 |
| Leaflet layer refs | 82 |

### Imagens/arquivos referenciados por notas

| arquivo | uso | alvo | resolvido em zz_media |
| --- | --- | --- | --- |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_jd.png | zz_media/th_jd.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_mark.png | zz_media/th_mark.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_abel.png | zz_media/th_abel.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_sel.png | zz_media/th_sel.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_neema.png | zz_media/th_neema.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_katie.png | zz_media/th_katie.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_rod.png | zz_media/th_rod.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md | html-img | th_lj.png | zz_media/th_lj.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 02.md | html-img | th_ew.png | zz_media/th_ew.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 02.md | html-img | th_rott.png | zz_media/th_rott.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 03.md | html-img | th_ew.png | zz_media/th_ew.png |
| .trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 03.md | html-img | th_rott.png | zz_media/th_rott.png |
| .trash/Call Out Boxes/Call Out - Left Section.md | embed | z_Assets/Misc/ImagePlaceholder.png |  |
| .trash/Call Out Boxes/Call Out - Right Section.md | embed | z_Assets/Misc/ImagePlaceholder.png |  |
| .trash/City Forces/Blueforce.md | thumbnail | blueforce.png |  |
| .trash/City Forces/Blueforce.md | embed | 1lg2.png | zz_media/1lg2.png |
| .trash/City Forces/Blueforce.md | embed | bf.png | zz_media/bf.png |
| CALENDAR.md | cover | zz_media/t52.png | zz_media/t52.png |
| Characters/Individual/Ava Victoria.md | thumbnail | zz_media/th_ava.png | zz_media/th_ava.png |
| Characters/Individual/Ava Victoria.md | embed | ava.png | zz_media/ava.png |
| Characters/Individual/Bastian Redd.md | thumbnail | zz_media/th_redd.png | zz_media/th_redd.png |
| Characters/Individual/Bastian Redd.md | cover | zz_media/red.png | zz_media/red.png |
| Characters/Individual/Bastian Redd.md | embed | redd.png | zz_media/redd.png |
| Characters/Individual/Bobby Cutman.md | thumbnail | zz_media/th_cut.png | zz_media/th_cut.png |
| Characters/Individual/Bobby Cutman.md | cover | zz_media/cut.png | zz_media/cut.png |
| Characters/Individual/Bobby Cutman.md | embed | cutman.png | zz_media/cutman.png |
| Characters/Individual/Cassidy LaRue.md | thumbnail | zz_media/th_jcass.jpg | zz_media/th_jcass.jpg |
| Characters/Individual/Cassidy LaRue.md | cover | zz_media/cr.png | zz_media/cr.png |
| Characters/Individual/Cassidy LaRue.md | embed | cassidy.png | zz_media/cassidy.png |
| Characters/Individual/Cassidy LaRue.md | embed | jadencassidy.png | zz_media/jadencassidy.png |
| Characters/Individual/Cassidy LaRue.md | html-img | cassbikini2.png |  |
| Characters/Individual/Dusty Dillon.md | thumbnail | zz_media/th_dusty.png | zz_media/th_dusty.png |
| Characters/Individual/Dusty Dillon.md | cover | zz_media/dd.png | zz_media/dd.png |
| Characters/Individual/Dusty Dillon.md | embed | dusty.png | zz_media/dusty.png |
| Characters/Individual/Dusty Dillon.md | embed | smoke.mp3 | zz_media/smoke.mp3 |
| Characters/Individual/Flint Garritt.md | thumbnail | zz_media/th_flint.png | zz_media/th_flint.png |
| Characters/Individual/Flint Garritt.md | cover | zz_media/fli.png | zz_media/fli.png |
| Characters/Individual/Flint Garritt.md | embed | fg.png | zz_media/fg.png |
| Characters/Individual/Geo Huxley.md | thumbnail | zz_media/th_geo.png | zz_media/th_geo.png |
| Characters/Individual/Geo Huxley.md | cover | zz_media/ja.png | zz_media/ja.png |
| Characters/Individual/Geo Huxley.md | embed | geo.png | zz_media/geo.png |
| Characters/Individual/Hella.md | thumbnail | zz_media/th_hella.png | zz_media/th_hella.png |
| Characters/Individual/Hella.md | embed | hella.png | zz_media/hella.png |
| Characters/Individual/Jaden Kade.md | thumbnail | zz_media/th_jaden.png | zz_media/th_jaden.png |
| Characters/Individual/Jaden Kade.md | cover | zz_media/ja.png | zz_media/ja.png |
| Characters/Individual/Jaden Kade.md | embed | jaden.png | zz_media/jaden.png |
| Characters/Individual/Jay Dillinger.md | thumbnail | zz_media/th_jay.png | zz_media/th_jay.png |
| Characters/Individual/Jay Dillinger.md | cover | zz_media/spjay.png | zz_media/spjay.png |
| Characters/Individual/Jay Dillinger.md | embed | jay.png | zz_media/jay.png |
| Characters/Individual/Katarina Volkoff.md | thumbnail | zz_media/th_kata.png | zz_media/th_kata.png |
| Characters/Individual/Katarina Volkoff.md | embed | kata.png | zz_media/kata.png |
| Characters/Individual/Kullen Dane.md | thumbnail | zz_media/th_dane.png | zz_media/th_dane.png |
| Characters/Individual/Kullen Dane.md | embed | dane.png | zz_media/dane.png |
| Characters/Individual/Kullen Dane.md | embed | sqq.png | zz_media/sqq.png |
| Characters/Individual/Lash Hawkins.md | thumbnail | zz_media/th_lash.png | zz_media/th_lash.png |
| Characters/Individual/Lash Hawkins.md | embed | lash.png | zz_media/lash.png |
| Characters/Individual/Layla Hawk.md | thumbnail | zz_media/th_lh.png | zz_media/th_lh.png |
| Characters/Individual/Layla Hawk.md | cover | zz_media/lh1.png | zz_media/lh1.png |
| Characters/Individual/Layla Hawk.md | embed | lh.png | zz_media/lh.png |
| Characters/Individual/Marlon Lambert.md | thumbnail | zz_media/th_marlon.png | zz_media/th_marlon.png |
| Characters/Individual/Marlon Lambert.md | cover | zz_media/ml1.png | zz_media/ml1.png |
| Characters/Individual/Marlon Lambert.md | embed | marlon.png | zz_media/marlon.png |
| Characters/Individual/Morris Gable.md | thumbnail | zz_media/th_morris.png | zz_media/th_morris.png |
| Characters/Individual/Morris Gable.md | embed | morrisgable.png | zz_media/morrisgable.png |
| Characters/Individual/Ora Razchek.md | thumbnail | zz_media/th_ora.png | zz_media/th_ora.png |
| Characters/Individual/Ora Razchek.md | embed | ora.png | zz_media/ora.png |
| Characters/Individual/Owen McCready.md | thumbnail | zz_media/th_owen.png | zz_media/th_owen.png |
| Characters/Individual/Owen McCready.md | embed | owen.png | zz_media/owen.png |
| Characters/Individual/Rachel Gold.md | thumbnail | zz_media/th_rachel.png | zz_media/th_rachel.png |
| Characters/Individual/Rachel Gold.md | cover | zz_media/rg1.png | zz_media/rg1.png |
| Characters/Individual/Rachel Gold.md | embed | rachel.png | zz_media/rachel.png |
| Characters/Individual/Royce Sincayd.md | thumbnail | zz_media/th_royce.png | zz_media/th_royce.png |
| Characters/Individual/Royce Sincayd.md | cover | zz_media/rs1.png | zz_media/rs1.png |
| Characters/Individual/Royce Sincayd.md | embed | royce.png | zz_media/royce.png |
| Characters/Individual/Salem Quinn.md | thumbnail | zz_media/th_salem.png | zz_media/th_salem.png |
| Characters/Individual/Salem Quinn.md | embed | salem.png | zz_media/salem.png |
| Characters/Individual/Salem Quinn.md | embed | sqq.png | zz_media/sqq.png |
| Characters/Individual/Scumbag.md | thumbnail | zz_media/th_scum.png | zz_media/th_scum.png |
| Characters/Individual/Scumbag.md | embed | scum.png | zz_media/scum.png |
| Characters/Individual/Shana.md | thumbnail | zz_media/th_shana.png | zz_media/th_shana.png |
| Characters/Individual/Shana.md | embed | shana.png | zz_media/shana.png |
| Characters/Individual/Shana.md | embed | shanabeau.png | zz_media/shanabeau.png |
| Characters/Individual/Tate Faulkner.md | thumbnail | zz_media/th_tate.png | zz_media/th_tate.png |
| Characters/Individual/Tate Faulkner.md | embed | tate.png | zz_media/tate.png |
| Characters/Individual/The Grand Mascara.md | thumbnail | zz_media/th_santopriest.png | zz_media/th_santopriest.png |
| Characters/Individual/The Grand Mascara.md | embed | santopriest.png | zz_media/santopriest.png |
| Characters/Individual/The Grim Man.md | thumbnail | zz_media/th_grim.png | zz_media/th_grim.png |
| Characters/Individual/The Grim Man.md | embed | grim.png | zz_media/grim.png |
| Characters/Individual/The Grim Man.md | embed | grimbrile.png |  |
| Characters/Individual/Tyren Will.md | thumbnail | zz_media/th_tw.png | zz_media/th_tw.png |
| Characters/Individual/Tyren Will.md | embed | tyren.png | zz_media/tyren.png |
| Characters/Individual/Warren Scottyard.md | thumbnail | zz_media/th_ws.png | zz_media/th_ws.png |
| Characters/Individual/Warren Scottyard.md | cover | zz_media/ws1.png | zz_media/ws1.png |
| Characters/Individual/Warren Scottyard.md | embed | ws.png | zz_media/ws.png |
| Characters/Mayors of Tribucia/Cricket Granger.md | thumbnail | zz_media/th_cricket.png | zz_media/th_cricket.png |
| Characters/Mayors of Tribucia/Cricket Granger.md | embed | cricket.png | zz_media/cricket.png |
| Characters/Mayors of Tribucia/Ellis Westmount.md | thumbnail | zz_media/th_ellis.png | zz_media/th_ellis.png |
| Characters/Mayors of Tribucia/Ellis Westmount.md | embed | ellis.png | zz_media/ellis.png |
| Characters/Mayors of Tribucia/Gorren Brile.md | thumbnail | zz_media/th_gorren.png | zz_media/th_gorren.png |
| Characters/Mayors of Tribucia/Gorren Brile.md | embed | gorren.png | zz_media/gorren.png |
| Characters/Mayors of Tribucia/Marla Rusk.md | thumbnail | zz_media/th_marla.png | zz_media/th_marla.png |
| Characters/Mayors of Tribucia/Marla Rusk.md | embed | marla.png | zz_media/marla.png |
| Characters/Mayors of Tribucia/Soria Langston-Clay.md | thumbnail | zz_media/th_soria.png | zz_media/th_soria.png |
| Characters/Mayors of Tribucia/Soria Langston-Clay.md | embed | soria.png | zz_media/soria.png |
| Characters/Murray Boys/Francis Murray.md | thumbnail | zz_media/th_francis.png | zz_media/th_francis.png |
| Characters/Murray Boys/Francis Murray.md | embed | francis.png | zz_media/francis.png |
| Characters/Murray Boys/Marco Murray.md | thumbnail | zz_media/th_marco.png | zz_media/th_marco.png |
| Characters/Murray Boys/Marco Murray.md | embed | marco.png | zz_media/marco.png |
| Characters/Murray Boys/Nico Murray.md | thumbnail | zz_media/th_nico.png | zz_media/th_nico.png |
| Characters/Murray Boys/Nico Murray.md | embed | nico.png | zz_media/nico.png |
| Characters/Murray Boys/Rosa Murray.md | thumbnail | zz_media/th_rosa.png | zz_media/th_rosa.png |
| Characters/Murray Boys/Rosa Murray.md | embed | rosa.png | zz_media/rosa.png |
| Characters/Rancher Collective/Beau DuNoir.md | thumbnail | zz_media/th_beau.png | zz_media/th_beau.png |
| Characters/Rancher Collective/Beau DuNoir.md | embed | beau.png | zz_media/beau.png |
| Characters/Rancher Collective/Danny Dandelion.md | thumbnail | zz_media/tth_danny.png | zz_media/tth_danny.png |
| Characters/Rancher Collective/Danny Dandelion.md | embed | danny.png | zz_media/danny.png |
| Characters/Rancher Collective/Freddy Blanchard.md | thumbnail | zz_media/th_freddy.png | zz_media/th_freddy.png |
| Characters/Rancher Collective/Freddy Blanchard.md | embed | Freddy.png |  |
| Characters/Rancher Collective/Freddy Blanchard.md | embed | bf1.png | zz_media/bf1.png |
| Characters/Rancher Collective/Harp Langston.md | thumbnail | zz_media/th_harp.png | zz_media/th_harp.png |
| Characters/Rancher Collective/Harp Langston.md | embed | harp.png | zz_media/harp.png |
| Characters/Rancher Collective/Turner Anderson.md | thumbnail | zz_media/th_turner.png | zz_media/th_turner.png |
| Characters/Rancher Collective/Turner Anderson.md | embed | turner.png | zz_media/turner.png |
| Characters/Rancher Collective/Turner Anderson.md | embed | duke3.png | zz_media/duke3.png |
| Characters/Rustwater Raiders/Blacktide Cray.md | thumbnail | zz_media/th_cray.png | zz_media/th_cray.png |
| Characters/Rustwater Raiders/Blacktide Cray.md | embed | blacktide.png | zz_media/blacktide.png |
| Characters/Rustwater Raiders/Clinton Firebay.md | thumbnail | zz_media/th_clinton.png | zz_media/th_clinton.png |
| Characters/Rustwater Raiders/Clinton Firebay.md | embed | clinton.png | zz_media/clinton.png |
| Characters/Rustwater Raiders/Darius Adeyemi.md | thumbnail | zz_media/th_dary.png | zz_media/th_dary.png |
| Characters/Rustwater Raiders/Darius Adeyemi.md | embed | dary.png | zz_media/dary.png |
| Characters/Rustwater Raiders/Lyla Bonetooth.md | thumbnail | zz_media/th_lyla.png | zz_media/th_lyla.png |
| Characters/Rustwater Raiders/Lyla Bonetooth.md | embed | lyla.png | zz_media/lyla.png |
| Characters/Rustwater Raiders/Salt-Eye Marlow.md | thumbnail | zz_media/th_salt.png | zz_media/th_salt.png |
| Characters/Rustwater Raiders/Salt-Eye Marlow.md | embed | salt.png | zz_media/salt.png |
| Characters/Rustwater Raiders/Silas Vayne.md | thumbnail | zz_media/th_silas.png | zz_media/th_silas.png |
| Characters/Rustwater Raiders/Silas Vayne.md | embed | silas.png | zz_media/silas.png |
| Characters/Rustwater Raiders/Silas Vayne.md | embed | rsl.png | zz_media/rsl.png |
| Characters/Rustwater Raiders/Zadie Adeyemi.md | thumbnail | zz_media/th_zadie.png | zz_media/th_zadie.png |
| Characters/Rustwater Raiders/Zadie Adeyemi.md | embed | zadie.png | zz_media/zadie.png |
| Characters/Steeltown Wrecking Crew/Abel May Jr..md | thumbnail | zz_media/th_abel.png | zz_media/th_abel.png |
| Characters/Steeltown Wrecking Crew/Abel May Jr..md | embed | abel.png | zz_media/abel.png |
| Characters/Steeltown Wrecking Crew/Jimmy Douglass.md | thumbnail | zz_media/th_jimmy.png | zz_media/th_jimmy.png |
| Characters/Steeltown Wrecking Crew/Jimmy Douglass.md | cover | obsidian://open?vault=DGLV&file=zz_media%2Fth_jimmy.png |  |
| Characters/Steeltown Wrecking Crew/Jimmy Douglass.md | embed | jimmy.png | zz_media/jimmy.png |
| Characters/Steeltown Wrecking Crew/Joe Ameen.md | thumbnail | zz_media/th_neema.png | zz_media/th_neema.png |
| Characters/Steeltown Wrecking Crew/Joe Ameen.md | embed | neema.png | zz_media/neema.png |
| Characters/Steeltown Wrecking Crew/Katie Kowalski.md | thumbnail | zz_media/th_katie.png | zz_media/th_katie.png |
| Characters/Steeltown Wrecking Crew/Katie Kowalski.md | embed | katie.png | zz_media/katie.png |
| Characters/Steeltown Wrecking Crew/Katie Kowalski.md | embed | katred2.png | zz_media/katred2.png |
| Characters/Steeltown Wrecking Crew/Lincoln Jones.md | thumbnail | zz_media/th_linc.png | zz_media/th_linc.png |
| Characters/Steeltown Wrecking Crew/Lincoln Jones.md | embed | lincoln.png | zz_media/lincoln.png |
| Characters/Steeltown Wrecking Crew/Mark Jeffrey.md | thumbnail | zz_media/th_mark.png | zz_media/th_mark.png |
| Characters/Steeltown Wrecking Crew/Mark Jeffrey.md | embed | mark.png | zz_media/mark.png |
| Characters/Steeltown Wrecking Crew/Rodney Blythe.md | thumbnail | zz_media/th_rb.png | zz_media/th_rb.png |
| Characters/Steeltown Wrecking Crew/Rodney Blythe.md | embed | rb.png | zz_media/rb.png |
| Characters/Steeltown Wrecking Crew/Selena Matissao.md | thumbnail | zz_media/th_selena.png | zz_media/th_selena.png |
| Characters/Steeltown Wrecking Crew/Selena Matissao.md | embed | selena.png | zz_media/selena.png |
| Characters/The Elite & Loyalist Guard/Brady & Brody.md | thumbnail | zz_media/th_bandb.png | zz_media/th_bandb.png |
| Characters/The Elite & Loyalist Guard/Brady & Brody.md | embed | bandb.png | zz_media/bandb.png |
| Characters/The Elite & Loyalist Guard/Davis Pollard.md | thumbnail | zz_media/th_davis.png | zz_media/th_davis.png |
| Characters/The Elite & Loyalist Guard/Davis Pollard.md | embed | davis.png | zz_media/davis.png |
| Characters/The Elite & Loyalist Guard/Emily Burton.md | thumbnail | zz_media/th_emily.png | zz_media/th_emily.png |
| Characters/The Elite & Loyalist Guard/Emily Burton.md | embed | emily.png | zz_media/emily.png |
| Characters/The Elite & Loyalist Guard/Emily Burton.md | embed | embikini.png |  |
| Characters/The Elite & Loyalist Guard/General Colt.md | thumbnail | zz_media/th_colt.png | zz_media/th_colt.png |
| Characters/The Elite & Loyalist Guard/General Colt.md | embed | colt.png | zz_media/colt.png |
| Characters/The Elite & Loyalist Guard/General Colt.md | embed | coltwalk.png | zz_media/coltwalk.png |
| Characters/The Elite & Loyalist Guard/Jacoban Clay.md | thumbnail | zz_media/th_jacoban.png | zz_media/th_jacoban.png |
| Characters/The Elite & Loyalist Guard/Jacoban Clay.md | embed | jacoban.png | zz_media/jacoban.png |
| Characters/The Elite & Loyalist Guard/Raynar Ventura.md | thumbnail | zz_media/th_raynar.png | zz_media/th_raynar.png |
| Characters/The Elite & Loyalist Guard/Raynar Ventura.md | embed | raynar.png | zz_media/raynar.png |
| Characters/The Elite & Loyalist Guard/Sgt. Rottwyler.md | thumbnail | zz_media/th_rott.png | zz_media/th_rott.png |
| Characters/The Elite & Loyalist Guard/Sgt. Rottwyler.md | cover | th_rott.png | zz_media/th_rott.png |
| Characters/The Elite & Loyalist Guard/Sgt. Rottwyler.md | embed | rott.png | zz_media/rott.png |
| Characters/The Elite & Loyalist Guard/The Duke.md | thumbnail | zz_media/th_dukeofd.png | zz_media/th_dukeofd.png |
| Characters/The Elite & Loyalist Guard/The Duke.md | embed | dukeofd.png | zz_media/dukeofd.png |
| Characters/The Elite & Loyalist Guard/The Duke.md | embed | prop.png | zz_media/prop.png |
| Characters/Third Row/Jailface.md | thumbnail | zz_media/th_jail.png | zz_media/th_jail.png |
| Characters/Third Row/Jailface.md | embed | jailface.png | zz_media/jailface.png |
| Characters/Third Row/Malika Locke.md | thumbnail | zz_media/th_malika.png | zz_media/th_malika.png |
| Characters/Third Row/Malika Locke.md | embed | malika.png | zz_media/malika.png |
| Characters/Third Row/Ninepack.md | thumbnail | zz_media/th_nine.png | zz_media/th_nine.png |
| Characters/Third Row/Ninepack.md | embed | ninepack.png | zz_media/ninepack.png |
| Characters/Third Row/Sable.md | thumbnail | zz_media/th_sable.png | zz_media/th_sable.png |
| Characters/Third Row/Sable.md | embed | sable.png | zz_media/sable.png |
| Characters/Third Row/Samson Knight.md | thumbnail | zz_media/th_samson.png | zz_media/th_samson.png |
| Characters/Third Row/Samson Knight.md | embed | knight.png | zz_media/knight.png |
| Characters/Unseen Widows/Len Vyne.md | thumbnail | zz_media/th_len.png | zz_media/th_len.png |
| Characters/Unseen Widows/Len Vyne.md | embed | len.png | zz_media/len.png |
| Characters/Unseen Widows/Nita Blackbird.md | thumbnail | zz_media/th_nita.png | zz_media/th_nita.png |
| Characters/Unseen Widows/Nita Blackbird.md | embed | nita.png | zz_media/nita.png |
| Characters/Unseen Widows/Prophet Veerah.md | thumbnail | zz_media/th_veerah.png | zz_media/th_veerah.png |
| Characters/Unseen Widows/Prophet Veerah.md | embed | veerah.png | zz_media/veerah.png |
| Characters/Unseen Widows/Prophet Veerah.md | embed | veerah preach.png | zz_media/veerah preach.png |
| Characters/Unseen Widows/Raina & Risa.md | thumbnail | zz_media/th_randr.png | zz_media/th_randr.png |
| Characters/Unseen Widows/Raina & Risa.md | embed | randr.png | zz_media/randr.png |
| Characters/Unseen Widows/Riley Thorne.md | thumbnail | zz_media/th_riley.png | zz_media/th_riley.png |
| Characters/Unseen Widows/Riley Thorne.md | embed | riley.png | zz_media/riley.png |
| CULTURE.md | cover | zz_media/t6.png | zz_media/t6.png |
| DISGRACELAND/01 - Main Event Shadows.md | cover | [[zz_media/abevsbob.png]] | zz_media/abevsbob.png |
| DISGRACELAND/02 - Ghosts On The Waves.md | cover | [[zz_media/lyladuke.png]] | zz_media/lyladuke.png |
| DISGRACELAND/03 - The Devil In The Row.md | cover | [[zz_media/03.png]] | zz_media/03.png |
| DISGRACELAND/04 - Glowing Darkness.md | cover | [[zz_media/04.png]] | zz_media/04.png |
| DISGRACELAND/05 - Sight Unseen.md | cover | [[zz_media/05.png]] | zz_media/05.png |
| DISGRACELAND/06 - Showdown In Gage Park.md | cover | [[zz_media/showdown1.png]] | zz_media/showdown1.png |
| DISGRACELAND/07 - The Spotlight Lies.md | cover | [[zz_media/071.png]] | zz_media/071.png |
| DISGRACELAND/08 - No Answers.md | cover | [[zz_media/081.png]] | zz_media/081.png |
| DISGRACELAND/B-Sides From The End Times/Hymn From A Dead Girl.md | cover | zz_media/b12.png | zz_media/b12.png |
| DISGRACELAND/B-Sides From The End Times/Snake Eyes In Threshton.md | cover | zz_media/b2.png | zz_media/b2.png |
| DISGRACELAND/B-Sides From The End Times/Visions In The Night.md | cover | zz_media/b3.png | zz_media/b3.png |
| DISGRACELAND/DISGRACELAND.md | cover | zz_media/001.png | zz_media/001.png |
| DISGRACELAND/DISGRACELAND.md | html-img | wods.png | zz_media/wods.png |
| ECONOMY.md | cover | zz_media/t3.png | zz_media/t3.png |
| ECONOMY.md | embed | slugs.png | zz_media/slugs.png |
| ECONOMY.md | embed | econ.png | zz_media/econ.png |
| Factions/Loyalist Guard.md | thumbnail | [[zz_media/lgg.png]] | zz_media/lgg.png |
| Factions/Loyalist Guard.md | embed | lgg.png | zz_media/lgg.png |
| Factions/Murray Boys.md | thumbnail | zz_media/murr.png | zz_media/murr.png |
| Factions/Rancher Collective.md | thumbnail | zz_media/rcl.png | zz_media/rcl.png |
| Factions/Rancher Collective.md | embed | rcl.png | zz_media/rcl.png |
| Factions/Rustwater Raiders.md | thumbnail | [[zz_media/lrr.png]] | zz_media/lrr.png |
| Factions/Rustwater Raiders.md | embed | lrr.png | zz_media/lrr.png |
| Factions/Steeltown Wrecking Crew.md | thumbnail | zz_media/SWC.png | zz_media/SWC.png |
| Factions/Steeltown Wrecking Crew.md | embed | SWC.png | zz_media/SWC.png |
| Factions/Third Row.md | thumbnail | zz_media/iii.png | zz_media/iii.png |
| Factions/Third Row.md | embed | iii.png | zz_media/iii.png |
| Factions/Unseen Widows.md | thumbnail | zz_media/UnseenWidows.png | zz_media/UnseenWidows.png |
| Factions/Unseen Widows.md | embed | UnseenWidows.png | zz_media/UnseenWidows.png |
| Home.md | banner | "[[zz_media/big1.png]]" |  |
| Home.md | embed | sool.png\ | zz_media/sool.png |
| Home.md | embed | eo.png\ | zz_media/eo.png |
| Home.md | embed | t2.png\ | zz_media/t2.png |
| Home.md | embed | news1.png\ | zz_media/news1.png |
| Home.md | embed | mapp.png\ | zz_media/mapp.png |
| Home.md | html-img | wod.png | zz_media/wod.png |
| LATEST_NEWS.md | cover | zz_media/en.png | zz_media/en.png |
| LATEST_NEWS.md | embed | paper.png | zz_media/paper.png |
| LATEST_NEWS.md | html-img | tt.png | zz_media/tt.png |
| Legacy - Disgraceland Chapter 01 - Ghosts on the Waves.md | cover | [[zz_media/lyladuke.png]] | zz_media/lyladuke.png |
| Legacy - Disgraceland OUTLINES.md | cover | zz_media/002.png | zz_media/002.png |
| Legacy - Disgraceland Scratch Notes.md | html-img | /vault/path/to/thumbnails/th_${slug}.png |  |
| Legacy - Disgraceland Scratch Notes.md | html-img | abevsbob.png | zz_media/abevsbob.png |
| Legacy - Disgraceland Scratch Notes.md | html-img | lyladuke.png | zz_media/lyladuke.png |
| Legacy - Disgraceland Scratch Notes.md | html-img | 03.png | zz_media/03.png |
| Legacy - Disgraceland Scratch Notes.md | html-img | 04.png | zz_media/04.png |
| Legacy - Disgraceland Scratch Notes.md | html-img | 05.png | zz_media/05.png |
| Locations/Coffin Island.md | cover | "[[zz_media/ci.png]]" |  |
| Locations/Coffin Island.md | embed | ci.png | zz_media/ci.png |
| Locations/Four Tombs Islands.md | cover | zz_media/4t.png | zz_media/4t.png |
| Locations/Four Tombs Islands.md | embed | 4t.png | zz_media/4t.png |
| Locations/Geo's P.I..md | cover | zz_media/gpi.png | zz_media/gpi.png |
| Locations/Geo's P.I..md | embed | gpi.png | zz_media/gpi.png |
| Locations/Ha Ha Hole.md | cover | zz_media/hhh.png | zz_media/hhh.png |
| Locations/Ha Ha Hole.md | embed | haha.png | zz_media/haha.png |
| Locations/Hollow House.md | cover | zz_media/hh.png | zz_media/hh.png |
| Locations/Hollow House.md | embed | hh.png | zz_media/hh.png |
| Locations/Three Nail Market.md | cover | zz_media/tnm.png | zz_media/tnm.png |
| Locations/Three Nail Market.md | embed | tnm.png | zz_media/tnm.png |
| Locations/Tribucia Tribute.md | cover | zz_media/paper.png | zz_media/paper.png |
| Locations/Tribucia Tribute.md | embed | paper.png | zz_media/paper.png |
| Locations/TTV Studios.md | cover | zz_media/ttv.png | zz_media/ttv.png |
| Locations/TTV Studios.md | embed | ttv.png | zz_media/ttv.png |
| Locations/Wrecking Crew Clubhouse.md | cover | zz_media/club.png | zz_media/club.png |
| Locations/Wrecking Crew Clubhouse.md | embed | club.png | zz_media/club.png |
| Lore/Abbsidian.md | cover | zz_media/abbsid.png | zz_media/abbsid.png |
| Lore/Abbsidian.md | embed | abbsid.png | zz_media/abbsid.png |
| Lore/Ashmoor Festival.md | cover | zz_media/unity.png | zz_media/unity.png |
| Lore/Ashmoor Festival.md | embed | unity.png | zz_media/unity.png |
| Lore/Backburn Shows.md | cover | zz_media/bbshow.png | zz_media/bbshow.png |
| Lore/Backburn Shows.md | embed | bbshow.png | zz_media/bbshow.png |
| Lore/Blackshift Massacre.md | cover | zz_media/bs.png | zz_media/bs.png |
| Lore/Blackshift Massacre.md | embed | bs.png | zz_media/bs.png |
| Lore/CRT Televisions.md | cover | zz_media/crt.png | zz_media/crt.png |
| Lore/CRT Televisions.md | embed | crt.png | zz_media/crt.png |
| Lore/Dark Night.md | cover | zz_media/dn.png | zz_media/dn.png |
| Lore/Dark Night.md | embed | dn.png | zz_media/dn.png |
| Lore/Darrell Douglass.md | thumbnail | th_ders.png | zz_media/th_ders.png |
| Lore/Darrell Douglass.md | cover | zz_media/d1.png | zz_media/d1.png |
| Lore/Darrell Douglass.md | embed | darrell.png | zz_media/darrell.png |
| Lore/Final Force.md | cover | zz_media/ff.png | zz_media/ff.png |
| Lore/Final Force.md | embed | ff.png | zz_media/ff.png |
| Lore/Galliah, the Stillborn Star.md | cover | zz_media/gall.png | zz_media/gall.png |
| Lore/Galliah, the Stillborn Star.md | embed | gall.png | zz_media/gall.png |
| Lore/Luxyn.md | cover | zz_media/luminaddict.png | zz_media/luminaddict.png |
| Lore/Luxyn.md | embed | luxyn.png | zz_media/luxyn.png |
| Lore/Night Time with Morris Gable.md | cover | zz_media/nt.png | zz_media/nt.png |
| Lore/Night Time with Morris Gable.md | embed | nt.png | zz_media/nt.png |
| Lore/Noche de Lucha.md | cover | zz_media/ancientnl.png | zz_media/ancientnl.png |
| Lore/Noche de Lucha.md | embed | ancientnl.png | zz_media/ancientnl.png |
| Lore/Poundball.md | cover | zz_media/pb1.png | zz_media/pb1.png |
| Lore/Poundball.md | embed | pound.png | zz_media/pound.png |
| Lore/Sliver.md | cover | zz_media/sliv.png | zz_media/sliv.png |
| Lore/Sliver.md | embed | sliver.png | zz_media/sliver.png |
| Lore/State of Tribucia.md | cover | zz_media/state.png | zz_media/state.png |
| Lore/State of Tribucia.md | embed | state.png | zz_media/state.png |
| Lore/Swillpots.md | cover | zz_media/swill.png | zz_media/swill.png |
| Lore/Swillpots.md | embed | swill.png | zz_media/swill.png |
| Lore/Tetra Bomb.md | cover | zz_media/tbomb.png | zz_media/tbomb.png |
| Lore/Tetra Bomb.md | embed | tbomb.png | zz_media/tbomb.png |
| Lore/The Black Marauder.md | cover | zz_media/bm.png | zz_media/bm.png |
| Lore/The Black Marauder.md | embed | bm.png | zz_media/bm.png |
| Lore/The Silo.md | cover | zz_media/silo.png | zz_media/silo.png |
| Lore/The Silo.md | embed | silo.png | zz_media/silo.png |
| Lore/The Wanderers.md | cover | zz_media/wandd.png | zz_media/wandd.png |
| Lore/The Wanderers.md | embed | wand.png | zz_media/wand.png |
| Lore/Transportation.md | cover | zz_media/car.png | zz_media/car.png |
| Lore/Transportation.md | embed | car.png | zz_media/car.png |
| Lore/Trashflicks.md | cover | zz_media/tf.png | zz_media/tf.png |
| Lore/Trashflicks.md | embed | trash.png | zz_media/trash.png |
| Lore/TTV Evening News.md | cover | zz_media/ttven.png | zz_media/ttven.png |
| Lore/TTV Evening News.md | embed | en.png | zz_media/en.png |
| Lore/Valkaara.md | cover | zz_media/valk.png | zz_media/valk.png |
| Lore/Valkaara.md | embed | valk.png | zz_media/valk.png |
| Lore/Water Wars.md | cover | zz_media/w.png | zz_media/w.png |
| Lore/Water Wars.md | embed | w.png | zz_media/w.png |
| Lore/WLL Fight Night.md | cover | zz_media/fn.png | zz_media/fn.png |
| Lore/World Lucha Libre.md | cover | zz_media/wllring.png | zz_media/wllring.png |
| Lore/World Lucha Libre.md | embed | wll1.png | zz_media/wll1.png |
| Lore/World Lucha Libre.md | embed | wll.png | zz_media/wll.png |
| LORE.md | cover | zz_media/t7.png | zz_media/t7.png |
| Religion/Church of the Ember Saint.md | embed | es.png | zz_media/es.png |
| Religion/El Santo.md | embed | els.png | zz_media/els.png |
| Religion/Faith of Mirella.md | embed | fm.png | zz_media/fm.png |
| Religion/RELIGION.md | cover | zz_media/t8.png | zz_media/t8.png |
| Religion/Word of the Stillborn Star.md | embed | ss.png | zz_media/ss.png |
| Territories/ASHMOOR.md | cover | zz_media/ashmoor.png | zz_media/ashmoor.png |
| Territories/ASHMOOR.md | embed | ashmoor.png | zz_media/ashmoor.png |
| Territories/CHARSPIRE.md | cover | zz_media/chars.png | zz_media/chars.png |
| Territories/CHARSPIRE.md | embed | chars.png | zz_media/chars.png |
| Territories/GUTTER ROW.md | cover | zz_media/gutt1.png | zz_media/gutt1.png |
| Territories/GUTTER ROW.md | embed | gutt1.png | zz_media/gutt1.png |
| Territories/STEELTOWN.md | cover | zz_media/s5t.png | zz_media/s5t.png |
| Territories/STEELTOWN.md | embed | s5t.png | zz_media/s5t.png |
| Territories/THE DROWNLANDS.md | cover | zz_media/drown.png | zz_media/drown.png |
| Territories/THE DROWNLANDS.md | embed | drown.png | zz_media/drown.png |
| Territories/THE DROWNLANDS.md | embed | drownland.png | zz_media/drownland.png |
| Territories/THE DROWNLANDS.md | html-img | th_ver.png | zz_media/th_ver.png |
| Territories/THE DROWNLANDS.md | html-img | th_rt.png | zz_media/th_rt.png |
| Territories/THE DROWNLANDS.md | html-img | th_mb.png | zz_media/th_mb.png |
| Territories/THE DROWNLANDS.md | html-img | th_lk.png | zz_media/th_lk.png |
| Territories/THE DROWNLANDS.md | html-img | th_rr.png | zz_media/th_rr.png |
| Territories/THRESHTON.md | cover | zz_media/df.png | zz_media/df.png |
| Territories/THRESHTON.md | embed | df.png | zz_media/df.png |
| Territories/WATER.md | cover | zz_media/chars.png | zz_media/chars.png |
| Territories/WATER.md | embed | chars.png | zz_media/chars.png |
| TIMELINE.md | cover | zz_media/t1.png | zz_media/t1.png |
| TRIBUCIA MAP.md | cover | zz_media/t4.png | zz_media/t4.png |
| Workflow/Charts.md | embed | Vault Report |  |
| Workflow/OUTLINES.md | cover | zz_media/002.png | zz_media/002.png |
| Workflow/Scratch Notes.md | html-img | /vault/path/to/thumbnails/th_${slug}.png |  |
| Workflow/Scratch Notes.md | html-img | abevsbob.png | zz_media/abevsbob.png |
| Workflow/Scratch Notes.md | html-img | lyladuke.png | zz_media/lyladuke.png |
| Workflow/Scratch Notes.md | html-img | 03.png | zz_media/03.png |
| Workflow/Scratch Notes.md | html-img | 04.png | zz_media/04.png |
| Workflow/Scratch Notes.md | html-img | 05.png | zz_media/05.png |

### Layers de mapa usadas pelo Leaflet

| layer | marcadores |
| --- | --- |
| zz_media%2FTribucia.png | 82 |