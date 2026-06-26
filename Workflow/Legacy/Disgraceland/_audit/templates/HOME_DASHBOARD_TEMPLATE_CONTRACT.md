# HOME DASHBOARD TEMPLATE CONTRACT

## 1. Função do template

Template funcional da Home/dashboard do vault Disgraceland. É a entrada visual e operacional do vault, reunindo navegação, calendário, capítulos recentes, notícias, personagens atualizados, territórios, locais e arquivos modificados.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/Home.md`

## 3. Frontmatter real

Obrigatórios para funcionamento visual:

- `obsidianUIMode`
- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`

Recorrentes:

- não há outros campos recorrentes na Home observada.

Opcionais:

- nenhum confirmado.

Sensíveis:

- todos os campos de banner;
- links dos cards de navegação;
- tags consultadas por DataCards/Dataview.

Visuais:

- todos os campos de banner;
- imagens HTML e embeds;
- callouts de dashboard.

Usados por Dataview:

- `thumbnail`
- `status`
- `role`
- `district`
- `territory`
- `faction`
- `religion`
- `file.mtime`
- `file.path`
- `file.folder`
- `file.name`

Usados por DataCards:

- `cover`
- `date`
- `description`
- `region`
- `leader`
- `population`
- `territory`
- `info`

Usados por Supercharged Links:

- tags das notas consultadas.

Usados por CSS/snippets:

- `[!cards]`
- `[!world]`
- `[!infobox]`
- `[!news]`
- `[!home]`
- `[!note]`
- classe HTML `homepage`.

Desconhecidos, mas preservados por segurança:

- sintaxes de imagem com parâmetros `sban htiny ctr p+t`.

## 4. Exemplo de frontmatter

```yaml
---
obsidianUIMode: preview
banner: "[[zz_media/big1.png]]"
banner-x: 51
banner-y: 34
banner-height: 280
content-start: 271
banner-fade: -45
---
```

## 5. Estrutura interna da nota

````markdown
<div style="text-align: center;">
  <img src="wod.png" width="1300px">
</div>

> [!cards|5]
> **DISGRACELAND**
> [![[sool.png|sban htiny ctr p+t]]](DISGRACELAND.md)
> ...

> [!world]- A LOOK AT DISGRACELAND
> ```datacards
> TABLE cover FROM #home
> ```

<div class="homepage">
<hr>
</div>

> [!infobox]
> ```calendarium
> ```
> **LATEST CHAPTERS:**
> ```datacards
> TABLE cover, date, description FROM #story
> ```

> [!news]+ TRIBUCIA TRIBUTE NEWS REPORT
> News text and links.

> [!home]+ LAST (5) Updated Characters
> ```dataview
> table ...
> from "Characters"
> where contains(tags, "character")
> ```

> [!note]+ TERRITORIES
> ```datacards
> TABLE cover, region, leader, population FROM #territory
> ```

> [!note]- LOCATIONS
> ```datacards
> TABLE cover, territory, info FROM #location
> ```

```dataview
TABLE WITHOUT ID
link(file.path, file.folder + " / " + file.name) AS "Last Modified",
file.mtime AS "Date"
FROM "/"
...
```
````

## 6. Blocos especiais

Usa:

- HTML manual;
- embeds de imagem com parâmetros;
- callouts customizados;
- Dataview;
- DataCards;
- Calendarium;
- banner;
- links para páginas principais.

## 7. Dependências técnicas

- Homepage
- Dataview
- DataCards
- Calendarium
- Supercharged Links
- Style Settings
- `world.css`
- `topnav.css`
- `dgl.css`
- snippets de callout
- `zz_media`

## 8. Campos que não podem ser removidos

Na Home:

- `obsidianUIMode`
- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`

Nas notas consultadas pela Home:

- `tags`
- `cover`
- `thumbnail`
- `status`
- `role`
- `district`
- `territory`
- `faction`
- `religion`
- `date`
- `description`
- `region`
- `leader`
- `population`
- `info`

## 9. Tags críticas

- `home`: cards de visão geral.
- `story`: últimos capítulos.
- `character`: últimos personagens.
- `territory`: cards de territórios.
- `location`: cards de locais.

Tags visuais das notas consultadas continuam relevantes para Supercharged Links.

## 10. Consultas relacionadas

```datacards
TABLE cover FROM #home
SORT file.name asc
```

```datacards
TABLE cover, date, description FROM #story
SORT file.ctime desc
limit 3
```

```dataview
table status, role, district, territory, faction, religion
from "Characters"
where contains(tags, "character")
sort file.mtime desc
limit 5
```

```datacards
TABLE cover, region, leader, population FROM #territory
```

```datacards
TABLE cover, territory, info FROM #location
```

## 11. Critérios de validade

A Home é válida se:

- mantém frontmatter de banner;
- mantém callouts estruturais;
- todos os DataCards retornam resultados;
- tabela de personagens consegue ler `thumbnail` e campos de personagem;
- Calendarium renderiza;
- imagens dos cards existem;
- links principais apontam para notas existentes.

## 12. Riscos de migração futura

- Remover tags consultadas esvazia seções da Home.
- Trocar campos `cover`/`thumbnail` quebra imagens.
- Remover campos de banner quebra composição visual.
- Remover snippets altera layout de dashboard.
- Alterar pastas consultadas quebra Dataview.
