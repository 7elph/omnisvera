# Relatório de Migração de Dataview, DataCards e Templates

Data: 2026-06-27

Objetivo: registrar quais consultas e templates ativos precisam sair do vocabulário legado e aderir à taxonomia Omnisvera.

## Dashboards ativos

| arquivo | consulta atual | problema | ação |
|---|---|---|---|
| `Home.md` | `FROM #session OR #story` | `sessions` foi rejeitado pela decisão do Sage. | Remover `#session`, manter `#story` por enquanto. |
| `Home_Mestre.md` | `TABLE cover, date, description FROM #story AND #earthropo` | `#story` ainda permitido temporariamente. | Manter. |
| `Home_Mestre.md` | `TABLE cover, region, leader, population FROM #territory` | `territory` deve migrar para `territorio`. | Atualizar para `#territorio`. |
| `Home_Mestre.md` | links para comparação/auditoria Disgraceland | Disgraceland não deve aparecer como camada operacional. | Trocar por taxonomia, plano de remoção e auditoria de plugins. |

## Templates de personagens

Arquivos:

- `Templates/Characters/Antagonista.md`;
- `Templates/Characters/Criatura.md`;
- `Templates/Characters/NPC Importante.md`;
- `Templates/Characters/NPC Menor.md`;
- `Templates/Characters/Personagem Jogador.md`.

Campos a remover dos templates novos:

- `subtype`;
- `work_status`;
- `canon_status`;
- `requires_review`;
- `life_status`;
- `portrait`.

Campos a preservar/adicionar:

- `type`;
- `NoteIcon`;
- `visibility`;
- `spoiler_level`;
- `gm_secret`;
- `revealed_in`;
- `created_by`;
- `campaign_status`;
- `name`;
- `race`;
- `class`;
- `status`;
- `role`;
- `origin`;
- `location`;
- `territory`;
- `faction`;
- `faith`;
- `thumbnail`;
- `cover`;
- `arcs`;
- `chapters`;
- `tags`.

Observação: `thumbnail` será usado também como imagem de retrato nos callouts, em vez de `portrait`.

## Templates de classes

Arquivos:

- `Templates/Classes/Arquétipo Narrativo.md`;
- `Templates/Classes/Classe Base.md`;
- `Templates/Classes/Especialização.md`.

Campos a remover dos templates novos:

- `subtype`;
- `work_status`;
- `canon_status`;
- `requires_review`;
- `source`;
- `source_type`.

Campos a preservar/adicionar:

- `type`;
- `visibility`;
- `spoiler_level`;
- `gm_secret`;
- `revealed_in`;
- `created_by`;
- `campaign_status`;
- `rules_status`;
- `name`;
- `aliases`;
- `system`;
- `class_group`;
- `primary_attribute`;
- `hit_die`;
- `armor_allowed`;
- `weapons_allowed`;
- `magic_type`;
- `role_in_party`;
- `narrative_role`;
- `related_characters`;
- `related_factions`;
- `related_items`;
- `related_lore`;
- `related_races`;
- `thumbnail`;
- `cover`;
- `tags`.

## Consultas a ajustar

| origem | consulta/campo | ação |
|---|---|---|
| `Templates/Classes/*` | `TABLE thumbnail, race, life_status, location, faction` | Trocar `life_status` por `status`. |
| `Templates/Classes/*` | `TABLE work_status, rules_status, campaign_status, canon_status` | Trocar por `TABLE rules_status, campaign_status, visibility, danger_level`. |
| `Templates/Characters/*` | imagem `![[portrait|400]]` | Trocar por `![[thumbnail|400]]`. |
| dashboards | `#territory` | Trocar por `#territorio`. |
| dashboards | `#session` | Remover. |

## Pendências controladas

| item | decisão |
|---|---|
| `third` | Não migrar automaticamente. |
| `murray` | Não migrar automaticamente. |
| `story` | Manter até decisão entre `story` e `capitulo`. |
| `region-steeltown` | CSS manual; revisar em etapa visual. |
| Pastas PT-BR | Planejar, não renomear agora. |
