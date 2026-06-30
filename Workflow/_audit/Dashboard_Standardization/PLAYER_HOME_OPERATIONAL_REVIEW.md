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

# Relatório — Home dos Jogadores

## Objetivo

Revisar `Home.md` para funcionar como a Home pública dos jogadores, com navegação visual, consultas seguras e sem links para bastidores técnicos ou conteúdo de mestre.

## Regra aplicada

`Home.md` deve mostrar apenas conteúdo:

- `visibility: Jogadores` ou `visibility: Público`;
- `gm_secret != true`;
- `spoiler_level` diferente de `medium` e `heavy`;
- localizado em pastas operacionais do vault.

## Ajustes aplicados

| Área | Ajuste |
|---|---|
| Cabeçalho | Adicionado logo visual de Omnisvera. |
| Navegação | Criados cards para mapas, crônicas e calendário. |
| Link do mestre | Removido link direto para `Home_Mestre.md`. |
| Capítulo em foco | Consulta por `EARTHROPO`, excluindo B-Sides e origens privadas. |
| Personagens | Consulta por `Characters/Individual`, apenas jogadores liberados. |
| Quests | Consulta por `CAMPANHA/Quests`, apenas quests liberadas. |
| Rumores | Consulta por `CAMPANHA/Rumors`, apenas rumores liberados. |
| Territórios | Consulta por `Territories`, com filtros de visibilidade. |
| Locais | Consulta por `Locations`, com filtros de visibilidade. |
| Facções | Consulta por `Factions`, com filtros de visibilidade. |
| Segurança | B-Sides, segredos de origem, Workflow e relatórios técnicos não aparecem na Home pública. |

## Consultas públicas usadas

As consultas da Home dos jogadores agora preferem pastas operacionais:

| Tipo | Fonte |
|---|---|
| Capítulos | `FROM "EARTHROPO"` |
| Personagens dos jogadores | `FROM "Characters/Individual"` |
| Quests | `FROM "CAMPANHA/Quests"` |
| Rumores | `FROM "CAMPANHA/Rumors"` |
| Territórios | `FROM "Territories"` |
| Locais | `FROM "Locations"` |
| Facções | `FROM "Factions"` |

## Itens propositalmente fora da Home pública

- `Home_Mestre.md`;
- `CAMPANHA/ESTADO_DA_CAMPANHA.md`;
- `Workflow/`;
- relatórios técnicos;
- B-Sides de origem;
- notas com `visibility: Mestre`;
- notas com `gm_secret: true`;
- notas com `spoiler_level: medium` ou `spoiler_level: heavy`.

## Resultado

Classificação: `READY_FOR_NEXT_STANDARDIZATION_STEP`

`Home.md` está alinhada como entrada pública dos jogadores e separada da Home visual do mestre e do Estado da Campanha.

## Validação executada

Comandos executados:

```powershell
rg -n "Home_Mestre|CAMPANHA/ESTADO_DA_CAMPANHA|Workflow/|Workflow\\|Disgraceland|TRIBUCIA|Home_Jogadores|gm_secret: true|visibility: Mestre|spoiler_level: medium|spoiler_level: heavy|FROM #|#session|sessions|player_known|life_status|handout_image" Home.md
python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
```

Resultados:

| Validação | Resultado |
|---|---|
| Busca de vazamento em `Home.md` | Sem ocorrências |
| Frontmatter | 130 notas analisadas, 0 inválidas |
| Wikilinks | 1273 links encontrados, 1273 resolvidos, 0 quebrados |
| Mídia ativa | 228 referências válidas, 0 quebradas |
| Imagens órfãs | 38 imagens órfãs ainda pendentes para revisão futura |
