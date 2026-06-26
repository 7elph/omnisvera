# Template Compatibility Matrix

Comparação de templates técnicos entre Disgraceland, modelo RPG desejado e Omnisvera atual.

| template | Disgraceland | RPG desejado | Omnisvera atual | lacuna | risco | decisão necessária |
| --- | --- | --- | --- | --- | --- | --- |
| Character | Template único de personagem com retrato, overview, biography, personality, role e `chapters`. | Base comum para PC/NPC/antagonista. | Parcial, com variações RPG. | Validar notas reais contra template. | Médio | Definir contrato base comum. |
| Player Character | Não separado. | Template próprio com jogador, nível, classe, raça, aparições. | Template/estrutura parcial existe. | Campos Old Dragon e visibilidade incompletos. | Médio | Definir campos mecânicos mínimos. |
| NPC Importante | Não separado. | NPC com retrato, facção, segredos e papel recorrente. | Template parcial existe. | Falta contrato de segredo/revelação. | Alto | Definir visibilidade. |
| NPC Menor | Não separado. | Nota leve, rápida para mesa. | Template parcial existe. | Campos mínimos precisam decisão. | Médio | Definir template enxuto. |
| Antagonista | Não separado. | Objetivos, ameaça, perigo, segredos. | Template parcial existe. | `danger_level` não operacional. | Médio | Definir mecânica de perigo. |
| Faction | Template de facção com tags, leader, status, thumbnail e cards. | Facção RPG ativa/inativa, influência, membros. | Parcial. | Tags antigas podem dominar visual. | Médio | Mapear tags antigas para RPG. |
| Territory | Template de território com cover, region, leader, population. | Região/reino com mapa, fronteira e locais. | Parcial. | Reino, região e assentamento podem se misturar. | Médio | Definir hierarquia geográfica. |
| Settlement | Não separado. | Cidade/vila/assentamento. | Parcial/ambíguo. | Pode estar dentro de Territories ou Locations. | Médio | Criar ou adaptar template. |
| Location/Dungeon | Locations com cover, territory, info. | Local, dungeon, ponto de interesse. | Parcial. | Dungeon não tem contrato próprio. | Médio | Definir subtipo `dungeon`. |
| Lore | Lore com tags, cover/info e cards. | Lore público/secreto/canonizado. | Parcial. | Canon/visibilidade ausentes. | Médio | Definir `canon_status` e visibilidade. |
| Religion | Religião como categoria técnica própria. | Religião/culto/entidade. | Parcial. | Culto e religião podem precisar subtipo. | Médio | Definir taxonomia. |
| Chapter/Session | Capítulo em `DISGRACELAND`; personagens têm `chapters`. | Sessão/capítulo com data, aparições, recompensas. | `chapters` existe; `sessions` ausente. | Ponte ausente. | Alto | Decidir migração de aparições. |
| Campaign Arc | Não separado. | Arco de campanha. | Não suportado como contrato auditado. | Template novo. | Médio | Definir se será nota própria. |
| Quest/Hook | Não separado. | Quest/gatilho com status. | Não suportado como contrato auditado. | Template novo. | Médio | Definir fluxo de quests. |
| Item/Artifact | Não central no template original. | Item mágico/artefato/recompensa. | Parcial/desconhecido. | Campos e cards de item ausentes. | Médio | Definir template de item. |
| Encounter | Não separado. | Preparação de combate/cena. | Não suportado como contrato auditado. | Template novo. | Médio | Definir se será granular. |
| Rumor | Não separado. | Rumor com fonte, confiabilidade, status público. | Não suportado. | Template novo ou campo. | Médio | Decidir modelo. |
| Handout | Não separado. | Nota/mídia liberável para jogador. | Não suportado claramente. | Falta `handout_status`. | Alto | Definir política de revelação. |
| Map | `TRIBUCIA MAP.md` + Leaflet. | Mapas por escala com marcadores. | Parcial via Leaflet. | Campos `map_image` e escala ausentes. | Alto | Definir contratos antes de renomear. |
| Media | `zz_media`, thumbnails/covers/embeds. | Mídia com status, uso e visibilidade. | Parcial; refs quebradas. | Sem template de referência de mídia. | Alto | Definir política de mídia. |

## Templates ausentes ou incompletos prioritários

- Quest/Hook
- Rumor
- Encounter
- Handout
- Campaign Arc
- Media Reference
- Settlement/City/Village
- Dungeon como subtipo operacional

## Conclusão

Omnisvera já começou a se afastar positivamente do template único de personagem de Disgraceland, mas ainda precisa formalizar contratos antes de migrar notas em lote. O principal risco é misturar evolução de template com mudança de campo/tag sem compatibilidade.
