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
  - padronizacao
  - story
---

# Relatório — Padronização de Earthropo, Story e B-Sides

## Objetivo

Padronizar a camada narrativa ativa da pasta `EARTHROPO`, separando com clareza:

- capítulos numerados públicos/jogáveis;
- B-Sides de origem dos personagens;
- índice narrativo de Earthropo;
- consultas de Dataview/DataCards que não devem puxar Workflow, templates ou relatórios.

## Decisões aplicadas

| Área | Decisão |
|---|---|
| Capítulos numerados | Continuam usando `story`, `chapter` e tags como `chapter01`. |
| B-Sides | Continuam usando `story`, `bside`, `origin-story` e tags como `origin-vezemir`. |
| `sessions` | Não foi criado nem usado. |
| Conteúdo público | Fica na nota do capítulo, como `EARTHROPO/01 - Ecos do Mundo Perdido.md`. |
| Conteúdo do mestre | Fica em `CAMPANHA/ESTADO_DA_CAMPANHA.md` e nos B-Sides privados. |
| Consultas | Devem consultar pastas operacionais e tags específicas, não tags amplas. |

## Arquivos ajustados

| Arquivo | Ajuste |
|---|---|
| `EARTHROPO/EARTHROPO.md` | Índice de Earthropo passou a filtrar B-Sides por pasta/tag específica e capítulos públicos por visibilidade. |
| `EARTHROPO/01 - Ecos do Mundo Perdido.md` | Adicionado `chapter_tag: chapter01`; consulta de elenco principal passou a filtrar visibilidade pública/jogadores. |
| `EARTHROPO/00 - O Bastardo de Ferro.md` | Adicionado `origin_tag: origin-vezemir`; consulta deixou de depender de tags amplas. |
| `EARTHROPO/00 - O Corvo da Maré Baixa.md` | Adicionado `origin_tag: origin-varkh`; consulta deixou de depender de tags amplas. |
| `EARTHROPO/00 - As Crônicas de Névoa de Sangue.md` | Adicionado `origin_tag: origin-raziel`; consulta deixou de depender de nomes fixos e tags legadas. |
| `Templates/RPG/Story.md` | Adicionado `chapter_tag`; consultas públicas passam a filtrar `visibility` e `gm_secret`. |
| `Templates/RPG/B-Side.md` | Adicionado `origin_tag`; consulta de personagens passa a usar `chapters` ou `origin_tag`. |
| `Home_Mestre.md` | Consulta de crônicas passa a usar `FROM "EARTHROPO"` para evitar puxar Workflow ou relatórios por tag. |

## Padrão operacional de capítulo numerado

Capítulos numerados são notas públicas/jogáveis e devem evitar segredos pesados.

Campos esperados:

```yaml
type: story
visibility: Jogadores
spoiler_level: light
gm_secret: false
chapter: 01 - Nome do Capítulo
chapter_tag: chapter01
chapters:
  - 01 - Nome do Capítulo
tags:
  - story
  - chapter
  - chapter01
```

Consulta segura para elenco:

```dataview
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE (
  contains(chapters, this.chapter)
  OR contains(tags, this.chapter_tag)
)
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT file.name ASC
```

## Padrão operacional de B-Side

B-Sides são histórias de origem de personagens e podem conter informação privada ou sensível.

Campos esperados:

```yaml
type: story
visibility: Mestre
spoiler_level: medium
gm_secret: true
chapter: 00 - Nome da Origem
origin_tag: origin-personagem
chapters:
  - 00 - Nome da Origem
tags:
  - story
  - bside
  - origin-story
  - origin-personagem
```

Consulta segura para personagens ligados:

```dataview
TABLE thumbnail, location, status
FROM "Characters/Individual"
WHERE contains(chapters, this.chapter)
OR contains(tags, this.origin_tag)
SORT file.name ASC
```

## Verificações de vazamento

- B-Sides não aparecem na seção de capítulos numerados de `EARTHROPO.md`.
- Capítulo público filtra personagens por `visibility: Jogadores` ou `visibility: Público`.
- Templates não usam `sessions`.
- Templates não usam `player_known`, `life_status` ou `handout_image`.
- Consultas deixaram de depender de tags amplas como `personagem`, `vezemir` ou `varkh`.

## Pendências

| Pendência | Status |
|---|---|
| Decidir se B-Sides manterão prefixo `00 -` ou serão renomeados futuramente para `B-Side - ...` | Precisa do Sage |
| Decidir se Home dos Jogadores mostra capítulos em preparação ou apenas capítulos já jogados | Precisa do Sage |
| Revisar visualmente DataCards no Obsidian após esta etapa | Recomendado |
| Separar ainda mais a Home do Mestre do Estado da Campanha ou fundir os dois fluxos | Precisa do Sage |

## Resultado

Classificação: `READY_FOR_NEXT_STANDARDIZATION_STEP`

O bloco `EARTHROPO / Story / B-Sides` está padronizado o suficiente para seguir a fila do vault sem iniciar migração em massa.

## Validação executada

Comandos executados após os ajustes:

```powershell
python .local-tools/validate_frontmatter.py . --ignore-legacy
python .local-tools/validate_links.py . --ignore-legacy
python .local-tools/validate_media.py . --ignore-legacy
```

Resultados:

| Validação | Resultado |
|---|---|
| Frontmatter | 130 notas analisadas, 0 inválidas |
| Wikilinks | 1275 links encontrados, 1275 resolvidos, 0 quebrados |
| Mídia ativa | 223 referências válidas, 0 quebradas |
| Imagens órfãs | 38 imagens órfãs ainda pendentes para revisão futura |

Busca operacional:

- não foram encontrados usos ativos de `sessions`, `player_known`, `life_status`, `handout_image` ou `#session` em `EARTHROPO`, `Templates`, `Home`, `Home_Mestre` e `CAMPANHA`;
- não foram encontrados usos ativos de `Home_Jogadores`, `TRIBUCIA` ou `Workflow/Legacy/Disgraceland` nessas áreas;
- consultas de B-Side deixaram de depender de tags amplas como `personagem`, `vezemir` e `varkh`.
