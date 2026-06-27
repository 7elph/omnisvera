# Omnisvera — Schema de Frontmatter

> [!IMPORTANT]
> Este documento segue a taxonomia oficial atual do Sage.
> Fonte da verdade: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].

## Função

Define o schema técnico recomendado para novos templates e novas notas operacionais.

Não aplicar em massa a notas existentes sem lote piloto.

## Schema base

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

level:
danger_level:
hooks: []
rumors: []

thumbnail:
cover:
chapters: []

tags:
  - definir
---
```

## Campos aceitos

| campo | tipo esperado | uso |
|---|---|---|
| `type` | texto | Classificação auxiliar. Opcional. |
| `status` | texto | Estado geral da nota. |
| `visibility` | texto | `Mestre`, `Jogadores` ou `Público`. |
| `spoiler_level` | texto | `none`, `light`, `medium`, `heavy`. |
| `gm_secret` | booleano | Segredo do mestre. |
| `revealed_in` | texto/lista | Onde/Quando foi revelado. |
| `created_by` | texto | Autor/responsável. |
| `campaign_status` | texto | Estado da entidade na campanha. |
| `quest_status` | texto | Estado de quest. |
| `handout_status` | texto | Estado de liberação de material entregue. |
| `level` | número/texto | Nível ou escala. |
| `danger_level` | texto/número | Risco. |
| `hooks` | lista | Ganchos. |
| `rumors` | lista | Rumores. |
| `thumbnail` | path | Imagem compacta. |
| `cover` | path | Imagem ampla. |
| `chapters` | lista | Capítulos/story/seções. |
| `tags` | lista | Infraestrutura técnica/visual. |

## Campos herdados preservados

Não remover automaticamente:

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

## Tags técnicas

Tags visuais migradas:

- `personagem`;
- `territorio`;
- `religiao`;
- `coroa-de-nimalia`;
- `guilda-dos-mercadores`;
- `conclave-dos-errantes`;
- `guardioes-do-veu-cinzento`;
- `mar-da-neblina`;
- `nimalia`.

Tags pendentes:

- `third`;
- `murray`;
- `story`.

## Compatibilidade

- `tags` deve continuar existindo quando plugins ou consultas dependerem dele.
- `tag` singular deve ser convertido para `tags` apenas em lote seguro.
- `cssclasses` e `cssclass` devem ser documentados antes de qualquer alteração.
- `chapters` não deve ser removido.
