# Plano de Remoção Operacional do Disgraceland

Data: 2026-06-27

Escopo: remover Disgraceland da camada operacional do Omnisvera sem apagar o legado técnico ainda.

## Decisão do Sage

Disgraceland não é mais conteúdo operacional do vault. Apenas o motor funcional herdado pode ser reaproveitado.

O legado técnico permanece em `Workflow/Legacy/Disgraceland` até uma etapa futura de arquivamento ou remoção controlada.

## 1. Onde Disgraceland ainda aparece

Busca executada:

```powershell
rg -l "Disgraceland|TRIBUCIA|loyalist|rancher|pirate|widow|third|murray|steeltown|water" . `
  --glob '!**/.git/**' `
  --glob '!**/node_modules/**' `
  --glob '!**/main.js' `
  --glob '!**/*.png' `
  --glob '!**/*.jpg' `
  --glob '!**/*.jpeg' `
  --glob '!**/*.webp' `
  --glob '!**/*.gif' `
  --glob '!**/*.svg'
```

Resultado resumido:

| área | classificação | observação |
|---|---|---|
| `Workflow/Legacy/Disgraceland` | LEGACY_ONLY | Conteúdo legado preservado; não operacional. |
| `Workflow/Legacy/Disgraceland/_audit` | DOCUMENTATION | Auditoria técnica histórica; pode mencionar Disgraceland. |
| `Workflow/_audit/*` | DOCUMENTATION | Relatórios anteriores; podem mencionar Disgraceland como baseline. |
| `Workflow/RPG_SYSTEM_DESIGN` | DOCUMENTATION | Documentos conceituais; podem mencionar Disgraceland como referência técnica. |
| `Workflow/COMPATIBILITY_LAYER` | DOCUMENTATION | Documentação da camada de compatibilidade; pode citar tags antigas como ponte. |
| `Home_Mestre.md` | OPERATIONAL_DASHBOARD | Ainda tinha links operacionais para comparação e auditoria do Disgraceland. Deve ser limpo. |
| `.obsidian/plugins/supercharged-links-obsidian/data.json` | PLUGIN_CONFIG | Ainda usa tags visuais antigas como seletores. |
| `.obsidian/snippets/supercharged-links-gen.css` | GENERATED_CSS | CSS gerado ainda contém seletores antigos. |
| `.obsidian/snippets/omnisvera-profile.css` | CSS_SNIPPET | Ainda contém classe regional legada `region-steeltown`. |
| `Templates/Characters/*` | TEMPLATE | Templates usam campos agora rejeitados pela taxonomia (`subtype`, `work_status`, `canon_status`, `requires_review`, `life_status`, `portrait`). |
| `Templates/Classes/*` | TEMPLATE | Templates usam campos rejeitados (`subtype`, `work_status`, `canon_status`, `requires_review`, `source`). |
| `Workflow/Templates/Plugin Configs/Calendarium - Disgraceland Template.json` | HISTORICAL_TEMPLATE | Configuração histórica; deve ficar marcada como legado, não operacional. |

## 2. Arquivos dentro de `Workflow/Legacy/Disgraceland`

Contagem observada: 728 arquivos.

Classificação:

- `KEEP_AS_LEGACY_REFERENCE` por enquanto;
- não participar da navegação principal;
- não ser consultado por Home, dashboards, Dataviews ou DataCards operacionais;
- só ser removido/arquivado em commit futuro com inventário próprio.

## 3. Vocabulário antigo encontrado

| termo/tag | estado atual | decisão |
|---|---|---|
| `Disgraceland` | Presente em legado e documentação; também aparecia em dashboard do mestre. | Remover de dashboards operacionais; manter em docs/legado com aviso histórico. |
| `TRIBUCIA` | Presente em legado e relatórios. | Manter apenas em legado/documentação. |
| `loyalist` | Config visual antiga. | Migrar para `coroa-de-nimalia` em configs/consultas ativas. |
| `rancher` | Config visual antiga. | Migrar para `guilda-dos-mercadores`. |
| `pirate` | Config visual antiga. | Migrar para `conclave-dos-errantes`. |
| `widow` | Config visual antiga. | Migrar para `guardioes-do-veu-cinzento`. |
| `third` | Config visual antiga. | Não migrar automaticamente. Decisão pendente. |
| `murray` | Config visual antiga. | Não migrar automaticamente. Decisão pendente. |
| `steeltown` | Config visual antiga e CSS regional. | Migrar tag visual para `nimalia`; classe CSS regional precisa revisão separada. |
| `water` | Config visual antiga. | Migrar para `mar-da-neblina`. |
| `individual` | Config visual antiga. | Migrar para `personagem`. |
| `religion` | Config visual antiga. | Migrar para `religiao`. |
| `territory` | Config visual antiga. | Migrar para `territorio`. |
| `story` | Config visual antiga usada por capítulos. | Não virar `sessions`; manter como `story` ou decidir `capitulo` depois. |

## 4. Dataviews/DataCards com risco

Riscos observados:

- consultas por `FROM #territory`, `FROM #religion` e `FROM #story` ainda refletem vocabulário inglês;
- dashboards atuais usam `FROM "Classes"` em `Home_Mestre.md`, mas a pasta `Classes` ainda não existe como pasta operacional consolidada;
- templates antigos ainda incluem consultas e campos que a taxonomia atual rejeitou;
- consultas antigas em documentação podem permanecer, mas devem ser marcadas como legado se forem exemplos Disgraceland.

Tratamento:

- atualizar consultas ativas e templates;
- não reescrever relatórios históricos;
- documentar consultas pendentes em `DATAVIEW_DATACARDS_TEMPLATE_MIGRATION_REPORT.md`.

## 5. Plugins/configs com nomes antigos

| arquivo | tipo | ação |
|---|---|---|
| `.obsidian/plugins/supercharged-links-obsidian/data.json` | configuração fonte | Migrar tags aprovadas. |
| `.obsidian/plugins/obsidian-style-settings/data.json` | configuração por UID/cor | Não precisa alterar se os UIDs forem preservados. |
| `.obsidian/snippets/supercharged-links-gen.css` | CSS gerado | Atualizar controladamente se a config fonte for migrada e o Obsidian ainda não regenerou. |
| `.obsidian/snippets/omnisvera-profile.css` | snippet CSS manual | Não alterar nesta etapa; classe `region-steeltown` vira pendência CSS. |
| `.obsidian/plugins/homepage/data.json` | Homepage | Já aponta para `Home`; não alterar. |
| `.obsidian/plugins/obsidian-leaflet-plugin/data.json` | Leaflet | Alteração local observada apenas em `lastAccessed`; não incluir. |

## 6. Pode ser removido operacionalmente agora

- Links ativos em `Home_Mestre.md` que tratam Disgraceland como dashboard/fonte operacional.
- Tags antigas aprovadas nas configs do Supercharged Links.
- Tags antigas aprovadas no CSS gerado do Supercharged Links, se a atualização for controlada.
- Campos rejeitados nos templates ativos, preservando `thumbnail`, `cover`, `status`, `chapters` e `tags`.

## 7. Precisa ficar como documentação histórica

- `Workflow/Legacy/Disgraceland`;
- `Workflow/Legacy/Disgraceland/_audit`;
- relatórios em `Workflow/_audit/Comparison`, `Workflow/_audit/Decision_Packet`, `Workflow/RPG_SYSTEM_DESIGN` e `Workflow/COMPATIBILITY_LAYER` que citam Disgraceland como fonte técnica;
- `Workflow/Templates/Plugin Configs/Calendarium - Disgraceland Template.json`, enquanto não houver decisão de descarte.

## 8. Deve ser arquivado depois

| item | motivo |
|---|---|
| `Workflow/Legacy/Disgraceland` | Quando o motor técnico já estiver totalmente migrado e validado no Omnisvera. |
| configs históricas de plugin com `Disgraceland` no nome | Depois que houver equivalente Omnisvera validado. |
| notas/documentos operacionais que só expliquem ponte Disgraceland antiga | Depois que a migração de plugins/templates terminar. |

## 9. Deve ser apagado em commit futuro

Nada nesta etapa.

Apagar deve ser última fase, depois de:

1. migração das tags visuais;
2. validação visual no Obsidian;
3. templates operacionais novos funcionando;
4. Dataview/DataCards sem dependência de vocabulário antigo;
5. relatório de legado indicando o que será removido.

## 10. Ações desta etapa

| ação | status |
|---|---|
| Remover Disgraceland da navegação operacional de `Home_Mestre.md` | executar nesta etapa. |
| Criar taxonomia oficial Omnisvera | executado em `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md`. |
| Auditar plugins antes de alteração | executar em `Workflow/_audit/Plugin_Migration/PLUGIN_TAG_MIGRATION_AUDIT.md`. |
| Migrar Supercharged Links para tags Omnisvera aprovadas | executar se diff for restrito e controlado. |
| Atualizar templates ativos | executar sem aplicar em notas existentes. |
| Renomear pastas | não executar nesta etapa; criar plano. |
