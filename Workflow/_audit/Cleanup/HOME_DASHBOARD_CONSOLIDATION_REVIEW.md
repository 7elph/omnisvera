# Home Dashboard Consolidation Review

Data da revisão final: 2026-06-27

Objetivo: registrar a decisão final de consolidação das Homes do vault Omnisvera.

## Decisão final do Sage

O vault deve ter somente duas Homes operacionais:

| arquivo | função oficial | classificação |
| --- | --- | --- |
| `Home.md` | Home dos Jogadores e entrada do plugin Homepage. | `PLAYER_DASHBOARD` |
| `Home_Mestre.md` | Home/área operacional do mestre. | `MASTER_DASHBOARD` |

`Home_Jogadores.md` não deve existir na raiz como terceira Home operacional. Ele foi arquivado em:

```text
Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md
```

## Configuração do plugin Homepage

Arquivo lido:

```text
.obsidian/plugins/homepage/data.json
```

Configuração relevante:

| chave | valor |
| --- | --- |
| `value` | `Home` |
| `kind` | `File` |
| `openOnStartup` | `true` |
| `view` | `Reading view` |

Conclusão: o plugin Homepage continua apontando para `Home`, portanto `Home.md`. Isso está correto porque `Home.md` agora é a Home dos Jogadores.

## Classificação dos arquivos encontrados

| arquivo | função atual aparente | classificação | recomendação |
| --- | --- | --- | --- |
| `Home.md` | Home dos Jogadores. | `PLAYER_DASHBOARD` | Manter como Home principal aberta pelo plugin Homepage. |
| `Home_Mestre.md` | Área/dashboard do mestre. | `MASTER_DASHBOARD` | Manter como única Home operacional do mestre. |
| `Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md` | Cópia histórica da antiga Home dos Jogadores. | `LEGACY_DASHBOARD` | Manter apenas como histórico de migração; não usar operacionalmente. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | Documentação técnica do sistema de dashboards. | `TECHNICAL_DOC` | Manter como documentação, não Home operacional. |
| `Workflow/_audit/Omnisvera/OMNISVERA_DASHBOARD_MAP_SYSTEMS.md` | Auditoria técnica. | `TECHNICAL_DOC` | Manter como relatório. |
| `Workflow/COMPATIBILITY_LAYER/DASHBOARD_COMPATIBILITY_RULES.md` | Regras técnicas de compatibilidade. | `TECHNICAL_DOC` | Manter como documentação. |
| `Workflow/Legacy/Disgraceland/Home.md` | Home do vault legado Disgraceland. | `LEGACY_DASHBOARD` | Preservar como legado técnico. |
| `Workflow/Legacy/Disgraceland/Workflow/Property Key Dashboard.md` | Dashboard legado de propriedades. | `LEGACY_DASHBOARD` | Preservar no legado. |
| `Workflow/Property Key Dashboard.md` | Dashboard antigo de propriedades no Workflow ativo. | `NEEDS_SAGE_REVIEW` | Revisar futuramente; não é Home operacional. |
| `Classes/Homem de Armas.md` | Nota de classe; falso positivo por “Homem”. | `NEEDS_SAGE_REVIEW` | Não tratar como Home/dashboard. |
| `Workflow/Legacy/Old Dragon anterior/Legacy - Old Dragon anterior - Homem de Armas.md` | Nota legada de classe; falso positivo por “Homem”. | `NEEDS_SAGE_REVIEW` | Não tratar como Home/dashboard. |

## Links operacionais finais

| origem | destino | observação |
| --- | --- | --- |
| `Home.md` | `[[Home_Mestre]]` | Link opcional com aviso de área do mestre/spoiler. |
| `Home_Mestre.md` | `[[Home]]` | Link para a visão segura dos jogadores. |

Não deve haver links operacionais para `Home_Jogadores`.

## Arquivos que continuam

- `Home.md`
- `Home_Mestre.md`
- `.obsidian/plugins/homepage/data.json`
- documentação técnica em `Workflow/`
- auditorias em `Workflow/_audit`
- camada de compatibilidade em `Workflow/COMPATIBILITY_LAYER`
- legado preservado em `Workflow/Legacy/Disgraceland`

## Arquivos que não são Home operacional

- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md`
- `Workflow/_audit/Omnisvera/OMNISVERA_DASHBOARD_MAP_SYSTEMS.md`
- `Workflow/COMPATIBILITY_LAYER/DASHBOARD_COMPATIBILITY_RULES.md`
- `Workflow/Legacy/Disgraceland/_audit/templates/HOME_DASHBOARD_TEMPLATE_CONTRACT.md`
- qualquer `*_INDEX.md` dentro de auditorias/modelos/workflow

## Recomendações de manutenção

1. Não recriar `Home_Jogadores.md` na raiz.
2. Não transformar `Home.md` em portal intermediário.
3. Manter o plugin Homepage apontando para `Home`.
4. Manter `Home.md` conservadora, com filtros de visibilidade.
5. Manter conteúdo técnico, Workflow, Legacy e auditorias fora da Home dos Jogadores.
6. Usar `Home_Mestre.md` para preparação, relatórios técnicos, auditorias e conteúdo secreto.

## Conclusão

A arquitetura final fica:

```text
Home.md = jogadores
Home_Mestre.md = mestre
Home_Jogadores.md = arquivado, não operacional
```
