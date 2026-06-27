> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG DATAVIEW DATACARDS REQUIREMENTS

Requisitos de consultas para um vault de RPG de mesa.

Os exemplos são conceituais e não devem ser aplicados em notas reais nesta etapa.

## 1. Princípios

Dataview deve responder perguntas operacionais. DataCards deve responder perguntas visuais.

Dataview é melhor para:

- listas rápidas;
- tabelas filtradas;
- controle de status;
- validação de campos;
- histórico de sessões.

DataCards é melhor para:

- personagens;
- facções;
- locais;
- handouts;
- itens;
- mapas;
- sessões recentes.

## 2. Personagens por facção

```dataview
TABLE thumbnail, life_status, location, role
FROM "Characters"
WHERE contains(tags, "character")
AND faction = this.file.link
SORT file.name ASC
```

Versão por tag:

```datacards
TABLE thumbnail, location, life_status FROM #faction_tag
SORT file.name ASC

// Settings
preset: compact
columns: 5
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## 3. Personagens por região

```dataview
TABLE thumbnail, location, faction, life_status
FROM "Characters"
WHERE territory = this.file.link OR region = this.file.link
SORT location ASC
```

## 4. NPCs vivos, mortos e desaparecidos

```dataview
TABLE thumbnail, location, faction, role
FROM "Characters"
WHERE subtype = "npc"
AND life_status = "alive"
SORT file.name ASC
```

```dataview
TABLE thumbnail, location, faction, role
FROM "Characters"
WHERE life_status = "dead" OR life_status = "missing"
SORT life_status ASC
```

## 5. Personagens que apareceram em uma sessão

Modelo com `sessions`:

```dataview
LIST
FROM "Characters"
WHERE contains(sessions, this.file.name)
SORT file.name ASC
```

Modelo compatível com `chapters`:

```dataview
LIST
FROM "Characters"
WHERE contains(chapters, this.file.name)
SORT file.name ASC
```

## 6. Facções ativas

```datacards
TABLE thumbnail, leader, territory, status FROM #faction
WHERE status = "Active"

// Settings
preset: grid
columns: 4
imageProperty: thumbnail
```

## 7. Locais por território

```datacards
TABLE cover, territory, danger_level, status FROM #location
WHERE territory = this.file.link
SORT file.name ASC

// Settings
preset: grid
columns: 4
imageProperty: cover
```

## 8. Quests abertas

```dataview
TABLE status, location, faction, hooks, player_known
FROM #quest
WHERE status = "open"
SORT danger_level DESC
```

## 9. Rumores disponíveis

```dataview
TABLE source, location, truth_status, player_known
FROM #rumor
WHERE status = "available"
AND player_known = false
SORT location ASC
```

## 10. Handouts liberados

```datacards
TABLE handout_image, revealed_in, description FROM #handout
WHERE handout_status = "revealed"

// Settings
preset: grid
columns: 4
imageProperty: handout_image
```

## 11. Segredos ainda não revelados

```dataview
TABLE spoiler_level, location, faction, revealed_in
FROM "/"
WHERE visibility = "Mestre"
AND player_known = false
AND spoiler_level != "none"
SORT spoiler_level DESC
```

## 12. Sessões por arco

```dataview
TABLE date, in_game_date, description
FROM #session
WHERE contains(arcs, this.file.name)
SORT session_number ASC
```

## 13. Imagens por tipo

Retratos:

```dataview
TABLE portrait, type, subtype, media_status
FROM "/"
WHERE portrait
SORT type ASC
```

Handouts:

```dataview
TABLE handout_image, handout_status, revealed_in
FROM #handout
SORT handout_status ASC
```

Mapas:

```dataview
TABLE map_image, region, visibility
FROM #map
SORT region ASC
```

## 14. Dashboard do mestre

Blocos recomendados:

- sessão atual;
- NPCs em cena;
- quests abertas;
- rumores disponíveis;
- segredos não revelados;
- handouts prontos;
- facções ativas;
- locais do território atual;
- últimos arquivos modificados.

Exemplo:

```dataview
TABLE WITHOUT ID
link(file.path, file.folder + " / " + file.name) AS "Modificado",
file.mtime AS "Data"
FROM "/"
WHERE file.mtime >= date(today) - dur(14 days)
SORT file.mtime DESC
LIMIT 10
```

## 15. Requisitos de compatibilidade

- Manter `thumbnail` para cards pequenos.
- Manter `cover` para cards de capa.
- Manter `chapters` até `sessions` estar validado.
- Usar `tags` para DataCards quando compatível.
- Evitar consultas que dependem de texto livre instável quando um campo estruturado puder existir.

## 16. Critérios de qualidade

Uma consulta RPG é boa se:

- responde uma pergunta de mesa;
- usa campos estáveis;
- funciona em mobile;
- não vaza segredo em painel de jogador;
- deixa claro se usa `thumbnail`, `cover` ou outro campo de mídia;
- possui fallback ou regra de compatibilidade para campos legados.
