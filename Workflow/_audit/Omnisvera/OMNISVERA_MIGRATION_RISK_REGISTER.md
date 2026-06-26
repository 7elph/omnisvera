# OMNISVERA MIGRATION RISK REGISTER

Gerado em: 2026-06-26 14:06.

Registro técnico do estado atual. Não corrige nem compara.

| risco | origem | impacto | arquivos/dados afetados | como evitar em etapa futura |
| --- | --- | --- | --- | --- |
| Campos críticos ausentes ou pouco usados | frontmatter | consultas futuras podem depender de campo não padronizado | sessions | documentar antes de migrar |
| DataCards dependem de imageProperty | DataCards | cards vazios se thumbnail/cover divergir | Characters/Individual/Raziel.md, Characters/Individual/Vezemir.md, CULTURE.md, EARTHROPO/00 - As Crônicas de Névoa de Sangue.md, EARTHROPO/00 - O Bastardo de Ferro.md, EARTHROPO/00 - O Corvo da Maré Baixa.md, EARTHROPO/EARTHROPO.md, Factions/Guarda Real de Nimalia.md, Home.md, LORE.md +8 | validar campos de mídia |
| Dataview depende de campos/pastas/tags | Dataview | consultas silenciosamente vazias | Characters/Individual/Augustus Terra Decimus.md, Characters/Individual/General Cassian Valerius.md, Home.md, Locations/Leth'valora.md, NOTES.md, Templates/Characters/Antagonista.md, Templates/Characters/Criatura.md, Templates/Characters/NPC Importante.md, Templates/Characters/Personagem Jogador.md, Templates/Classes/Arquétipo Narrativo.md +31 | não renomear sem atualizar consultas |
| Tags recorrentes sem seletor visual | tags/Supercharged | links podem ficar sem diferenciação visual | omnisvera, coroa, character, paladin, antropo, antagonist, chapter01, nimalia, earthropo, Category/Character, draft, npc, elf, missing, mystery +64 | mapear antes de definir sistema visual |
| Tags configuradas sem uso detectado | Supercharged | config visual pode estar obsoleta ou esperando conteúdo | steeltown, individual, loyalist, widow, pirate, rancher, third, murray, water | validar antes de remover |
| Mídia possivelmente órfã | zz_media | risco de apagar arquivo usado por CSS/plugin/fora do Markdown | 35 | análise cruzada antes de remover |
| Referências de mídia não resolvidas | Markdown/frontmatter | imagem quebrada no Obsidian | 69 | corrigir apenas em etapa futura |
| Leaflet depende de links e layers | mapa | renomear nota/imagem quebra mapa | THRESHTON, STEELTOWN, GUTTER ROW, ASHMOOR, CHARSPIRE, THE DROWNLANDS, Coffin Island, Steeltown Wrecking Crew, Hollow House, The Silo, TTV Studios, Tribucia Tribute +70 | atualizar mapa junto com renames |
| Calendarium depende de eventos/notas | calendário | eventos órfãos se notas forem renomeadas | 0 | validar JSON antes de alterações |
| Templates podem não refletir uso real | Templates vs notas | novas notas podem nascer inconsistentes | Templates/Characters/Antagonista.md, Templates/Characters/Criatura.md, Templates/Characters/NPC Importante.md, Templates/Characters/NPC Menor.md, Templates/Characters/Personagem Jogador.md, Templates/Classes/Arquétipo Narrativo.md, Templates/Classes/Classe Base.md, Templates/Classes/Especialização.md | comparar template real vs uso real em etapa futura |

## Campos críticos

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