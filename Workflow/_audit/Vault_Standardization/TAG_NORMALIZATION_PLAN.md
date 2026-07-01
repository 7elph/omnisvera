# Omnisvera — Plano Dry-Run de Normalizacao de Tags

Gerado em: 2026-07-01 04:36

> [!IMPORTANT]
> Este plano nao alterou nenhuma nota.
> A estrategia segura e adicionar tags oficiais e preservar tags legacy/hibridas.

## Resumo

| metrica | valor |
|---|---:|
| notas analisadas | 330 |
| notas candidatas | 2 |
| baixo risco | 2 |
| medio risco | 0 |
| alto risco | 0 |

## Baixo risco

Casos simples como `local` -> adicionar `location`, `faccao` -> adicionar `faction`, `raca` -> adicionar `race`.

| Arquivo | Tags atuais relevantes | Tags oficiais a adicionar | Tags preservadas | Risco | Observacao |
|---|---|---|---|---|---|
| `Factions/Culto dos Sussurrantes.md` | `antagonista` | `character` | `antagonista` | low | Adicionar `character` preservando `antagonista`. |
| `Workflow/_audit/Class_Rules_Standardization/RULES_FOLDER_CONSOLIDATION_REPORT.md` | `raca` | `race` | `raca` | low | Adicionar `race` preservando `raca`. |

## Medio risco

Casos que envolvem `Category/*`, `settlement` ou interpretacao de tipo real da nota.

- Nenhum caso identificado.

## Alto risco

Reservado para casos que afetem diretamente Dataview/DataCards/Home ou tags de semantica ambigua severa.

- Nenhum caso identificado.

## Tags preservadas sem migracao automatica

- `story`: manter como eixo narrativo/capitulo por enquanto.
- `bside`: manter como tag narrativa especial.
- `old-dragon`: manter como tag de sistema/campanha.
- `Category/*`: preservar ate revisar consultas Dataview/DataCards.

## Proxima etapa recomendada

Revisar este plano com o Sage e aplicar apenas os casos de baixo risco em uma Fase B2,
com commit proprio e validacao de Dataview/DataCards depois.
