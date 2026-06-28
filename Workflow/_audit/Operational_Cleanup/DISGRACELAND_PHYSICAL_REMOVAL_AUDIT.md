# Disgraceland Physical Removal Audit

Status: aprovado para remoção física controlada em 2026-06-27.

## Objetivo

Verificar se `Workflow/Legacy/Disgraceland/` ainda é necessário como pasta física operacional dentro do vault Omnisvera.

## Resultado

Classificação final: `SAFE_TO_DELETE_WITH_LEGACY`.

Motivo: o conteúdo de Disgraceland já foi auditado, os contratos técnicos foram extraídos, a taxonomia Omnisvera foi definida, tags visuais principais foram migradas e as Homes/Templates operacionais não dependem mais da pasta física de Disgraceland.

## Arquivos encontrados

| caminho | quantidade |
|---|---:|
| `Workflow/Legacy/Disgraceland/` | 728 arquivos |

## Busca executada

Termos procurados:

- `Workflow/Legacy/Disgraceland`;
- `Disgraceland`;
- `TRIBUCIA`;
- `loyalist`;
- `rancher`;
- `pirate`;
- `widow`;
- `third`;
- `murray`;
- `steeltown`;
- `water`.

Escopo operacional verificado:

- `Home.md`;
- `Home_Mestre.md`;
- `Templates`;
- `Characters`;
- `Factions`;
- `Territories`;
- `Locations`;
- `Lore`;
- `Religion`;
- `Items`;
- `Bestiary`;
- `Rules`;
- `CAMPANHA`;
- documentos ativos `Workflow/OMNISVERA_*.md`;
- documentação de workflow fora de `Workflow/Legacy/Disgraceland`.

## Classificação das ocorrências restantes

| tipo | exemplos | classificação | ação |
|---|---|---|---|
| Documentação de contexto para IA | `Workflow/AI_CONTEXT/*`, `Workflow/ASSISTANT_HANDOFF.md` | `HISTORICAL_REFERENCE` | manter por enquanto |
| Regras antigas de compatibilidade | `Workflow/COMPATIBILITY_LAYER/*` | `HISTORICAL_REFERENCE` | manter como documentação histórica |
| Relatórios antigos | `Workflow/_audit/*`, `Workflow/Reports/latest_vault_audit.md` | `AUDIT_REFERENCE` | manter por rastreabilidade |
| Taxonomia atual | `Workflow/OMNISVERA_SYSTEM_TAXONOMY*.md`, `Workflow/OMNISVERA_TAG_BRIDGE_GUIDE.md` | `AUDIT_REFERENCE` / mapa de migração | manter |
| Índice de legado | `Workflow/Legacy/Legacy - Archive Index.md` | `LEGACY_REFERENCE` | atualizar para apontar para resumo de remoção |

## Bloqueadores operacionais

Nenhum bloqueador operacional identificado.

Não foram encontradas dependências ativas que exigissem manter a pasta física `Workflow/Legacy/Disgraceland/` para:

- Home dos Jogadores;
- Home do Mestre;
- templates ativos;
- notas canônicas;
- Dataview/DataCards operacionais;
- navegação principal.

## Ação recomendada

Remover fisicamente:

```text
Workflow/Legacy/Disgraceland/
```

Preservar antes da remoção:

```text
Workflow/_archive/legacy_removal/DISGRACELAND_REMOVAL_SUMMARY.md
```

Não remover:

```text
Workflow/Legacy/
Workflow/Legacy/Legacy - Archive Index.md
Workflow/Legacy/Old Dragon anterior/
```

## Observação

Essa remoção não apaga o histórico do Git. Os relatórios e contratos já commitados continuam servindo como referência técnica.
