# FACTION TEMPLATE CONTRACT

## 1. Função do template

Template funcional para notas de facções. Cada facção funciona como hub narrativo e técnico para agrupar personagens por tag, exibir cards de membros e preservar identidade visual.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/Factions`

Exemplos reais:

- `Loyalist Guard.md`
- `Third Row.md`
- `Murray Boys.md`
- `Rancher Collective.md`
- `Rustwater Raiders.md`
- `Steeltown Wrecking Crew.md`
- `Unseen Widows.md`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`
- `thumbnail`
- `status`

Recorrentes:

- `obsidianUIMode`
- `NoteIcon`
- `NoteStatus`
- `leader`
- `location`
- `faction`

Opcionais:

- `faction` pode apontar para a própria facção ou aparecer inconsistente em algumas notas;
- `location` pode variar entre território ou local;
- tags secundárias como `antagonist`, `military`.

Sensíveis:

- tag principal da facção, por exemplo `loyalist`, `third`, `rancher`, `pirate`, `widow`, `murray`, `steeltown`.
- `thumbnail`, usado pelos cards.
- `leader`, exibido ou usado como metadado.

Visuais:

- `NoteIcon: faction`
- `thumbnail`
- tags visuais Supercharged.

Usados por Dataview:

- indiretamente por tags e campos exibidos em dashboards.

Usados por DataCards:

- `thumbnail`
- `location`
- `status`
- `tags`

Usados por Supercharged Links:

- tag principal da facção.

Usados por CSS/snippets:

- callout `[!NOTE|clean no-i right]+`;
- callouts internos como `[!column]`, `[!curse]` em algumas facções.

Desconhecidos, mas preservados por segurança:

- `NoteStatus`
- `faction`
- tags secundárias de papel narrativo.

## 4. Exemplo de frontmatter

```yaml
---
obsidianUIMode: preview
NoteIcon: faction
NoteStatus: New
thumbnail: zz_media/faction.png
leader: [[Faction Leader]]
status: Active
location: "[[Gutter Row]]"
faction: "[[Faction Name]]"
tags:
  - faction
  - antagonist
  - third
---
```

## 5. Estrutura interna da nota

Ordem funcional observada:

````markdown
# FACTION NAME

```datacards
TABLE thumbnail, location, status FROM #tag-principal
SORT name ASC

// Settings
preset: compact
columns: 6
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

> [!NOTE|clean no-i right]+ Faction Name
> ![[faction-image.png|400]]

> [!column] Information
>> [!curse] <h4>Details</h4>
>> **Group:** [[Faction Name]]
>> **Founder:** ...
>> **Home Location:** ...
>> **Current Leader:** ...
>> **Status:** ...

---

## Overview

## Symbols & Identity

## Leadership

## Origins & History

## Influence
````

Nem todas as facções usam todas as seções, mas o padrão técnico é: frontmatter + DataCards + imagem/callout + dados estruturados + seções narrativas.

## 6. Blocos especiais

Usa:

- DataCards para membros relacionados;
- callout de retrato/imagem;
- callouts internos de informação;
- embeds de imagem;
- tags visuais;
- HTML manual em cabeçalhos, ocasionalmente.

## 7. Dependências técnicas

- DataCards
- Dataview, indiretamente via dashboards
- Supercharged Links
- Style Settings
- `dgl.css`
- `disgraceland-profile.css`
- `supercharged-links-gen.css`
- `zz_media`

## 8. Campos que não podem ser removidos

- `tags`
- `thumbnail`
- `leader`
- `status`
- `location`
- `faction`
- `NoteIcon`
- `NoteStatus`
- `obsidianUIMode`

## 9. Tags críticas

Tags de facção com função técnica/visual:

- `loyalist`
- `rancher`
- `third`
- `pirate`
- `widow`
- `murray`
- `steeltown`

Também relevantes:

- `faction`: identifica nota de facção.
- `antagonist`, `military`: agrupamento narrativo.

Usos:

- Supercharged Links: cor/peso de links.
- DataCards: `FROM #tag`.
- Dataview/Home: agrupamento e filtros indiretos.
- narrativa: organização de personagens por facção.

## 10. Consultas relacionadas

Exemplo real de facção:

```datacards
TABLE thumbnail, location, status FROM #third
SORT name ASC

// Settings
preset: compact
columns: 8
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

Outro padrão:

```datacards
TABLE thumbnail, location, status FROM #loyalist
SORT name ASC
```

## 11. Critérios de validade

Uma nota de facção é válida se:

- está em `Factions`;
- possui `tags` com `faction` e uma tag principal de agrupamento;
- possui `thumbnail` quando usa DataCards;
- possui bloco DataCards consultando sua tag principal;
- preserva `leader`, `status` e `location`;
- não remove tag visual configurada no Supercharged Links.

## 12. Riscos de migração futura

- Renomear a tag principal esvazia DataCards da facção.
- Remover a tag principal remove cor/peso de links.
- Remover `thumbnail` quebra cards.
- Padronizar `faction` sem auditoria pode apagar relação com personagens.
- Mover imagens de facção quebra callouts.
