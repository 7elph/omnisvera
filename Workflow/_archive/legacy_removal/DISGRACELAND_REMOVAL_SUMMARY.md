# Disgraceland Removal Summary

Status: resumo permanente da remoção física controlada.

Data: 2026-06-27.

## O que foi removido

Foi removido o diretório:

```text
Workflow/Legacy/Disgraceland/
```

Esse diretório continha o vault legado de Disgraceland usado como fonte técnica durante a reconstrução do motor Omnisvera.

## Por que foi removido

Disgraceland deixou de ser conteúdo operacional do Omnisvera.

A parte funcional relevante já foi extraída para:

- taxonomia Omnisvera;
- templates RPG;
- guias de mesa;
- regras de tags;
- padrões de Dataview/DataCards;
- documentação de dashboard;
- relatórios de auditoria.

Manter a pasta física dentro do vault aumentava ruído em buscas, DataCards, auditorias e navegação do Obsidian.

## Histórico preservado

O conteúdo técnico de Disgraceland permanece recuperável pelo histórico Git e pelos commits/documentos já criados:

- `e348885` — `docs: audit Disgraceland Obsidian system`;
- `cb0de8d` — `docs: define Disgraceland technical contracts`;
- `bbebdda` — `docs: define Disgraceland template contracts`;
- `Workflow/Legacy/Disgraceland/_audit`, preservado nesses commits anteriores;
- `Workflow/_audit/Disgraceland_Removal/DISGRACELAND_OPERATIONAL_REMOVAL_PLAN.md`;
- `Workflow/_audit/Operational_Cleanup/DISGRACELAND_PHYSICAL_REMOVAL_AUDIT.md`.

## Partes funcionais reaproveitadas

- lógica de dashboard/Home;
- uso de frontmatter visual;
- uso de `thumbnail` e `cover`;
- consultas Dataview/DataCards;
- Supercharged Links;
- tags visuais;
- padrões de templates;
- estrutura de auditoria técnica;
- separação entre conteúdo operacional e histórico.

## Fonte atual da verdade

A fonte atual da verdade é:

- `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md`;
- `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md`;
- `Workflow/README.md`.

## Regra futura

Não reintroduzir notas, tags, facções, nomes ou mapas de Disgraceland como conteúdo operacional de Omnisvera sem uma decisão explícita do Sage.
