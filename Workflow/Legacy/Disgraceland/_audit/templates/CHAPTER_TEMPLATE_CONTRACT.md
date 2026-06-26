# CHAPTER TEMPLATE CONTRACT

## 1. Função do template

Template funcional para capítulos principais e B-Sides do Disgraceland.

Cada capítulo é uma nota narrativa que também alimenta:

- cards de últimos capítulos na Home;
- DataCards de elenco principal;
- aparições de personagens via `chapters`;
- Calendarium, quando eventos apontam para a nota.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/DISGRACELAND`
- `Workflow/Legacy/Disgraceland/DISGRACELAND/B-Sides From The End Times`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`
- `cover`
- `date`
- `description`

Recorrentes:

- `cssclasses`

Opcionais:

- tags `chapter*`;
- tags `bside*`;
- classes como `character/Scumbag`.

Sensíveis:

- `tags`, especialmente `story`;
- `cover`, usado por DataCards da Home;
- `date`, exibido nos cards de últimos capítulos;
- `description`, exibido nos cards;
- `cssclasses`, usada para visual/script.

Visuais:

- `cssclasses`
- `cover`
- tag `story`.

Usados por Dataview:

- `file.name`, por aparições de personagens;
- `date`, `description`, `cover`, quando listados.

Usados por DataCards:

- `cover`
- `date`
- `description`
- tags `story`, `chapter*`, `bside*`.

Usados por Supercharged Links:

- `story`.

Usados por CSS/snippets:

- `b-sides-script`
- `chapter`
- `scriptwrite.css`
- `bside.css`

Desconhecidos, mas preservados por segurança:

- classes específicas como `character/Scumbag`.

## 4. Exemplo de frontmatter

```yaml
---
cssclasses:
  - b-sides-script
  - chapter
tags:
  - chapter
  - story
  - chapter1
cover: [[zz_media/chapter-cover.png]]
date: 1st of Bloomsun, 2186
description: Short chapter description.
---
```

B-Side:

```yaml
---
cssclasses:
  - b-sides-script
  - chapter
  - character/Scumbag
tags:
  - bside01
  - bside
  - story
cover: zz_media/bside-cover.png
date: 6th of Bloomsun, 2186
description: Short B-Side description.
---
```

## 5. Estrutura interna da nota

Capítulo principal:

````markdown
# Chapter 01:

#### _Temperday Afternoon, 1st of [[CALENDAR|Bloomsun]], 2186_

> Chapter summary.

## MAIN CAST

```datacards
TABLE thumbnail, location, status FROM #chapter01
SORT name ASC

// Settings
preset: compact
columns: 5
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

> [!world]- SPOILERS
> Spoiler summary.

---

#### CHAPTER TITLE

Your story goes here...
````

B-Side:

````markdown
## **"B-SIDE TITLE"**
##### _A B-Side from the End Times_

> B-Side summary.

## MAIN CAST

```datacards
TABLE thumbnail, location, status FROM #bside1
SORT name ASC
```

---

Your story goes here...
````

## 6. Blocos especiais

Usa:

- DataCards de elenco;
- callout `[!world]- SPOILERS` em capítulos principais;
- `cssclasses`;
- cover;
- links internos;
- headings estilizados.

## 7. Dependências técnicas

- DataCards
- Dataview, por aparições de personagens
- Supercharged Links
- Style Settings
- `bside.css`
- `scriptwrite.css`
- `world.css`
- `dgl.css`
- Calendarium, quando evento aponta para capítulo
- `zz_media`

## 8. Campos que não podem ser removidos

- `tags`
- `cover`
- `date`
- `description`
- `cssclasses`

## 9. Tags críticas

- `story`: usada por Home/DataCards e Supercharged Links.
- `chapter`: identifica capítulo principal.
- `chapter1`, `chapter01`, etc.: usados para DataCards de elenco.
- `bside`, `bside01`, `bside1`: usados para DataCards de elenco B-Side.

## 10. Consultas relacionadas

Home, últimos capítulos:

```datacards
TABLE cover, date, description FROM #story
SORT file.ctime desc
limit 3
```

Elenco:

```datacards
TABLE thumbnail, location, status FROM #chapter01
SORT name ASC
```

Aparições em personagem dependem do nome do arquivo do capítulo:

```dataview
list
from "DISGRACELAND"
where contains(this.chapters, file.name)
sort file.name asc
```

## 11. Critérios de validade

Uma nota de capítulo é válida se:

- está em `DISGRACELAND`;
- possui tag `story`;
- possui `cover`, `date` e `description`;
- mantém `cssclasses` de script/capítulo;
- usa tag de elenco compatível com personagens;
- seu `file.name` corresponde aos valores em `chapters` dos personagens.

## 12. Riscos de migração futura

- Renomear arquivo quebra aparições de personagens.
- Remover `story` tira o capítulo da Home.
- Remover `cover`, `date` ou `description` quebra cards de últimos capítulos.
- Alterar tags `chapter*`/`bside*` quebra DataCards de elenco.
- Remover `cssclasses` altera aparência de script.
