# Auditoria de Faxina do Workflow

Data: 2026-06-27

## Objetivo

Classificar a pasta `Workflow/` para reduzir ambiguidade entre documentos ativos, relatórios históricos, auditorias e legado.

## Classificação geral

| caminho | classificação | ação |
|---|---|---|
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md` | `ACTIVE_TAXONOMY` | Manter como fonte da verdade. |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md` | `ACTIVE_TAXONOMY` | Manter como fonte da verdade. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | `ACTIVE_STANDARD` | Manter como guia ativo. |
| `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` | `ACTIVE_STANDARD` | Manter como guia ativo. |
| `Workflow/OMNISVERA_NOTE_STANDARD.md` | `ACTIVE_STANDARD` | Manter como guia ativo. |
| `Workflow/OMNISVERA_MEDIA_STANDARD.md` | `ACTIVE_STANDARD` | Manter como guia ativo. |
| `Workflow/OMNISVERA_VISIBILITY_AND_SPOILER_GUIDE.md` | `ACTIVE_GUIDE` | Manter como guia ativo. |
| `Workflow/OMNISVERA_LOCATION_TERRITORY_GUIDE.md` | `ACTIVE_GUIDE` | Manter como guia ativo. |
| `Workflow/OMNISVERA_TAG_BRIDGE_GUIDE.md` | `ACTIVE_GUIDE` | Manter como guia ativo. |
| `Workflow/LOCAL_TOOLING.md` | `ACTIVE_TOOLING` | Manter e atualizar. |
| `Workflow/LOCAL_ASSISTANT_PROTOCOL.md` | `ACTIVE_TOOLING` | Manter. |
| `Workflow/DEVIN_OPERATING_PROTOCOL.md` | `ACTIVE_TOOLING` | Manter. |
| `Workflow/CANON.md` | `ACTIVE_GUIDE` | Manter; pode precisar revisão posterior sobre Disgraceland como template. |
| `Workflow/GEOGRAPHY.md` | `ACTIVE_GUIDE` | Manter. |
| `Workflow/RULES_SOURCES.md` | `ACTIVE_GUIDE` | Manter. |
| `Workflow/MISSING_NOTES_BACKLOG.md` | `ACTIVE_REPORT` | Manter. |
| `Workflow/AI_CONTEXT/` | `ACTIVE_TOOLING` | Manter como contexto para IA. |
| `Workflow/_audit/Post_Pilot_Fixes/` | `ACTIVE_REPORT` | Manter como auditoria recente. |
| `Workflow/_audit/Pilot_Migration/` | `ACTIVE_REPORT` | Manter como auditoria recente. |
| `Workflow/_audit/Operational_Cleanup/` | `ACTIVE_REPORT` | Manter como auditoria atual. |
| `Workflow/COMPATIBILITY_LAYER/` | `HISTORICAL_REPORT` | Manter como histórico por enquanto. |
| `Workflow/RPG_SYSTEM_DESIGN/` | `HISTORICAL_REPORT` | Manter como histórico por enquanto. |
| `Workflow/_audit/Comparison/` | `HISTORICAL_REPORT` | Manter como histórico por enquanto. |
| `Workflow/_audit/Decision_Packet/` | `HISTORICAL_REPORT` | Manter como histórico por enquanto. |
| `Workflow/_audit/Omnisvera/` | `HISTORICAL_REPORT` | Manter como base de auditoria. |
| `Workflow/Reports/` | `ACTIVE_REPORT` | Manter; revisar tamanho depois. |
| `Workflow/Templates/` | `LEGACY_REFERENCE` | Manter por enquanto; avaliar em lote próprio. |
| `Workflow/Legacy/Old Dragon anterior/` | `LEGACY_REFERENCE` | Manter; não contém Disgraceland. |
| `Workflow/Legacy/Disgraceland/` | `DELETE_CANDIDATE` | Remover se auditoria de dependência confirmar ausência de bloqueador operacional. |

## Decisão desta etapa

Não mover documentos ativos nem relatórios históricos amplos nesta etapa. A organização principal será feita por `Workflow/README.md`.

## Pendências

- Revisar documentos antigos que ainda dizem que Disgraceland é fonte de template.
- Avaliar se `Workflow/COMPATIBILITY_LAYER/` e `Workflow/RPG_SYSTEM_DESIGN/` devem ir para archive em etapa posterior.
- Avaliar se scripts `audit_format.py` e `audit_runtime.py` ainda são usados.
