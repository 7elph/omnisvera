# TERRITORY TEMPLATE CONTRACT

## 1. Função do template

Template funcional para territórios/regiões de Disgraceland. Cada território descreve uma zona maior do mapa e alimenta cards de território na Home, além de listar residentes por Dataview.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/Territories`

Exemplos:

- `ASHMOOR.md`
- `GUTTER ROW.md`
- `STEELTOWN.md`
- `CHARSPIRE.md`
- `THRESHTON.md`
- `THE DROWNLANDS.md`
- `WATER.md`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`
- `cover`
- `leader`
- `region`
- `population`

Recorrentes:

- `NoteIcon`
- `Alignment`
- `Government`
- `reputation`
- `politics`
- `size`
- `religion`
- `exports`
- `imports`

Opcionais:

- listas em `region`, `religion`, `exports`, `imports`;
- campos vazios em territórios incompletos.

Sensíveis:

- `tags`, especialmente `territory`;
- `cover`, usado por DataCards;
- `leader`, `region`, `population`, exibidos na Home;
- `location` textual em personagens, usado para puxar residentes.

Visuais:

- `NoteIcon: settlement`
- `cover`
- tag `territory`.

Usados por Dataview:

- `location` em personagens, consultado dentro da nota de território;
- `tags`.

Usados por DataCards:

- `cover`
- `region`
- `leader`
- `population`
- `tags`

Usados por Supercharged Links:

- `territory`
- tags regionais como `ashmoor`, `gutter row`, `steeltown`, etc., se configuradas ou usadas por estilo.

Usados por CSS/snippets:

- callout `[!NOTE|clean no-i right]+`;
- headings HTML `<h2>`.

Desconhecidos, mas preservados por segurança:

- `Alignment`
- `Government`
- `reputation`
- `politics`
- `exports`
- `imports`

## 4. Exemplo de frontmatter

```yaml
---
NoteIcon: settlement
tags:
  - Category/Settlement
  - ashmoor
  - territory
cover: zz_media/territory.png
Alignment: Unlawful Evil
Government: Mayor
reputation: elite class
politics: Mayor
leader: [[Territory Leader]]
region:
  - North-East Tribucia
size: Township
population: 22,000
religion:
  - Church of the Ember Saint
exports:
  - Power, Authority
imports:
  - Everything
---
```

## 5. Estrutura interna da nota

````markdown
# TERRITORY NAME

<h2>Overview</h2>

> [!NOTE|clean no-i right]+ Territory Image
> ![[territory-image.png|400]]

Texto de visão geral.

<h2>Districts</h2>

#### District Name

Descrição do distrito.

---

<h2>Notable Residents of Territory</h2>

```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "territory name")
limit 10
```
````

## 6. Blocos especiais

Usa:

- callout de imagem;
- embed de imagem;
- HTML heading `<h2>`;
- Dataview de residentes;
- links para distritos/âncoras;
- listas YAML.

## 7. Dependências técnicas

- Dataview
- DataCards
- Supercharged Links
- Style Settings
- `world.css`
- `dgl.css`
- snippets de callout
- `zz_media`

## 8. Campos que não podem ser removidos

- `tags`
- `cover`
- `leader`
- `region`
- `population`
- `NoteIcon`
- `Alignment`
- `Government`
- `reputation`
- `politics`
- `size`
- `religion`
- `exports`
- `imports`

## 9. Tags críticas

- `territory`: usada por DataCards/Home e Supercharged Links.
- `Category/Settlement`: categorização do template original.
- tags regionais (`ashmoor`, `gutter row`, `steeltown`, etc.): agrupamento narrativo e possível filtro.

## 10. Consultas relacionadas

Home, cards de territórios:

```datacards
TABLE cover, region, leader, population FROM #territory
SORT name DESC

// Settings
preset: portrait
columns: 6
imageProperty: cover
cardSpacing: 4
```

Residentes no território:

```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "ashmoor")
limit 10
```

## 11. Critérios de validade

Uma nota de território é válida se:

- possui tag `territory`;
- mantém `cover`;
- mantém `leader`, `region` e `population`;
- preserva blocos de distrito quando existentes;
- usa consulta de residentes se precisa listar personagens;
- não altera o nome textual do território sem ajustar consultas e links.

## 12. Riscos de migração futura

- Remover `cover` quebra DataCards da Home.
- Remover `region`, `leader` ou `population` empobrece/rompe cards.
- Renomear território pode quebrar links e filtros `contains(lower(string(location)))`.
- Alterar tags regionais pode quebrar Supercharged Links ou filtros.
- Mover imagem de `zz_media` quebra o callout visual.
