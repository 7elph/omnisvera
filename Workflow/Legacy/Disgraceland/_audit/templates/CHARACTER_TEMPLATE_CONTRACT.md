# CHARACTER TEMPLATE CONTRACT

## 1. Função do template

Template funcional para notas de personagens de Disgraceland. Representa indivíduos, protagonistas, antagonistas, membros de facções, prefeitos e personagens agrupados por subpastas.

O template cumpre quatro papéis técnicos:

- exibir ficha/visão geral do personagem;
- renderizar retrato por callout;
- alimentar dashboards e DataCards via `thumbnail`, `status`, `location`, `territory`, `district`, `faction`, `religion` e `role`;
- listar aparições em capítulos via `chapters` + Dataview.

## 2. Pasta de origem

Notas aparecem em:

- `Workflow/Legacy/Disgraceland/Characters/Individual`
- `Workflow/Legacy/Disgraceland/Characters/Mayors of Tribucia`
- `Workflow/Legacy/Disgraceland/Characters/Murray Boys`
- `Workflow/Legacy/Disgraceland/Characters/Rancher Collective`
- `Workflow/Legacy/Disgraceland/Characters/Rustwater Raiders`
- `Workflow/Legacy/Disgraceland/Characters/Steeltown Wrecking Crew`
- `Workflow/Legacy/Disgraceland/Characters/The Elite & Loyalist Guard`
- `Workflow/Legacy/Disgraceland/Characters/Third Row`
- `Workflow/Legacy/Disgraceland/Characters/Unseen Widows`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`
- `thumbnail`
- `status`

Recorrentes:

- `obsidianUIMode`
- `NoteIcon`
- `NoteStatus`
- `religion`
- `location`
- `territory`
- `district`
- `faction`
- `role`
- `chapters`

Opcionais:

- valores vazios de `NoteIcon`, `religion`, `faction`, `district` ou `chapters`;
- tags específicas de capítulo, facção, religião ou grupo.

Sensíveis:

- `chapters`: usado para aparições em Dataview.
- `thumbnail`: usado por DataCards e Home.
- `tags`: usado por Dataview, DataCards e Supercharged Links.
- `faction`, `location`, `territory`, `district`: usados por dashboards e consultas.

Visuais:

- `obsidianUIMode`
- `NoteIcon`
- `thumbnail`
- `tags`

Usados por Dataview:

- `chapters`
- `thumbnail`
- `status`
- `role`
- `district`
- `territory`
- `faction`
- `religion`
- `tags`
- `file.name`
- `file.mtime`

Usados por DataCards:

- `thumbnail`
- `location`
- `status`
- tags de capítulo/facção.

Usados por Supercharged Links:

- `tags`, especialmente tags visuais de facção/grupo.

Usados por CSS/snippets:

- callout de retrato `[!NOTE|clean no-i right]+`;
- possíveis estilos gerados por Supercharged Links.

Desconhecidos, mas preservados por segurança:

- `NoteIcon`
- `NoteStatus`
- tags específicas de capítulo, religião e subgrupo.

## 4. Exemplo de frontmatter

```yaml
---
obsidianUIMode: preview
NoteIcon:
NoteStatus: New
thumbnail: zz_media/th_character.png
religion: "[[Church of the Ember Saint]]"
status: Alive
location: "[[Gutter Row]]"
territory: "[[GUTTER ROW]]"
district: "[[GUTTER ROW#Vileby|Vileby]]"
faction: None
role: Character role
chapters:
  - 05 - Sight Unseen
tags:
  - character
  - individual
  - chapter05
---
```

## 5. Estrutura interna da nota

Ordem funcional observada:

````markdown
# CHARACTER NAME

> [!NOTE|clean no-i right]+ Character Name
> ![[character-image.png|400]]

## Overview
**Titles:**
**Alias/Nickname:**
**Home Location:**
**Public Reputation:**
**Gender:**
**Spouse:**
**Age:**
**Height:**
**Weight:**
**Date of Birth:**
**Occupation:**
**Status:**
**Affiliation:**
**Known Associates:**
**Faith:**
**Appearances:**

```dataview
list
from "DISGRACELAND"
where contains(this.chapters, file.name)
sort file.name asc
```

---

## Biography

> <h4>Character quote</h4>

## Personality

**Temperament:**
**Vices:**
**Abilities:**
**Secrets:**
**Beliefs:**

## Role In Disgraceland
````

## 6. Blocos especiais

Usa:

- Dataview para aparições;
- callout de retrato;
- embed de imagem com tamanho;
- tags visuais;
- links internos para locais, facções, religião e associados.

Não depende diretamente de:

- Leaflet;
- Calendarium;
- banner.

## 7. Dependências técnicas

- Dataview
- DataCards
- Supercharged Links
- Style Settings
- `disgraceland-profile.css`
- `dgl.css`
- `supercharged-links-gen.css`
- snippets de callout `[!NOTE|clean no-i right]`
- `zz_media`

## 8. Campos que não podem ser removidos

- `tags`
- `thumbnail`
- `status`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`
- `NoteIcon`
- `NoteStatus`
- `obsidianUIMode`

## 9. Tags críticas

Tags com função técnica/visual:

- `character`: usada por Home/Dataview.
- `individual`: usada por Supercharged Links.
- `loyalist`: Supercharged Links, facção e agrupamento.
- `rancher`: Supercharged Links, facção e agrupamento.
- `third`: Supercharged Links, facção e agrupamento.
- `pirate`: Supercharged Links, facção e agrupamento.
- `widow`: Supercharged Links, facção e agrupamento.
- `murray`: Supercharged Links e agrupamento.
- `steeltown`: Supercharged Links e agrupamento.
- tags `chapter*`: conectam personagens a capítulos/DataCards.

## 10. Consultas relacionadas

Aparições do personagem:

```dataview
list
from "DISGRACELAND"
where contains(this.chapters, file.name)
sort file.name asc
```

Últimos personagens na Home:

```dataview
table
  "<img src='" + thumbnail + "' width='60' ... />" as "IMAGE",
  status,
  role,
  district,
  territory,
  faction,
  religion,
  date(file.mtime) as "TIME/DATE"
from "Characters"
where contains(tags, "character")
sort file.mtime desc
limit 5
```

Elenco de capítulos:

```datacards
TABLE thumbnail, location, status FROM #chapter01
SORT name ASC
```

## 11. Critérios de validade

Uma nota de personagem é válida se:

- está dentro de `Characters`;
- possui `tags` contendo `character` ou tag de grupo equivalente;
- mantém `thumbnail` quando aparece em DataCards/Home;
- mantém `chapters` quando precisa listar aparições;
- mantém o callout de retrato quando possui imagem;
- preserva campos de localização, facção, religião e papel usados pela Home;
- não remove tags visuais sem substituição documentada.

## 12. Riscos de migração futura

- Remover `chapters` quebra aparições.
- Trocar `thumbnail` por `cover` quebra DataCards e Home.
- Renomear tags de facção quebra Supercharged Links e cards.
- Remover `character` quebra o dashboard de últimos personagens.
- Mover imagens de `zz_media` quebra retratos.
- Renomear capítulos quebra `where contains(this.chapters, file.name)`.
