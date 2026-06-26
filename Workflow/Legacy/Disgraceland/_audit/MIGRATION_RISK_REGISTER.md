# MIGRATION RISK REGISTER

Gerado em: 2026-06-26 07:40.

Registro técnico para futura migração. Não é recomendação de alteração nesta etapa.

| risco | origem | impacto | arquivos afetados | como evitar |
| --- | --- | --- | --- | --- |
| Remover/renomear tags visuais | Supercharged Links + Style Settings + tags YAML | Perda de cor/peso de links e agrupamento visual. | .trash/City Forces/Blueforce.md, Characters/Mayors of Tribucia/Ellis Westmount.md, Characters/Steeltown Wrecking Crew/Abel May Jr..md, Characters/Steeltown Wrecking Crew/Jimmy Douglass.md, Characters/Steeltown Wrecking Crew/Joe Ameen.md, Characters/Steeltown Wrecking Crew/Katie Kowalski.md, Characters/Steeltown Wrecking Crew/Lincoln Jones.md, Characters/Steeltown Wrecking Crew/Mark Jeffrey.md, Characters/Steeltown Wrecking Crew/Rodney Blythe.md, Characters/Steeltown Wrecking Crew/Selena Matissao.md +3, Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md, Characters/Individual/Geo Huxley.md, Characters/Individual/Hella.md, Characters/Individual/Jaden Kade.md, Characters/Individual/Jay Dillinger.md +21, Locations/Coffin Island.md, Locations/Four Tombs Islands.md, Locations/Geo's P.I..md, Locations/Ha Ha Hole.md, Locations/Hollow House.md, Locations/Three Nail Market.md, Locations/Tribucia Tribute.md, Locations/TTV Studios.md, Locations/Wrecking Crew Clubhouse.md, Lore/Abbsidian.md +30, Lore/Galliah, the Stillborn Star.md, Religion/Church of the Ember Saint.md, Religion/El Santo.md, Religion/Faith of Mirella.md, Religion/RELIGION.md, Religion/Word of the Stillborn Star.md, Home.md, Territories/ASHMOOR.md, Territories/CHARSPIRE.md, Territories/GUTTER ROW.md, Territories/STEELTOWN.md, Territories/THE DROWNLANDS.md, Territories/THRESHTON.md, Characters/Individual/Kullen Dane.md, Characters/Mayors of Tribucia/Soria Langston-Clay.md, Characters/The Elite & Loyalist Guard/Brady & Brody.md, Characters/The Elite & Loyalist Guard/Davis Pollard.md, Characters/The Elite & Loyalist Guard/Emily Burton.md, Characters/The Elite & Loyalist Guard/General Colt.md, Characters/The Elite & Loyalist Guard/Jacoban Clay.md, Characters/The Elite & Loyalist Guard/Raynar Ventura.md, Characters/The Elite & Loyalist Guard/Sgt. Rottwyler.md, Characters/The Elite & Loyalist Guard/The Duke.md +3 +7 | Manter tags até recriar mapeamento visual e regenerar CSS pelo plugin. |
| Trocar thumbnail por cover | DataCards/Home/personagens | Cards podem ficar sem imagem. | DISGRACELAND/01 - Main Event Shadows.md, DISGRACELAND/02 - Ghosts On The Waves.md, DISGRACELAND/03 - The Devil In The Row.md, DISGRACELAND/04 - Glowing Darkness.md, DISGRACELAND/05 - Sight Unseen.md, DISGRACELAND/06 - Showdown In Gage Park.md, DISGRACELAND/07 - The Spotlight Lies.md, DISGRACELAND/08 - No Answers.md +14 | Atualizar imageProperty e campos consultados em lote, depois validar dashboards. |
| Renomear chapters ou capítulos | Campo chapters + Dataview | Aparições deixam de aparecer. | Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md, Characters/Individual/Geo Huxley.md, Characters/Individual/Hella.md +67 | Preservar nomes ou criar aliases antes de renomear. |
| Renomear notas do mapa | Leaflet data.json | Marcadores deixam de abrir notas. | TRIBUCIA MAP.md, .obsidian/plugins/obsidian-leaflet-plugin/data.json | Atualizar links dos marcadores junto com qualquer rename. |
| Mover/apagar zz_media/Tribucia.png | Leaflet layer | Mapa base desaparece. | zz_media/Tribucia.png | Manter imagem ou atualizar todas as layers no JSON. |
| Editar supercharged-links-gen.css diretamente | Snippet gerado | Mudança será sobrescrita. | .obsidian/snippets/supercharged-links-gen.css | Editar via plugin/Style Settings ou copiar para outro snippet. |
| Remover NoteIcon | Icon Folder/tema/frontmatter | Pode alterar ícones visuais. | .trash/City Forces/Blueforce.md, CALENDAR.md, Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md +127 | Tratar como campo visual até prova contrária. |
| Remover banner-* da Home | Home/dashboard | Home perde composição visual. | Home.md | Preservar até recriar dashboard equivalente. |
| Alterar #home/#story/#territory/#location | Home DataCards | Seções da Home ficam vazias. | Home.md | Atualizar consultas DataCards simultaneamente. |
| Alterar location/territory/faction | Dataview de residentes/personagens | Tabelas retornam vazio/inconsistência. | Home.md, Legacy - Disgraceland Scratch Notes.md, Territories/ASHMOOR.md, Territories/CHARSPIRE.md, Territories/GUTTER ROW.md, Territories/STEELTOWN.md, Territories/THRESHTON.md, Workflow/Scratch Notes.md | Mapear valores antigos para novos e validar consultas. |
| Remover snippets de callout | CSS snippets | Retratos, cards e dashboard perdem layout. | dgl.css, videopop.css, world.css | Manter até documentar substituição visual. |
| Mudar pastas Characters/Factions/Territories | FROM em Dataview/DataCards | Consultas deixam de encontrar notas. | Home.md, Legacy - Disgraceland Scratch Notes.md, Territories/ASHMOOR.md, Territories/CHARSPIRE.md, Territories/GUTTER ROW.md, Territories/STEELTOWN.md, Territories/THRESHTON.md, Workflow/Scratch Notes.md | Atualizar todos os FROM ou manter compatibilidade. |
| Assumir campos vazios como inúteis | Template/frontmatter | Plugins/templates podem esperar campo. | .trash/City Forces/Blueforce.md, CALENDAR.md, Characters/Individual/Ava Victoria.md, Characters/Individual/Bastian Redd.md, Characters/Individual/Bobby Cutman.md, Characters/Individual/Cassidy LaRue.md, Characters/Individual/Dusty Dillon.md, Characters/Individual/Flint Garritt.md +57 | Só remover após checar consultas, CSS, templates e plugins. |
| Apagar mídia órfã por análise textual simples | zz_media + JSON/CSS/canvas | Pode quebrar uso em plugin/CSS/canvas. | zz_media/003.png, zz_media/004.png, zz_media/07.png, zz_media/071.png, zz_media/0711.png, zz_media/08.png, zz_media/081.png, zz_media/1011.mp4 +140 | Checar JSON, CSS, canvas e plugins antes de apagar. |

## Mídia possivelmente órfã

Arquivos em `zz_media`: 425. Referenciados textualmente em Markdown/frontmatter: 277. Possíveis órfãos por análise textual simples: 148. Não apagar sem checar CSS/JSON/canvas/plugins.

| arquivo |
| --- |
| zz_media/003.png |
| zz_media/004.png |
| zz_media/07.png |
| zz_media/071.png |
| zz_media/0711.png |
| zz_media/08.png |
| zz_media/081.png |
| zz_media/1011.mp4 |
| zz_media/1lg.png |
| zz_media/1rr.png |
| zz_media/Characters.png |
| zz_media/Map2.png |
| zz_media/Territories.png |
| zz_media/Tribucia.png |
| zz_media/ashban.png |
| zz_media/b1.png |
| zz_media/banchar.png |
| zz_media/bangr.png |
| zz_media/bantd.png |
| zz_media/banth.png |
| zz_media/bash.png |
| zz_media/bc.png |
| zz_media/bf 1.png |
| zz_media/bobby.png |
| zz_media/brc.png |
| zz_media/bsi.png |
| zz_media/bside.png |
| zz_media/burn.mp3 |
| zz_media/bvsb.png |
| zz_media/cal.png |
| zz_media/canv.png |
| zz_media/charban 1.png |
| zz_media/charban.png |
| zz_media/charmap.png |
| zz_media/chbar.png |
| zz_media/cray.png |
| zz_media/d.png |
| zz_media/dban.png |
| zz_media/dban1.png |
| zz_media/dglban.png |
| zz_media/dlban.png |
| zz_media/dstory.png |
| zz_media/duk.png |
| zz_media/ent.png |
| zz_media/ep.png |
| zz_media/epp1121.png |
| zz_media/epp121.png |
| zz_media/epp21.png |
| zz_media/ex.png |
| zz_media/fade.png |
| zz_media/fgt 1.png |
| zz_media/fgt.png |
| zz_media/fightf.png |
| zz_media/firebay.png |
| zz_media/fr.png |
| zz_media/freddy.png |
| zz_media/grban.png |
| zz_media/grd.png |
| zz_media/gutt.png |
| zz_media/guttr.png |
| zz_media/jdmj.png |
| zz_media/jdmj2.png |
| zz_media/jimmy1.png |
| zz_media/jk.png |
| zz_media/lash2.png |
| zz_media/lchar.png |
| zz_media/lg.png |
| zz_media/lmap.png |
| zz_media/maaap.png |
| zz_media/maap.png |
| zz_media/map3211.png |
| zz_media/mapqq.png |
| zz_media/mash.png |
| zz_media/mfight 1.png |
| zz_media/mfight.png |
| zz_media/mjfight.png |
| zz_media/music.png |
| zz_media/nem.png |
| zz_media/news.png |
| zz_media/nico2.png |
| zz_media/notes.jpg |
| zz_media/notes11.png |
| zz_media/notey.png |
| zz_media/outey.png |
| zz_media/rc.png |
| zz_media/ru.png |
| zz_media/sban.png |
| zz_media/sc.png |
| zz_media/script.png |
| zz_media/sert.png |
| zz_media/showdown.png |
| zz_media/showdown1.png |
| zz_media/sliver2.png |
| zz_media/smap.png |
| zz_media/sod.png |
| zz_media/sool2.png |
| zz_media/sound.png |
| zz_media/sports.png |
| zz_media/stand.png |
| zz_media/steel.png |
| zz_media/steelban.png |
| zz_media/stella.png |
| zz_media/swcban.png |
| zz_media/t5.png |
| zz_media/t51.png |
| zz_media/t9.png |
| zz_media/tes1.png |
| zz_media/test1.png |
| zz_media/test2.png |
| zz_media/th_bc.png |
| zz_media/th_bd.png |
| zz_media/th_bobby.png |
| zz_media/th_cass.png |
| zz_media/th_cb.png |
| zz_media/th_cg.png |
| zz_media/th_da.png |
| zz_media/th_danny.png |
| zz_media/th_dd.png |
| zz_media/th_dp.png |
| zz_media/th_duke.png |
| zz_media/th_ew 1.png |
| zz_media/th_fb.png |
| zz_media/th_gb.png |
| zz_media/th_hl.png |
| zz_media/th_jclay.png |
| zz_media/th_jdd.png |
| zz_media/th_kataq.png |
| zz_media/th_lb.png |
| zz_media/th_marl.png |
| zz_media/th_mjj.png |
| zz_media/th_mr.png |
| zz_media/th_quin.png |
| zz_media/th_rach.png |
| zz_media/th_ray.png |
| zz_media/th_rott 1.png |
| zz_media/th_se.png |
| zz_media/th_shana 1.png |
| zz_media/th_slc.png |
| zz_media/th_stacy.png |
| zz_media/th_stella.png |
| zz_media/th_sv.png |
| zz_media/th_ta.png |
| zz_media/th_za.png |
| zz_media/thrban.png |
| zz_media/uwban.png |
| zz_media/vpreach.png |
| zz_media/wood.png |
| zz_media/yes.png |