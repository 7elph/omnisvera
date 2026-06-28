# Auditoria de Newlines e Frontmatter Operacional

Data: 2026-06-27

## Objetivo

Verificar se arquivos operacionais críticos estavam colapsados em poucas linhas ou com frontmatter inválido após visualização pelo raw do GitHub.

## Critérios

Cada arquivo foi verificado para:

- quantidade de linhas;
- primeira linha `---` em linha própria;
- fechamento de frontmatter em linha própria;
- corpo Markdown com headings em linhas reais;
- blocos Dataview/Datacards em linhas reais;
- tabelas Markdown em linhas próprias;
- listas YAML em linhas próprias.

## Resultado antes

| arquivo | linhas | classificação |
|---|---:|---|
| `Home.md` | 109 | `OK` |
| `Home_Mestre.md` | 205 | `OK` |
| `CULTURE.md` | 190 | `OK` |
| `Religion/RELIGION.md` | 41 | `OK` |
| `CALENDAR.md` | 224 | `OK` |
| `TIMELINE.md` | 69 | `OK` |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | 88 | `OK` |
| `Templates/RPG/Story.md` | 68 | `OK` |
| `Workflow/OMNISVERA_TAG_BRIDGE_GUIDE.md` | 48 | `OK` |
| `Workflow/OMNISVERA_VISIBILITY_AND_SPOILER_GUIDE.md` | 50 | `OK` |
| `Workflow/OMNISVERA_LOCATION_TERRITORY_GUIDE.md` | 32 | `OK` |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md` | 176 | `OK` |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md` | 101 | `OK` |

## Correções aplicadas

Nenhuma correção mecânica de newline/frontmatter foi necessária. Os arquivos estavam com quebras reais no workspace local.

## Resultado depois

| arquivo | linhas depois | classificação |
|---|---:|---|
| `Home.md` | 109 | `OK` |
| `Home_Mestre.md` | 205 | `OK` |
| `CULTURE.md` | 100 | `OK` |
| `Religion/RELIGION.md` | 57 | `OK` |
| `CALENDAR.md` | 111 | `OK` |
| `TIMELINE.md` | 75 | `OK` |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | 88 | `OK` |
| `Templates/RPG/Story.md` | 68 | `OK` |
| `Workflow/OMNISVERA_TAG_BRIDGE_GUIDE.md` | 48 | `OK` |
| `Workflow/OMNISVERA_VISIBILITY_AND_SPOILER_GUIDE.md` | 50 | `OK` |
| `Workflow/OMNISVERA_LOCATION_TERRITORY_GUIDE.md` | 32 | `OK` |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md` | 176 | `OK` |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md` | 101 | `OK` |

A reestruturação de `CULTURE.md`, `Religion/RELIGION.md`, `CALENDAR.md` e `TIMELINE.md` foi tratada em relatório próprio porque é ajuste de conteúdo operacional, não correção de newline.

## Observação

As diferenças observadas no raw do GitHub parecem ser efeito de renderização/visualização, não colapso real dos arquivos locais.
