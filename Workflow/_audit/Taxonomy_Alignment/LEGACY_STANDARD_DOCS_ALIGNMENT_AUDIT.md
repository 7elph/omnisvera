# Auditoria de Alinhamento dos Documentos Antigos com a Taxonomia

Data: 2026-06-27

Fonte da verdade:

- `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md`
- `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md`

## Objetivo

Identificar documentos antigos de padrão, planejamento, compatibilidade e templates que ainda poderiam contradizer a taxonomia oficial atual do Sage.

## Termos auditados

Campos rejeitados/problemáticos:

- `sessions`;
- `player_known`;
- `subtype`;
- `portrait`;
- `token_image`;
- `map_image`;
- `handout_image`;
- `life_status`;
- `old_dragon_class`;
- `old_dragon_race`;
- `requires_review`;
- `work_status`;
- `canon_status`;
- `source`;
- `state`.

Termos operacionais antigos:

- `Home_Jogadores`;
- `portal neutro`;
- `loyalist`;
- `rancher`;
- `pirate`;
- `widow`;
- `steeltown`;
- `water`;
- `individual`;
- `religion`;
- `territory`.

Observação: `religion` e `territory` também são campos herdados preservados. Ocorrências como campos YAML não são erro.

## Classificação dos grupos encontrados

| grupo/arquivo | termos encontrados | conflito | recomendação | risco | ação proposta |
|---|---|---|---|---|---|
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | campos rejeitados, pasta `Classes`, consultas antigas | Sim | `ATUALIZAR_AGORA` | Alto: orientava dashboards com schema rejeitado. | Reescrito conforme taxonomia. |
| `Workflow/OMNISVERA_CLASS_STANDARD.md` | campos rejeitados, pasta `Classes`, consulta por campos antigos | Sim | `ATUALIZAR_AGORA` | Alto: orientava classes com padrão rejeitado. | Reescrito conforme taxonomia. |
| `Workflow/OMNISVERA_NOTE_STANDARD.md` | campos rejeitados | Sim | `ATUALIZAR_AGORA` | Alto: padrão geral antigo. | Reescrito conforme taxonomia. |
| `Workflow/OMNISVERA_MEDIA_STANDARD.md` | campos de mídia rejeitados como padrão novo | Sim | `ATUALIZAR_AGORA` | Médio: poderia reintroduzir campos fora da taxonomia. | Reescrito com `thumbnail` e `cover` como campos ativos. |
| `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` | schema antigo com campos rejeitados | Sim | `ATUALIZAR_AGORA` | Alto: era fonte de schema. | Reescrito conforme taxonomia. |
| `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md` | campos de personagem rejeitados | Sim | `ATUALIZAR_AGORA` | Alto: orientava templates novos. | Reescrito conforme taxonomia. |
| `Templates/` | `territory`, `religion` como campos herdados | Não | `MANTER` | Baixo. | Nenhuma alteração necessária nesta etapa. |
| `Workflow/COMPATIBILITY_LAYER/*` | decisões antigas aprovadas antes da taxonomia atual | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio: pode confundir IA. | Aviso histórico adicionado. |
| `Workflow/RPG_SYSTEM_DESIGN/*` | modelo RPG anterior com campos agora rejeitados | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio: útil como histórico, perigoso como padrão. | Aviso histórico adicionado. |
| `Workflow/_audit/Decision_Packet/*` | decisões anteriores, algumas substituídas | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio. | Aviso histórico adicionado. |
| `Workflow/_audit/Comparison/*` | comparação antiga pré-taxonomia final | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio. | Aviso histórico adicionado. |
| `Workflow/CHARACTER_SCHEMA.md` | schema anterior | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio. | Aviso histórico adicionado. |
| `Workflow/AI_CONTEXT/05_FRONTMATTER_SCHEMA.md` | schema anterior | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio. | Aviso histórico adicionado. |
| `Workflow/Templates/Character Template.md` | template antigo | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio. | Aviso histórico adicionado. |
| `Workflow/Templates/Player Character Template.md` | template antigo | Sim como fonte atual | `MARCAR_COMO_LEGADO` | Médio. | Aviso histórico adicionado. |
| `Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md` | `Home_Jogadores`, campos antigos | Não operacional | `MANTER_COMO_HISTORICO` | Baixo. | Não alterar. |
| `Workflow/_audit/Omnisvera/*` | auditoria de estado anterior | Histórico | `MANTER_COMO_HISTORICO` | Baixo. | Não alterar. |
| `Workflow/Reports/latest_vault_audit.md` | relatório gerado com links legados | Histórico | `MANTER_COMO_HISTORICO` | Baixo. | Não alterar. |

## Resultado

Os documentos ativos `Workflow/OMNISVERA_*.md` foram alinhados ou mantidos como fonte da verdade.

Documentos históricos foram marcados com aviso para não serem usados como fonte principal.

Templates ativos não exigiram alteração nesta etapa.
