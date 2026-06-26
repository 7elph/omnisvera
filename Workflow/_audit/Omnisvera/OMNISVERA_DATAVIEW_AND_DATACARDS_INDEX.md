# OMNISVERA DATAVIEW AND DATACARDS INDEX

Gerado em: 2026-06-26 14:06.

Dataview: 41 blocos. DataCards: 18 blocos.

## Dataview

| arquivo | linha | tipo | FROM | tags | campos | WHERE | SORT/LIMIT | risco |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Characters/Individual/Augustus Terra Decimus.md | 46 | list | EARTHROPO | — | chapter, file.name, name | where contains(this.chapter, file.name) | sort file.name asc | quebra se campo/tag/pasta mudar |
| Characters/Individual/General Cassian Valerius.md | 51 | list | EARTHROPO | — | file.inlinks, file.link, file.name, name | where contains(this.file.inlinks, file.link) | sort file.name asc | quebra se campo/tag/pasta mudar |
| Home.md | 92 | > | Characters | — | date, district, faction, file.mtime, religion, role, status, tags, territory, thumbnail, width | — | — | quebra se campo/tag/pasta mudar |
| Home.md | 160 | table | / | — | WITHOUT ID, date, file.folder, file.mtime, file.name, file.path, name | WHERE file.mtime >= date(today) - dur(30 days) | SORT file.mtime DESC, LIMIT 10 | quebra se campo/tag/pasta mudar |
| Locations/Leth'valora.md | 85 | table | Characters | — | faction, location, status | where contains(lower(string(location)), "leth'valora") | limit 10 | quebra se campo/tag/pasta mudar |
| NOTES.md | 42 | table | / | — | WITHOUT ID, file.mtime, file.name, file.path, name | WHERE file.name != this.file.name | SORT file.mtime DESC, LIMIT 15 | quebra se campo/tag/pasta mudar |
| Templates/Characters/Antagonista.md | 61 | list | EARTHROPO | — | chapters, file.name, name | WHERE contains(this.chapters, file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Characters/Criatura.md | 61 | list | EARTHROPO | — | chapters, file.name, name | WHERE contains(this.chapters, file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Characters/NPC Importante.md | 61 | list | EARTHROPO | — | chapters, file.name, name | WHERE contains(this.chapters, file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Characters/Personagem Jogador.md | 61 | list | EARTHROPO | — | chapters, file.name, name | WHERE contains(this.chapters, file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Classes/Arquétipo Narrativo.md | 110 | table | Characters | — | class, faction, file.link, file.name, life_status, location, name, race, role, thumbnail | WHERE contains(this.file.link, role) OR contains(this.file.link, class) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Classes/Classe Base.md | 117 | table | Characters | — | class, faction, file.link, file.name, life_status, location, name, race, thumbnail | WHERE class = this.file.link OR contains(classes, this.file.link) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Classes/Classe Base.md | 128 | table | Classes | — | campaign_status, canon_status, file.link, file.name, name, parent_class, rules_status, work_status | WHERE parent_class = this.file.link | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Templates/Classes/Especialização.md | 120 | table | Characters | — | class, faction, file.link, file.name, life_status, location, name, race, thumbnail | WHERE class = this.file.link OR contains(classes, this.file.link) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Territories/Floresta de Avenor.md | 91 | table | Characters | — | faction, location, status | where contains(lower(string(location)), "leth'valora") | limit 10 | quebra se campo/tag/pasta mudar |
| Territories/Nimalia.md | 115 | table | Characters | — | faction, location, status | where contains(lower(string(location)), "nimalia") | limit 10 | quebra se campo/tag/pasta mudar |
| Workflow/Charts.md | 53 | table | Religion | — | file.name, info, name, religion, status, tags | WHERE contains(tags, "religion") | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_CLASS_STANDARD.md | 451 | table | Characters | — | class, faction, file.link, file.name, life_status, location, name, race, thumbnail | WHERE class = this.file.link OR contains(classes, this.file.link) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_CLASS_STANDARD.md | 466 | table | Classes | — | campaign_status, canon_status, file.link, file.name, name, parent_class, rules_status, work_status | WHERE parent_class = this.file.link | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 41 | table | Characters | — | date, file.mtime, life_status, role, subtype, thumbnail, type, width | WHERE type = "character" | SORT file.mtime DESC, LIMIT 5 | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 68 | table | Characters | — | file.name, life_status, location, name, role, subtype, thumbnail, type | WHERE type = "character" AND subtype = "player_character" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 88 | table | Characters | — | faction, file.link, file.name, life_status, location, name, role, thumbnail | WHERE contains(faction, this.file.link) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 108 | table | Characters | — | chapters, faction, file.name, life_status, name, role, thumbnail | WHERE contains(chapters, this.file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 130 | table |  | — | canon_status, file.mtime, requires_review, subtype, type, work_status | WHERE requires_review = true | SORT file.mtime DESC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 151 | table | Classes | — | campaign_status, class, file.name, name, rules_status, system, thumbnail, type | WHERE type = "class" AND campaign_status = "Allowed" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 160 | table | Classes | — | campaign_status, canon_status, class, file.name, name, rules_status, system, thumbnail, type | WHERE type = "class" AND rules_status = "Official" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 173 | table | Characters | — | chapters, faction, file.name, life_status, name, role, thumbnail | WHERE contains(chapters, this.file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 190 | table | Characters | — | faction, file.link, file.name, life_status, location, name, role, thumbnail | WHERE contains(faction, this.file.link) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 207 | table | Characters | — | file.link, file.name, life_status, location, name, origin, role, thumbnail | WHERE location = this.file.link OR origin = this.file.link | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 223 | table |  | — | canon_status, file.mtime, requires_review, subtype, type, work_status | WHERE requires_review = true | SORT file.mtime DESC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 240 | table | Characters | — | file.name, life_status, location, name, role, thumbnail, type | WHERE type = "character" AND life_status = "Morto" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 256 | table | Characters | — | file.name, life_status, location, name, role, subtype, thumbnail, type | WHERE type = "character" AND subtype = "antagonist" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 273 | table | Characters | — | class, faction, file.link, file.name, life_status, location, name, race, thumbnail | WHERE class = this.file.link OR contains(classes, this.file.link) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 293 | table | Classes | — | campaign_status, canon_status, file.link, file.name, name, parent_class, rules_status, work_status | WHERE parent_class = this.file.link | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 312 | table | Classes | — | campaign_status, canon_status, file.mtime, requires_review, rules_status, subtype | WHERE requires_review = true | SORT file.mtime DESC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 329 | list | EARTHROPO | — | chapters, file.name, name | WHERE contains(this.chapters, file.name) | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 344 | table | Territories | — | cover, file.name, leader, name, population, portrait, territory, type | WHERE type = "territory" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/OMNISVERA_DASHBOARD_SYSTEM.md | 359 | table | Factions | — | faction, file.name, location, name, status, thumbnail, type | WHERE type = "faction" | SORT file.name ASC | quebra se campo/tag/pasta mudar |
| Workflow/Vault Report.md | 16 | table | / | — | WITHOUT ID, faction, file.name, file.tags, location, name, religion, tags, territory | WHERE !startswith(file.name, "Legacy -") | — | quebra se campo/tag/pasta mudar |
| Workflow/Vault Report.md | 30 | table | / | — | NoteStatus, WITHOUT ID, file.name, name | WHERE NoteStatus | SORT NoteStatus ASC | quebra se campo/tag/pasta mudar |
| Workflow/Vault Report.md | 43 | table | / | — | NoteStatus, file.mtime, file.mtime AS "Modificada", file.name, file.path, info, name, status | WHERE (NoteStatus = "Placeholder" OR NoteStatus = "Draft") | SORT file.path ASC | quebra se campo/tag/pasta mudar |

## DataCards

| arquivo | linha | FROM | tags | campos | imageProperty | preset | columns | risco |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Characters/Individual/Raziel.md | 196 | #raziel | raziel | item, name, status, thumbnail | thumbnail | grid | 6 | quebra se imageProperty/campo/tag mudar |
| Characters/Individual/Vezemir.md | 239 | #vezemir | vezemir | item, name, status, thumbnail | thumbnail | grid | 6 | quebra se imageProperty/campo/tag mudar |
| CULTURE.md | 20 | #entertainment | entertainment | cover, info, name, status | cover | square | 6 | quebra se imageProperty/campo/tag mudar |
| CULTURE.md | 49 | #music | music | cover, info, name, portrait, status | cover | portrait | 5 | quebra se imageProperty/campo/tag mudar |
| CULTURE.md | 82 | #sport | sport | cover, info, name, status | cover | grid | 6 | quebra se imageProperty/campo/tag mudar |
| CULTURE.md | 108 | #news | news | cover, info, name, status | cover | grid | 5 | quebra se imageProperty/campo/tag mudar |
| EARTHROPO/00 - As Crônicas de Névoa de Sangue.md | 25 | #chapter00_raziel | chapter00_raziel | location, name, status, thumbnail | thumbnail | compact | 6 | quebra se imageProperty/campo/tag mudar |
| EARTHROPO/00 - O Bastardo de Ferro.md | 29 | #chapter00 | chapter00 | location, name, status, thumbnail | thumbnail | compact | 6 | quebra se imageProperty/campo/tag mudar |
| EARTHROPO/00 - O Corvo da Maré Baixa.md | 25 | #chapter00_varkh | chapter00_varkh | location, name, status, thumbnail | thumbnail | compact | 6 | quebra se imageProperty/campo/tag mudar |
| EARTHROPO/EARTHROPO.md | 46 | — | — | chapter, cover, date, description, name | — | — | — | quebra se imageProperty/campo/tag mudar |
| Factions/Guarda Real de Nimalia.md | 22 | #guarda | guarda | location, name, status, thumbnail | thumbnail | grid | 6 | quebra se imageProperty/campo/tag mudar |
| Home.md | 46 | — | — | cover, name | — | — | — | quebra se imageProperty/campo/tag mudar |
| Home.md | 67 | — | — | cover, date, description | — | — | — | quebra se imageProperty/campo/tag mudar |
| Home.md | 109 | — | — | NoteStatus, cover, leader, name, population, portrait, region, territory | — | — | — | quebra se imageProperty/campo/tag mudar |
| Home.md | 122 | — | — | NoteStatus, cover, info, location, territory | — | — | — | quebra se imageProperty/campo/tag mudar |
| Home.md | 135 | — | — | cover, name, portrait, race, status | — | — | — | quebra se imageProperty/campo/tag mudar |
| Home.md | 147 | — | — | class, cover, name, portrait, status | — | — | — | quebra se imageProperty/campo/tag mudar |
| LORE.md | 7 | #lore | lore | cover, info, name | cover | square | 6 | quebra se imageProperty/campo/tag mudar |

## Campos usados por consultas

| campo | Dataview | DataCards | função provável |
| --- | --- | --- | --- |
| NoteStatus | 2 | 2 | status editorial/template |
| campaign_status | 6 | 0 | campo observado no frontmatter atual |
| canon_status | 7 | 0 | campo observado no frontmatter atual |
| chapter | 1 | 1 | campo observado no frontmatter atual |
| chapters | 7 | 0 | aparições/estrutura narrativa herdada |
| class | 7 | 1 | campo observado no frontmatter atual |
| cover | 1 | 12 | capa visual para cards/notas |
| date | 3 | 2 | data de sessão/capítulo/evento |
| description | 0 | 2 | descrição curta para cards |
| district | 1 | 0 | campo observado no frontmatter atual |
| faction | 15 | 0 | facção e agrupamento |
| file.folder | 1 | 0 | campo observado no frontmatter atual |
| file.inlinks | 1 | 0 | campo observado no frontmatter atual |
| file.link | 12 | 0 | campo observado no frontmatter atual |
| file.mtime | 8 | 0 | campo observado no frontmatter atual |
| file.mtime AS "Modificada" | 1 | 0 | campo observado no frontmatter atual |
| file.name | 33 | 0 | campo observado no frontmatter atual |
| file.path | 3 | 0 | campo observado no frontmatter atual |
| file.tags | 1 | 0 | campo observado no frontmatter atual |
| info | 2 | 6 | campo observado no frontmatter atual |
| item | 0 | 2 | campo observado no frontmatter atual |
| leader | 1 | 1 | líder de facção/território |
| life_status | 14 | 0 | campo observado no frontmatter atual |
| location | 16 | 5 | localização e filtros |
| name | 33 | 16 | campo observado no frontmatter atual |
| origin | 1 | 0 | campo observado no frontmatter atual |
| parent_class | 3 | 0 | campo observado no frontmatter atual |
| population | 1 | 1 | população de território/assentamento |
| portrait | 1 | 4 | campo observado no frontmatter atual |
| race | 5 | 1 | campo observado no frontmatter atual |
| region | 0 | 1 | região geográfica |
| religion | 3 | 0 | campo observado no frontmatter atual |
| requires_review | 3 | 0 | campo observado no frontmatter atual |
| role | 11 | 0 | papel de personagem |
| rules_status | 6 | 0 | campo observado no frontmatter atual |
| status | 7 | 12 | estado narrativo/operacional exibido em cards |
| subtype | 6 | 0 | campo observado no frontmatter atual |
| system | 2 | 0 | campo observado no frontmatter atual |
| tags | 3 | 0 | filtros, DataCards, Dataview e visual |
| territory | 3 | 2 | território/região e filtros |
| thumbnail | 18 | 6 | imagem pequena para cards/tabelas |
| type | 10 | 0 | campo observado no frontmatter atual |
| width | 2 | 0 | campo observado no frontmatter atual |
| work_status | 5 | 0 | campo observado no frontmatter atual |