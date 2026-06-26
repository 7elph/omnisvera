# Home Dashboard Consolidation Review

Data da auditoria: 2026-06-26

Objetivo: identificar arquivos que funcionam, parecem funcionar ou documentam Home/dashboard/homepage/index, sem apagar, mover, renomear ou consolidar automaticamente.

## Resultado executivo

O vault tem três arquivos operacionais no topo:

| arquivo | classificação | função recomendada |
| --- | --- | --- |
| `Home.md` | `OFFICIAL_PORTAL` | Entrada neutra do plugin Homepage; deve apenas direcionar para Mestre/Jogadores. |
| `Home_Mestre.md` | `MASTER_DASHBOARD` | Único dashboard operacional do mestre. |
| `Home_Jogadores.md` | `PLAYER_DASHBOARD` | Único dashboard operacional dos jogadores. |

Interpretação prática: existem só dois dashboards operacionais desejados, `Home_Mestre.md` e `Home_Jogadores.md`. `Home.md` deve existir apenas como portal/roteador porque o plugin Homepage aponta para `Home`.

## Configuração do plugin Homepage

Arquivo lido:

```text
.obsidian/plugins/homepage/data.json
```

Configuração atual:

| chave | valor |
| --- | --- |
| Homepage | `Main Homepage` |
| `value` | `Home` |
| `kind` | `File` |
| `openOnStartup` | `true` |
| `openMode` | `Replace last note` |
| `manualOpenMode` | `Replace last note` |
| `view` | `Reading view` |
| `openWhenEmpty` | `true` |

Conclusão: o Obsidian abre `Home.md` como página inicial. Isso está compatível com `Home.md` como portal neutro.

## Arquivos encontrados por `*home*.md` / `*dashboard*.md`

| arquivo encontrado | função atual aparente | classificação | função recomendada | duplicado? | observação |
| --- | --- | --- | --- | --- | --- |
| `Home.md` | Portal neutro recém-criado. | `OFFICIAL_PORTAL` | Manter como entrada do plugin Homepage. | não | Não deve virar dashboard completo se a meta é ter só Mestre/Jogadores. |
| `Home_Mestre.md` | Dashboard operacional do mestre. | `MASTER_DASHBOARD` | Manter como dashboard do mestre. | não | Pode conter links técnicos, workflow, Legacy e conteúdo secreto. |
| `Home_Jogadores.md` | Dashboard operacional conservador dos jogadores. | `PLAYER_DASHBOARD` | Manter como dashboard dos jogadores. | não | Deve filtrar visibilidade e não apontar para Workflow/Legacy. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | Documento técnico de dashboard. | `TECHNICAL_DOC` | Manter como documentação técnica, não Home operacional. | não | Está modificado localmente fora desta tarefa; não foi usado. |
| `Workflow/_audit/Omnisvera/OMNISVERA_DASHBOARD_MAP_SYSTEMS.md` | Relatório de auditoria técnica. | `TECHNICAL_DOC` | Manter como auditoria. | não | Não é dashboard operacional. |
| `Workflow/COMPATIBILITY_LAYER/DASHBOARD_COMPATIBILITY_RULES.md` | Regras técnicas de compatibilidade. | `TECHNICAL_DOC` | Manter como documentação técnica. | não | Não é dashboard operacional. |
| `Workflow/Legacy/Disgraceland/_audit/templates/HOME_DASHBOARD_TEMPLATE_CONTRACT.md` | Contrato técnico do template legado. | `TECHNICAL_DOC` | Manter como documentação técnica legada. | não | Não operacional em Omnisvera. |
| `Workflow/Legacy/Disgraceland/Home.md` | Home operacional do vault legado de Disgraceland. | `LEGACY_DASHBOARD` | Manter como referência técnica legada. | sim, mas só dentro do legado | Não mover sem plano de Legacy. |
| `Workflow/Legacy/Disgraceland/Workflow/Property Key Dashboard.md` | Dashboard técnico legado de propriedades. | `LEGACY_DASHBOARD` | Manter no legado ou revisar depois. | sim, legado | Não é dashboard operacional de Omnisvera. |
| `Workflow/Property Key Dashboard.md` | Dashboard antigo de propriedades no Workflow ativo. | `NEEDS_SAGE_REVIEW` | Provável documentação técnica ou candidato a arquivamento futuro. | possível | Não mover sem decisão. |
| `Classes/Homem de Armas.md` | Nota de classe; falso positivo por conter “home” em “Homem”. | `NEEDS_SAGE_REVIEW` | Não tratar como Home/dashboard. | não | Não é Home. |
| `Workflow/Legacy/Old Dragon anterior/Legacy - Old Dragon anterior - Homem de Armas.md` | Nota legada de classe; falso positivo por “Homem”. | `NEEDS_SAGE_REVIEW` | Não tratar como Home/dashboard. | não | Não é Home. |

## Arquivos encontrados por `*homepage*.md` / `*index*.md`

| arquivo encontrado | função atual aparente | classificação | função recomendada | observação |
| --- | --- | --- | --- | --- |
| `Workflow/_audit/Cleanup/VAULT_CLEANUP_INDEX.md` | Índice de relatório de limpeza. | `TECHNICAL_DOC` | Manter como índice técnico. | Não é Home. |
| `Workflow/_audit/Comparison/TRIPLE_COMPARISON_INDEX.md` | Índice de comparação. | `TECHNICAL_DOC` | Manter como índice técnico. | Não é Home. |
| `Workflow/_audit/Omnisvera/OMNISVERA_CSS_SNIPPET_INDEX.md` | Índice técnico de snippets. | `TECHNICAL_DOC` | Manter como auditoria. | Não é Home. |
| `Workflow/_audit/Omnisvera/OMNISVERA_DATAVIEW_AND_DATACARDS_INDEX.md` | Índice técnico de consultas. | `TECHNICAL_DOC` | Manter como auditoria. | Não é Home. |
| `Workflow/_audit/Omnisvera/OMNISVERA_PLUGIN_CONFIG_INDEX.md` | Índice técnico de plugins. | `TECHNICAL_DOC` | Manter como auditoria. | Não é Home. |
| `Workflow/AI_CONTEXT/02_ENTITY_INDEX.md` | Índice contextual para IA. | `TECHNICAL_DOC` | Manter como documentação técnica/contextual. | Não é Home. |
| `Workflow/COMPATIBILITY_LAYER/COMPATIBILITY_LAYER_INDEX.md` | Índice da camada de compatibilidade. | `TECHNICAL_DOC` | Manter como documentação técnica. | Não é Home. |
| `Workflow/Legacy/Disgraceland/_audit/CSS_SNIPPET_INDEX.md` | Índice técnico legado. | `TECHNICAL_DOC` | Manter como auditoria legada. | Não é Home. |
| `Workflow/Legacy/Disgraceland/_audit/DATAVIEW_AND_DATACARDS_INDEX.md` | Índice técnico legado. | `TECHNICAL_DOC` | Manter como auditoria legada. | Não é Home. |
| `Workflow/Legacy/Disgraceland/_audit/PLUGIN_CONFIG_INDEX.md` | Índice técnico legado. | `TECHNICAL_DOC` | Manter como auditoria legada. | Não é Home. |
| `Workflow/Legacy/Disgraceland/_audit/templates/DISGRACELAND_TEMPLATE_INDEX.md` | Índice de templates legados. | `TECHNICAL_DOC` | Manter como auditoria legada. | Não é Home. |
| `Workflow/Legacy/Legacy - Archive Index.md` | Índice do arquivo legado. | `TECHNICAL_DOC` | Manter como documentação de arquivo. | Não é Home. |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_SYSTEM_INDEX.md` | Índice do modelo RPG. | `TECHNICAL_DOC` | Manter como documentação técnica. | Não é Home. |

## Arquivos do plugin Homepage encontrados

| arquivo | classificação | observação |
| --- | --- | --- |
| `.obsidian/plugins/homepage/data.json` | configuração de plugin | Aponta para `Home`. Não editar nesta etapa. |
| `.obsidian/plugins/homepage/main.js` | código de plugin | Não editar. |
| `.obsidian/plugins/homepage/manifest.json` | manifesto de plugin | Não editar. |
| `.obsidian/plugins/homepage/styles.css` | estilo de plugin | Não editar. |

## Links e referências diretas

### Links operacionais atuais

| origem | destino | observação |
| --- | --- | --- |
| `Home.md` | `[[Home_Mestre]]` | Portal aponta para dashboard do mestre. |
| `Home.md` | `[[Home_Jogadores]]` | Portal aponta para dashboard dos jogadores. |
| `Home_Jogadores.md` | `[[Home]]` | Jogadores podem voltar ao portal. |
| `Home_Mestre.md` | `[[Home_Jogadores]]` | Mestre pode abrir visão segura dos jogadores. |

### Referências técnicas/históricas

| origem | destino mencionado | classificação |
| --- | --- | --- |
| `.obsidian/plugins/homepage/data.json` | `Home` | Configuração ativa do plugin. |
| `Workflow/_audit/Omnisvera/*` | `Home.md` | Auditoria técnica histórica. |
| `Workflow/_audit/Cleanup/*` | `Home.md`, `Home_Mestre.md`, `Home_Jogadores.md` | Relatórios recentes. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | `Home.md` | Documentação técnica, não Home operacional. |
| `Workflow/Reports/latest_vault_audit.md` | `Home.md` | Relatório antigo; pode estar desatualizado. |
| `Workflow/Legacy/Disgraceland/_audit/*` | `Home.md` | Auditoria do vault legado. |

## Duplicatas ou suspeitos

| arquivo | motivo | recomendação |
| --- | --- | --- |
| `Workflow/Property Key Dashboard.md` | Dashboard antigo no Workflow ativo; pode duplicar documentação/auditoria de propriedades. | `NEEDS_SAGE_REVIEW`; decidir se vira documentação técnica ou arquivo legado em etapa futura. |
| `Workflow/Legacy/Disgraceland/Workflow/Property Key Dashboard.md` | Dashboard legado homônimo. | Manter como legado; não operacional. |
| `Workflow/Reports/latest_vault_audit.md` | Relatório antigo com muitas referências a Home antiga. | `NEEDS_SAGE_REVIEW`; não é dashboard, mas pode confundir auditorias futuras. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | Documento técnico com exemplos de dashboard e alteração local não commitada. | Manter como documentação técnica; não transformar em Home. |

## Consolidação recomendada

Padrão recomendado:

1. `Home.md` permanece como portal neutro e entrada do plugin Homepage.
2. `Home_Mestre.md` permanece como o único dashboard operacional do mestre.
3. `Home_Jogadores.md` permanece como o único dashboard operacional dos jogadores.
4. Arquivos em `Workflow/` permanecem documentação técnica, não Home operacional.
5. `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` deve ser explicitamente tratado como documentação técnica.
6. `Workflow/Property Key Dashboard.md` deve ser revisado pelo Sage antes de qualquer arquivamento.
7. Dashboards dentro de `Workflow/Legacy/Disgraceland` permanecem apenas referência legada.

## Arquivos que devem continuar

- `Home.md`
- `Home_Mestre.md`
- `Home_Jogadores.md`
- `.obsidian/plugins/homepage/data.json`
- documentos de auditoria já commitados;
- documentos da camada de compatibilidade;
- documentos de workflow que são técnicos.

## Arquivos que devem virar ou permanecer documentação técnica

- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md`
- `Workflow/_audit/Omnisvera/OMNISVERA_DASHBOARD_MAP_SYSTEMS.md`
- `Workflow/COMPATIBILITY_LAYER/DASHBOARD_COMPATIBILITY_RULES.md`
- `Workflow/Legacy/Disgraceland/_audit/templates/HOME_DASHBOARD_TEMPLATE_CONTRACT.md`
- todos os `*_INDEX.md` em `Workflow/_audit`, `Workflow/RPG_SYSTEM_DESIGN`, `Workflow/COMPATIBILITY_LAYER` e `Workflow/Legacy`.

## Arquivos que precisam decisão do Sage

- `Workflow/Property Key Dashboard.md`
- `Workflow/Reports/latest_vault_audit.md`
- qualquer dashboard antigo fora de `Home.md`, `Home_Mestre.md`, `Home_Jogadores.md` e fora do Legacy.

## Próxima etapa sugerida

Se a consolidação for aprovada:

1. Não alterar plugin Homepage, porque ele já aponta para `Home.md`.
2. Manter `Home.md` como portal simples.
3. Garantir que nenhum outro arquivo em `Workflow/` seja chamado de Home operacional.
4. Opcionalmente adicionar nota de cabeçalho em `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md`: “documentação técnica, não dashboard operacional”.
5. Revisar `Workflow/Property Key Dashboard.md` e decidir se deve ir para `Workflow/_archive/obsolete_review` em etapa futura.

## Conclusão

A estrutura atual está próxima do desejado: há uma Home dos jogadores e uma Home do mestre. O único ponto a manter claro é que `Home.md` não deve ser tratado como terceiro dashboard operacional; ele é apenas portal/entrada do plugin Homepage.
