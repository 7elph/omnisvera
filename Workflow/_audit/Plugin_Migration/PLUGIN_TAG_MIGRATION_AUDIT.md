# Auditoria de Migração de Tags em Plugins

Data: 2026-06-27

Objetivo: auditar onde tags e vocabulário herdados do Disgraceland ainda existem fora do legado antes de alterar configurações.

## Comandos de auditoria

```powershell
rg -n "loyalist|rancher|pirate|widow|third|murray|steeltown|water|individual|religion|territory|story" .obsidian `
  --glob '!**/main.js' `
  --glob '!**/*.map'

rg -n "#(loyalist|rancher|pirate|widow|third|murray|steeltown|water|individual|religion|territory|story)\b|FROM #(loyalist|rancher|pirate|widow|third|murray|steeltown|water|individual|religion|territory|story)\b" `
  Home.md Home_Mestre.md Templates Characters Factions Territories Locations Lore Religion EARTHROPO CAMPANHA Workflow `
  --glob '!Workflow/Legacy/**' `
  --glob '!Workflow/_audit/**' `
  --glob '!Workflow/RPG_SYSTEM_DESIGN/**' `
  --glob '!Workflow/COMPATIBILITY_LAYER/**'
```

## Ocorrências por arquivo

| arquivo | classificação | tags/termos | ação |
|---|---|---|---|
| `.obsidian/plugins/supercharged-links-obsidian/data.json` | PLUGIN_CONFIG | `steeltown`, `individual`, `religion`, `territory`, `loyalist`, `widow`, `pirate`, `rancher`, `third`, `murray`, `water`, `story` | Migrar apenas tags aprovadas, preservar `third`, `murray`, `story`. |
| `.obsidian/plugins/obsidian-style-settings/data.json` | PLUGIN_CONFIG | UIDs de Supercharged Links, não nomes de tags | Não alterar; cores/pesos seguem os UIDs. |
| `.obsidian/snippets/supercharged-links-gen.css` | GENERATED_CSS | seletores por tags antigas | Atualizar controladamente se a config fonte for migrada. |
| `.obsidian/snippets/omnisvera-profile.css` | CSS_SNIPPET | `region-steeltown` | Não alterar nesta etapa; precisa decisão CSS/regional. |
| `.obsidian/graph.json` | PLUGIN_CONFIG | `tag: #territory` | Atualizar para `tag: #territorio` quando a tag visual for migrada. |
| `Home.md` | DASHBOARD | `FROM #session OR #story` | Remover `#session`; manter `#story` por enquanto. |
| `Home_Mestre.md` | DASHBOARD | `FROM #story`, `FROM #territory`, links a Disgraceland | Migrar `#territory` para `#territorio`; manter `#story`; remover links operacionais ao legado. |
| `Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md` | ARCHIVE | `#session`, `#story` | Não operacional; não alterar nesta etapa. |
| `Templates/Characters/*` | TEMPLATE | campos rejeitados e `portrait` | Atualizar templates ativos para taxonomia Sage. |
| `Templates/Classes/*` | TEMPLATE | campos rejeitados e consultas por `life_status`/`canon_status` | Atualizar templates ativos para taxonomia Sage. |

## Mapa de migração aprovado

| antigo | novo | aplicar agora? | motivo |
|---|---|---:|---|
| `loyalist` | `coroa-de-nimalia` | sim | Decisão aprovada. |
| `rancher` | `guilda-dos-mercadores` | sim | Decisão aprovada. |
| `pirate` | `conclave-dos-errantes` | sim | Decisão aprovada. |
| `widow` | `guardioes-do-veu-cinzento` | sim | Decisão aprovada. |
| `steeltown` | `nimalia` | sim, com ressalva | Pode representar contexto/reino; revisar depois com `nimalis`. |
| `water` | `mar-da-neblina` | sim | Decisão aprovada. |
| `individual` | `personagem` | sim | Decisão aprovada. |
| `religion` | `religiao` | sim | Decisão aprovada. |
| `territory` | `territorio` | sim | Decisão aprovada. |
| `lore` | `lore` | não precisa | Já compatível. |
| `third` | pendente | não | Não aplicar `terceira-fileira`; precisa decisão Sage. |
| `murray` | pendente | não | Precisa decisão entre `nobreza-de-nimalia` e `nobreza-de-nimalis`. |
| `story` | pendente controlado | não | Não virar `sessions`; manter por enquanto. |

## Risco por plugin/configuração

| componente | risco | controle |
|---|---|---|
| Supercharged Links config | Alto se UIDs forem recriados ou tags antigas removidas sem equivalência. | Preservar UIDs, alterar apenas `value` das tags aprovadas. |
| Style Settings | Médio se UIDs mudarem. | Não mudar UIDs. |
| CSS gerado | Médio porque é arquivo gerado. | Alterar apenas strings de tags aprovadas e documentar que deve ser regenerado/validado no Obsidian. |
| Graph | Baixo/médio. | Ajustar filtro `tag: #territory` para `tag: #territorio`. |
| Homepage | Baixo. | Não alterar; já aponta para `Home`. |
| Leaflet | Baixo nesta etapa. | Não alterar; mudança local observada é `lastAccessed`. |
| Calendarium | Baixo nesta etapa. | Não alterar; sem migração de calendário agora. |

## Decisão de execução

Pode executar nesta etapa:

1. migrar tags aprovadas em `.obsidian/plugins/supercharged-links-obsidian/data.json`;
2. preservar UIDs e Style Settings;
3. atualizar `.obsidian/snippets/supercharged-links-gen.css` de forma controlada para manter visual imediato;
4. atualizar `.obsidian/graph.json` de `#territory` para `#territorio`;
5. remover `#session` dos dashboards ativos;
6. atualizar templates ativos sem aplicar em notas existentes.

Não executar nesta etapa:

- migrar `third`;
- migrar `murray`;
- renomear `story`;
- alterar `omnisvera-profile.css`;
- renomear pastas operacionais.
