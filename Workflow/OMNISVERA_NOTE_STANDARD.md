# Omnisvera — Padrão Geral de Notas

> [!IMPORTANT]
> Este documento segue a taxonomia oficial atual do Sage.
> Fonte da verdade: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].

## Função

Define o padrão geral para novas notas operacionais de Omnisvera.

Este padrão não deve ser aplicado em massa a notas existentes sem lote piloto.

## Frontmatter base recomendado

```yaml
---
type:
status: Rascunho
visibility: Mestre
spoiler_level: medium
gm_secret: true
revealed_in:
created_by: Sage
campaign_status: Em revisao

thumbnail:
cover:
chapters: []

tags:
  - definir
---
```

## Campos técnicos aceitos

| campo | função |
|---|---|
| `type` | Classificação auxiliar. Opcional para notas antigas. |
| `status` | Estado geral da nota ou entidade. |
| `visibility` | Separação entre Mestre, Jogadores e Público. |
| `spoiler_level` | Nível de spoiler. |
| `gm_secret` | Controle explícito de segredo. |
| `revealed_in` | Onde/Quando foi revelado. |
| `created_by` | Responsável/autoria. |
| `campaign_status` | Estado operacional na campanha. |
| `quest_status` | Estado de quest. |
| `handout_status` | Estado de liberação de material entregue. |
| `level` | Nível quando aplicável. |
| `danger_level` | Risco ou ameaça. |
| `hooks` | Ganchos conectados. |
| `rumors` | Rumores conectados. |
| `thumbnail` | Imagem de cards/listagens. |
| `cover` | Imagem ampla/capa. |
| `chapters` | Capítulos/story/seções relacionadas. |
| `tags` | Infraestrutura técnica/visual. |

## Campos herdados preservados

Campos herdados ainda podem existir e não devem ser removidos sem validação:

- `info`;
- `location`;
- `territory`;
- `district`;
- `faction`;
- `religion`;
- `role`;
- `leader`;
- `population`;
- `region`;
- `size`;
- `Alignment`;
- `Government`;
- `reputation`;
- `politics`;
- `exports`;
- `imports`;
- `date`;
- `description`;
- `cssclasses`;
- `cssclass`;
- `tag`;
- `class`;
- `race`;
- `ruleset`.

## Tags

Tags são infraestrutura técnica. Não são o campo narrativo principal.

Tags visuais atuais devem seguir o padrão:

- minúsculas;
- sem acento;
- com hífen quando houver múltiplas palavras.

Exemplos:

- `personagem`;
- `territorio`;
- `religiao`;
- `coroa-de-nimalia`;
- `guilda-dos-mercadores`;
- `conclave-dos-errantes`;
- `guardioes-do-veu-cinzento`;
- `mar-da-neblina`.

## Estrutura mínima de nota

```md
# Nome

## Visão Geral

## Relações

## Ganchos

## Pendências
```

## Regras

- Não inventar lore para preencher campo vazio.
- Não remover campo herdado no mesmo passo em que se adiciona campo novo.
- Não renomear notas usadas por mapa/calendário sem atualizar as configurações.
- Não usar documentação histórica como fonte principal.
