# RPG TEMPLATE TAXONOMY

Taxonomia ideal de templates para um vault de RPG de mesa baseado nos contratos técnicos do Disgraceland.

Não compara com Omnisvera. Não define campos obrigatórios finais. Não aplica nada em notas reais.

| tipo | função | pasta sugerida | campos críticos | plugins | imagem | Dataview | DataCards | dashboard | risco de migração |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Player Character | Personagem jogador, vínculo com jogador e mecânica resumida | `Characters/Players` | `type`, `subtype`, `status`, `life_status`, `player`, `old_dragon_class`, `old_dragon_race`, `level`, `thumbnail`, `portrait`, `sessions`, `tags` | Dataview, DataCards, Supercharged Links | Sim | Sim | Sim | Sim | Alto: mistura ficha mecânica e narrativa |
| NPC Importante | NPC recorrente com retrato, facção, segredos e aparições | `Characters/NPCs/Important` | `type`, `subtype`, `life_status`, `location`, `territory`, `faction`, `role`, `visibility`, `thumbnail`, `portrait`, `sessions`, `hooks` | Dataview, DataCards, Supercharged Links | Sim | Sim | Sim | Sim | Alto: aparece em múltiplas consultas |
| NPC Menor | NPC rápido, consultável, menos detalhado | `Characters/NPCs/Minor` | `type`, `subtype`, `life_status`, `location`, `faction`, `role`, `visibility`, `tags` | Dataview, Supercharged Links | Opcional | Sim | Opcional | Opcional | Médio: pode virar NPC importante |
| Antagonista | Ameaça ou vilão com status, plano e perigo | `Characters/Antagonists` | `type`, `subtype`, `danger_level`, `life_status`, `faction`, `location`, `gm_secret`, `hooks`, `thumbnail`, `portrait`, `tags` | Dataview, DataCards, Supercharged Links | Sim | Sim | Sim | Sim | Alto: contém spoilers e segredos |
| Facção | Grupo com membros, líder, território, objetivos e relações | `Factions` | `type`, `status`, `leader`, `territory`, `region`, `danger_level`, `visibility`, `thumbnail`, `tags` | DataCards, Dataview, Supercharged Links | Sim | Sim | Sim | Sim | Alto: tags visuais e agrupamento |
| Região/Território | Área ampla do mapa, com locais e facções | `Territories` | `type`, `region`, `leader`, `population`, `cover`, `map`, `tags` | Dataview, DataCards, Leaflet | Sim | Sim | Sim | Sim | Alto: geografia e mapa dependem de nomes |
| Cidade/Vila/Assentamento | Ponto habitado dentro de uma região | `Locations/Settlements` | `type`, `subtype`, `territory`, `region`, `population`, `leader`, `faction`, `cover`, `tags` | Dataview, DataCards, Leaflet | Sim | Sim | Sim | Sim | Alto: pivô de NPCs/quests |
| Local/Dungeon | Local explorável, dungeon, ruína, taverna, sede | `Locations` ou `Dungeons` | `type`, `subtype`, `territory`, `district`, `danger_level`, `cover`, `map_image`, `hooks`, `tags` | Dataview, DataCards, Leaflet | Sim | Sim | Sim | Sim | Alto: mapa e encontros podem depender dele |
| Lore | Conceito de mundo, evento histórico, regra diegética | `Lore` | `type`, `canon_status`, `visibility`, `player_known`, `cover`, `tags` | Dataview, Supercharged Links | Opcional | Sim | Opcional | Opcional | Médio: pode conter spoiler |
| Religião/Culto | Fé, culto, igreja, doutrina ou seita | `Religion` | `type`, `status`, `leader`, `region`, `faction`, `visibility`, `cover`, `tags` | Dataview, DataCards, Supercharged Links | Opcional | Sim | Opcional | Opcional | Médio/alto: cruza facção e lore |
| Sessão/Capítulo | Registro de sessão, recap e elenco | `Sessions` ou `Campaign/Chapters` | `type`, `date`, `in_game_date`, `arc`, `cover`, `description`, `tags`, `participants` | Dataview, DataCards, Calendarium | Opcional | Sim | Sim | Sim | Alto: substitui/convive com `chapters` |
| Arco de Campanha | Conjunto de sessões/quests/revelações | `Campaign/Arcs` | `type`, `status`, `sessions`, `quests`, `factions`, `cover`, `tags` | Dataview, DataCards | Opcional | Sim | Sim | Sim | Médio: agregador estrutural |
| Quest/Gancho | Objetivo aberto, pista ou direção de ação | `Quests` | `type`, `status`, `visibility`, `player_known`, `location`, `faction`, `hooks`, `sessions`, `tags` | Dataview, DataCards | Opcional | Sim | Sim | Sim | Alto: precisa separar público/segredo |
| Item/Artefato | Item mágico, relíquia, objeto de pista ou recompensa | `Items` | `type`, `subtype`, `status`, `owner`, `location`, `visibility`, `thumbnail`, `cover`, `tags` | Dataview, DataCards, Supercharged Links | Sim | Sim | Sim | Opcional | Médio: pode virar handout |
| Encontro | Cena mecânica/social/exploratória planejada | `Encounters` | `type`, `subtype`, `danger_level`, `location`, `participants`, `session`, `gm_secret`, `tags` | Dataview | Opcional | Sim | Opcional | Sim | Alto: informação de mestre |
| Rumor | Informação circulante verdadeira/falsa/parcial | `Rumors` | `type`, `status`, `truth_status`, `visibility`, `player_known`, `source`, `location`, `tags` | Dataview, DataCards | Não obrigatório | Sim | Sim | Sim | Alto: controle de revelação |
| Handout | Material entregável aos jogadores | `Handouts` | `type`, `visibility`, `player_known`, `revealed_in`, `handout_image`, `media_status`, `tags` | Dataview, DataCards, Media | Sim | Sim | Sim | Sim | Alto: público vs secreto |
| Mapa | Nota de mapa Leaflet ou índice de mapa | `Maps` | `type`, `map_image`, `scale`, `region`, `visibility`, `tags` | Leaflet, Dataview | Sim | Sim | Opcional | Sim | Muito alto: links/marcadores |
| Mídia | Registro/documentação de asset visual/áudio | `Media Index` ou `zz_media` com notas auxiliares | `type`, `media_status`, `media_kind`, `visibility`, `used_by`, `tags` | DataCards, Dataview, Media Extended | Sim | Sim | Sim | Opcional | Alto: não apagar sem validação |

## Observações por família

### Personagens

Todos os personagens precisam responder rapidamente:

- quem é;
- onde está;
- facção;
- status de vida;
- se é conhecido pelos jogadores;
- em quais sessões apareceu;
- qual imagem pode ser mostrada.

### Facções

Facções devem manter tags visuais estáveis. No modelo Disgraceland, tag de facção é simultaneamente lore, filtro e estilo de link. Em RPG, esse comportamento continua útil.

### Geografia

O modelo RPG deve separar território, assentamento, local e dungeon. A hierarquia evita misturar escala regional com pontos visitáveis.

### Sessões

Sessão/Capítulo vira o eixo de histórico. Ela precisa substituir o uso puramente narrativo de `story` por um registro jogável: elenco, decisões, pistas reveladas, consequências e data.

### Handouts e rumores

Esses tipos são centrais em RPG e precisam existir explicitamente. Disgraceland usa notícia/story/lore, mas RPG precisa controlar liberação.

## Regra de desenho

Todo template de RPG deve declarar:

- se aparece para jogadores;
- se pode entrar em dashboard;
- qual mídia usa;
- quais consultas depende;
- quais tags têm função visual;
- quais campos não podem ser removidos numa migração futura.
