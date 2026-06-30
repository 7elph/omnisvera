---
obsidianUIMode: preview
NoteIcon: workflow
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
status: Concluído
tags:
  - workflow
  - audit
  - dashboard
  - padronizacao
---

# Relatório — Home do Mestre e Estado da Campanha

## Objetivo

Reduzir a duplicidade entre `Home_Mestre.md` e `CAMPANHA/ESTADO_DA_CAMPANHA.md`.

A separação oficial ficou:

| Arquivo | Função |
|---|---|
| `Home_Mestre.md` | Navegação visual do mestre: mapas, cards, índices e atalhos. |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | Caderno operacional do mestre: preparação, segredos, bastidores, consequências e decisões de sessão. |

## Ajustes aplicados

| Arquivo | Ajuste |
|---|---|
| `Home_Mestre.md` | Painel inicial renomeado para navegação do mestre, com links diretos para seções úteis do Estado da Campanha. |
| `Home_Mestre.md` | Bloco “Fios da Campanha” deixou de repetir preparação e passou a apontar para o Estado da Campanha. |
| `Home_Mestre.md` | Relatórios técnicos foram recolhidos em seção própria de documentação técnica. |
| `Home_Mestre.md` | Modificados recentemente agora fica recolhido para não dominar a página visual. |
| `Home_Mestre.md` | Consulta de raças usa `FROM "Races"` em vez de `#race`. |
| `Home.md` | Consultas públicas de facções e crônicas usam pastas operacionais (`Factions` e `EARTHROPO`) em vez de tags amplas. |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | Nota passou a declarar que é o caderno operacional e que a Home do Mestre é a navegação visual. |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | Consultas de personagens, facções e itens passaram a consultar pastas operacionais. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | Documentada a separação entre Home visual e Estado operacional. |

## Regra operacional

- Durante sessão, abrir `Home_Mestre.md` para navegar rápido.
- Para preparação, segredos, consequências e controle real da mesa, abrir `CAMPANHA/ESTADO_DA_CAMPANHA.md`.
- A Home do Mestre não deve virar um segundo Estado da Campanha.
- O Estado da Campanha não precisa virar vitrine visual.

## Consultas revisadas

| Consulta | Antes | Depois |
|---|---|---|
| Raças na Home do Mestre | `FROM #race` | `FROM "Races"` |
| Personagens em foco | `FROM #personagem` | `FROM "Characters/Individual"` |
| Facções em movimento | `FROM #faccao OR #faction` | `FROM "Factions"` |
| Itens revelados | `FROM #item OR #artefato` | `FROM "Items"` com filtro por tag de item/artefato |
| Facções públicas | `FROM #faction` | `FROM "Factions"` |
| Crônicas públicas | `FROM #story` | `FROM "EARTHROPO"` |

## Resultado

Classificação: `READY_FOR_NEXT_STANDARDIZATION_STEP`

`Home_Mestre.md` e `CAMPANHA/ESTADO_DA_CAMPANHA.md` agora têm funções distintas, reduzindo duplicidade e risco de ruído durante a mesa.

## Validação executada

Comandos executados:

```powershell
python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
```

Resultados:

| Validação | Resultado |
|---|---|
| Frontmatter | 130 notas analisadas, 0 inválidas |
| Wikilinks | 1277 links encontrados, 1277 resolvidos, 0 quebrados |
| Mídia ativa | 223 referências válidas, 0 quebradas |
| Imagens órfãs | 38 imagens órfãs ainda pendentes para revisão futura |

Busca operacional:

- `Home.md`, `Home_Mestre.md` e `CAMPANHA/ESTADO_DA_CAMPANHA.md` não usam mais consultas operacionais amplas como `FROM #race`, `FROM #personagem`, `FROM #faccao`, `FROM #faction`, `FROM #item`, `FROM #artefato` ou `FROM #story`.
- Menções a `Home_Jogadores.md` permanecem apenas como documentação histórica de que o arquivo não existe mais na raiz.
