> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG MAP AND CALENDAR REQUIREMENTS

Requisitos para mapas e calendário em um vault de RPG.

Não aplica mudanças. Não compara com Omnisvera.

## 1. Mapas necessários

Um vault de RPG pode precisar de múltiplas escalas:

- mapa de mundo;
- continente;
- reino;
- região;
- território;
- cidade;
- vila;
- dungeon;
- andar;
- sala/área;
- mapa público;
- mapa do mestre.

## 2. Contrato de mapa

Cada mapa precisa saber:

- tipo de mapa;
- imagem base;
- escala;
- região associada;
- visibilidade;
- marcadores;
- notas linkadas;
- versão pública ou privada.

Campos candidatos:

```yaml
type: map
subtype: region
map_image: zz_media/maps/region.png
region: "[[Region]]"
visibility: Mestre
scale:
tags:
  - map
```

## 3. Leaflet

Leaflet é útil para RPG porque:

- transforma imagem em mapa navegável;
- permite marcadores clicáveis;
- organiza tipos de marcador;
- conecta geografia a notas.

Contrato:

- `id` do mapa deve ser estável;
- `image` deve apontar para arquivo existente;
- marcadores devem linkar notas existentes;
- renomear nota exige atualizar marcador;
- mover imagem exige atualizar bloco e JSON.

## 4. Tipos de marcadores

Tipos úteis:

- região;
- cidade;
- vila;
- dungeon;
- ponto de interesse;
- facção;
- NPC;
- ameaça;
- segredo;
- handout;
- evento;
- portal/passagem.

Cada tipo pode ter cor/ícone próprio.

## 5. Mapa de mestre vs mapa de jogador

Campos:

```yaml
visibility: Mestre
player_known: false
```

Regras:

- mapa do mestre pode conter marcadores secretos;
- mapa de jogador só deve conter locais revelados;
- se necessário, usar duas notas ou duas imagens;
- não depender apenas de tags para esconder spoiler.

## 6. Calendário diegético

O calendário precisa registrar:

- data atual em jogo;
- dias da semana;
- meses;
- estações;
- feriados;
- eventos religiosos;
- eventos históricos;
- eventos futuros;
- sessões jogadas.

Calendarium é útil porque já guarda calendário e eventos em JSON.

## 7. Sessões vinculadas a datas

Campos candidatos em sessão:

```yaml
type: session
date: 2026-06-26
in_game_date: 12th of Bloomsun, 2186
session_number: 1
```

Consulta:

```dataview
TABLE date, in_game_date, description
FROM #session
SORT session_number ASC
```

## 8. Eventos históricos

Eventos históricos podem ser notas de lore ou eventos no calendário:

```yaml
type: lore
subtype: historical_event
historical_date:
visibility: Público
player_known: true
```

## 9. Eventos futuros

Eventos futuros precisam de controle de spoiler:

```yaml
type: event
in_game_date:
visibility: Mestre
spoiler_level: heavy
player_known: false
```

## 10. Feriados e religiões

Religiões e feriados devem se conectar:

- calendário lista feriado;
- nota de religião explica significado;
- eventos apontam para religião/culto;
- quests podem depender de data.

## 11. Timeline de campanha

Além do calendário diegético, o vault precisa de timeline:

- ordem histórica do mundo;
- ordem das sessões;
- revelações;
- mortes;
- mudanças políticas;
- conclusão de quests;
- alterações territoriais.

Campos candidatos:

```yaml
timeline_date:
event_type:
related_sessions:
related_factions:
```

## 12. Riscos

- Renomear nota quebra marcador Leaflet.
- Mover mapa quebra layer.
- Alterar `id` do Leaflet quebra associação.
- Duplicar mapa público/privado sem regra gera vazamento.
- Renomear sessão quebra eventos de Calendarium.
- Eventos futuros podem aparecer em dashboard de jogador se filtro falhar.

## 13. Critérios de validade

Sistema de mapa/calendário é válido se:

- mapas abrem no Obsidian;
- marcadores linkam notas existentes;
- imagens existem;
- calendário renderiza;
- eventos apontam para notas existentes;
- dashboards filtram visibilidade;
- datas de sessão e datas em jogo estão separadas.
