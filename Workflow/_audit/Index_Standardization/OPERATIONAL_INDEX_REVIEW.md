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
  - indice
  - padronizacao
---

# Relatório — Índices Operacionais

## Objetivo

Revisar os índices ativos do vault para que eles consultem pastas operacionais, não puxem `Workflow`, `Templates`, legado ou conteúdo privado por acidente, e deixem clara a separação entre visão dos jogadores e visão do mestre.

## Índices revisados

| Índice | Função | Ajuste aplicado |
|---|---|---|
| `Bestiary/INDICE_DE_MONSTROS.md` | Monstros e ameaças | Separado em monstros liberados e monstros do mestre; adicionado frontmatter visual. |
| `CAMPANHA/Quests/INDICE_DE_QUESTS.md` | Quests | Separado em quests liberadas e quests do mestre; adicionado frontmatter visual. |
| `CAMPANHA/Rumors/INDICE_DE_RUMORES.md` | Rumores | Separado em rumores liberados e rumores do mestre; adicionado frontmatter visual. |
| `Classes/INDICE_DE_CLASSES.md` | Classes | Adicionado filtro contra placeholders. |
| `Items/INDICE_DE_ITENS.md` | Itens | Itens dos jogadores agora filtram spoilers médios/pesados. |
| `Locations/INDICE_DE_LOCAIS.md` | Locais | Já estava alinhado com pasta operacional e filtros públicos/mestre. |
| `Races/INDICE_DE_RACAS.md` | Raças | Adicionado filtro contra placeholders. |
| `Rules/Spells/INDICE_DE_MAGIAS.md` | Magias | Separado em magias liberadas e magias do mestre; adicionado frontmatter visual. |
| `Territories/INDICE_DE_TERRITORIOS.md` | Territórios | Já estava alinhado com pasta operacional e filtros públicos/mestre. |

## Regras confirmadas

- Índices públicos usam `visibility`, `gm_secret` e `spoiler_level`.
- Índices de mestre podem mostrar conteúdo em revisão, mas continuam consultando pastas operacionais.
- Nenhum índice ativo deve consultar `Workflow/`, `Templates/` ou `Workflow/Legacy/`.
- Índices não devem puxar tags amplas se uma pasta operacional já existe.
- `Rules/Classes` e `Rules/Races` não devem ser recriados.

## Resultado

Classificação: `READY_FOR_NEXT_STANDARDIZATION_STEP`

Os índices operacionais estão alinhados o suficiente para continuarmos a fila de padronização sem risco alto de vazamento ou ruído por consulta ampla.

## Validação executada

Comandos executados:

```powershell
rg -n "FROM #|from #|Workflow/|Templates/|Workflow\\|Templates\\|Home_Jogadores|Disgraceland|TRIBUCIA|sessions|player_known|life_status|handout_image|#session" `
  Bestiary\INDICE_DE_MONSTROS.md `
  CAMPANHA\Quests\INDICE_DE_QUESTS.md `
  CAMPANHA\Rumors\INDICE_DE_RUMORES.md `
  Classes\INDICE_DE_CLASSES.md `
  Items\INDICE_DE_ITENS.md `
  Locations\INDICE_DE_LOCAIS.md `
  Races\INDICE_DE_RACAS.md `
  Rules\Spells\INDICE_DE_MAGIAS.md `
  Territories\INDICE_DE_TERRITORIOS.md

python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
```

Resultados:

| Validação | Resultado |
|---|---|
| Busca de padrões perigosos nos índices | Sem ocorrências |
| Frontmatter | 130 notas analisadas, 0 inválidas |
| Wikilinks | 1275 links encontrados, 1275 resolvidos, 0 quebrados |
| Mídia ativa | 228 referências válidas, 0 quebradas |
| Imagens órfãs | 38 ocorrências no validador; 8 arquivos reais em `zz_media` listados no relatório de limpeza |
