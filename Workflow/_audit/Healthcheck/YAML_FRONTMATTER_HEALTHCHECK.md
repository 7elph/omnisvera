# YAML Frontmatter Healthcheck

Data: 2026-06-27

Objetivo: verificar a saúde mecânica do frontmatter/YAML antes de qualquer migração em massa por templates.

## Escopo auditado

Pastas/áreas verificadas:

- raiz do vault;
- `Characters`;
- `Factions`;
- `Territories`;
- `Locations`;
- `Lore`;
- `Religion`;
- `Templates`;
- `Workflow`, excluindo auditorias legadas grandes e relatórios já commitados quando não faziam parte do vault operacional.

Exclusões técnicas:

- `.git`;
- `node_modules`;
- `.codex-tools`;
- `.omnisvera-tools`;
- `.tmp_refs`;
- `zz_media`;
- `Workflow/Legacy/Disgraceland`;
- `Workflow/_audit`;
- `Workflow/RPG_SYSTEM_DESIGN`.

## Método

PyYAML não estava disponível no ambiente, então foi usada checagem heurística conservadora:

- delimitador inicial `---`;
- delimitador final `---`;
- frontmatter inline;
- frontmatter sem fechamento;
- tabs no frontmatter;
- campos duplicados;
- campos possivelmente colapsados;
- formato de `tags`;
- formato de `chapters`;
- formato de `cssclasses`.

Nenhuma correção automática foi aplicada nesta etapa.

## Resumo

| classificação | quantidade |
| --- | ---: |
| `OK` | 94 |
| `NO_FRONTMATTER` | 26 |
| `NEEDS_REVIEW` | 2 |
| `BROKEN_FRONTMATTER` | 0 |
| `INLINE_FRONTMATTER` | 0 |
| `MISSING_CLOSING_DELIMITER` | 0 |
| `YAML_PARSE_ERROR` | 0 |
| total auditado | 122 |

## Arquivos com revisão necessária

| arquivo | classificação | problema | ação aplicada | recomendação |
| --- | --- | --- | --- | --- |
| `CULTURE.md` | `NEEDS_REVIEW` | `tags` está em formato escalar: `tags: home`. | Nenhuma. | Converter para lista em etapa controlada se o Sage aprovar. |
| `LATEST_NEWS.md` | `NEEDS_REVIEW` | `tags` está em formato escalar: `tags: home`. | Nenhuma. | Converter para lista em etapa controlada se o Sage aprovar. |

## Arquivos sem frontmatter

Classificação: `NO_FRONTMATTER`.

Esses arquivos são majoritariamente documentação técnica, contexto de IA, camada de compatibilidade ou arquivo histórico. Não foram tratados como erro.

| arquivo | observação |
| --- | --- |
| `Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md` | Arquivo histórico arquivado; frontmatter original foi preservado no corpo após aviso. |
| `Workflow/AI_CHANGELOG.md` | Documento técnico. |
| `Workflow/AI_CONTEXT/00_README_FOR_AI.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/01_CANON_SUMMARY.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/02_ENTITY_INDEX.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/03_OPEN_DECISIONS.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/04_MEDIA_RULES.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/05_FRONTMATTER_SCHEMA.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/06_TASK_TEMPLATES.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/07_VALIDATION_CHECKLIST.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/08_DO_NOT_INVENT.md` | Documento técnico/contextual. |
| `Workflow/AI_CONTEXT/09_SESSION_STATE.md` | Documento técnico/contextual. |
| `Workflow/AI_REVIEW_CHECKLIST.md` | Documento técnico. |
| `Workflow/AI_TASK_TEMPLATE.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/COMPATIBILITY_LAYER_INDEX.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/DASHBOARD_COMPATIBILITY_RULES.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/DATACARDS_COMPATIBILITY_RULES.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/DATAVIEW_COMPATIBILITY_RULES.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/FRONTMATTER_COMPATIBILITY_SCHEMA.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/MEDIA_FIELD_COMPATIBILITY_MODEL.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/PILOT_MIGRATION_PLAN.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/TAG_COMPATIBILITY_MAP.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/TEMPLATE_COMPATIBILITY_GUIDE.md` | Documento técnico. |
| `Workflow/COMPATIBILITY_LAYER/VISIBILITY_COMPATIBILITY_MODEL.md` | Documento técnico. |
| `Workflow/DEVIN_OPERATING_PROTOCOL.md` | Documento técnico. |
| `Workflow/Reports/latest_vault_audit.md` | Relatório técnico antigo. |

## Correções aplicadas

Nenhuma correção mecânica de frontmatter foi aplicada.

## Risco

Baixo para delimitadores e frontmatter quebrado: não foram encontrados casos de `INLINE_FRONTMATTER`, `MISSING_CLOSING_DELIMITER` ou `BROKEN_FRONTMATTER`.

Médio para consistência futura: `CULTURE.md` e `LATEST_NEWS.md` usam `tags` escalar; isso é provavelmente aceito pelo Obsidian, mas diverge do padrão de lista planejado para migração controlada.
