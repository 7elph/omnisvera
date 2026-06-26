# LOCATION TEMPLATE CONTRACT

## 1. Função do template

Template funcional para locais específicos dentro de territórios: clubes, ilhas, sedes, mercados, estúdios e pontos de interesse.

O template alimenta cards de locais na Home e serve como página de referência com imagem, descrição, reputação e links para personagens/facções.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/Locations`

Exemplos:

- `Hollow House.md`
- `Three Nail Market.md`
- `TTV Studios.md`
- `Coffin Island.md`
- `Ha Ha Hole.md`

## 3. Frontmatter real

Obrigatórios para funcionamento do tipo:

- `tags`
- `cover`
- `territory`
- `info`

Recorrentes:

- `obsidianUIMode`
- `NoteIcon`
- `NoteStatus`
- `status`
- `district`

Opcionais:

- `location`
- `faction`
- tags narrativas como `entertainment`, `brothel`, `faction`.

Sensíveis:

- `tags`, especialmente `location`;
- `cover`, usado por DataCards;
- `territory` e `info`, exibidos na Home;
- `district`, usado para contexto e links de âncora.

Visuais:

- `cover`
- `NoteIcon`
- callout de imagem.

Usados por Dataview:

- tags, se consultadas.

Usados por DataCards:

- `cover`
- `territory`
- `info`
- tag `location`

Usados por Supercharged Links:

- `lore` aparece em algumas notas de local;
- outras tags podem afetar link visual se configuradas.

Usados por CSS/snippets:

- callout `[!NOTE|clean no-i right]+`;
- callouts customizados, exemplo `[!hollow]`.

Desconhecidos, mas preservados por segurança:

- `NoteStatus`
- tags específicas do local.

## 4. Exemplo de frontmatter

```yaml
---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus:
status: Open for Business
info: Short public description of the location.
territory: "[[GUTTER ROW]]"
district: "[[GUTTER ROW#Red Light District|Red Light District]]"
cover: zz_media/location.png
tags:
  - lore
  - entertainment
  - location
---
```

## 5. Estrutura interna da nota

```markdown
# Location Name

> [!NOTE|clean no-i right]+ Location Name
> ![[location-image.png|500]]

> "Quote or local saying."
> – [[Speaker]]

## Overview
**Name:**
**Type:**
**Location:**
**Founder:**
**Security:**
**Clientele:**

# Reputation

| Who | What They Say |
|---|---|

# Related NPC or section

> [!custom-callout]- Lore Notes
- Notes and rumors.

# Tags
`#tag` `#location`
```

## 6. Blocos especiais

Usa:

- callouts de imagem;
- embeds de imagem com tamanho;
- callouts customizados;
- tabelas Markdown;
- tags inline em alguns casos;
- links para territórios/distritos.

## 7. Dependências técnicas

- DataCards
- Dataview, indiretamente
- Supercharged Links
- Style Settings
- `dgl.css`
- snippets de callout
- `zz_media`

## 8. Campos que não podem ser removidos

- `tags`
- `cover`
- `territory`
- `info`
- `district`
- `status`
- `NoteIcon`
- `NoteStatus`
- `obsidianUIMode`

## 9. Tags críticas

- `location`: usada pela Home/DataCards.
- `lore`: pode acionar Supercharged Links.
- tags locais (`hollowhouse`, `shana`, `gutterrow`, etc.): agrupamento narrativo e possíveis filtros.
- `faction`, quando presente: pode conflitar tecnicamente com notas de facção, portanto deve ser preservada até análise.

## 10. Consultas relacionadas

Home, cards de locais:

```datacards
TABLE cover, territory, info FROM #location
SORT rating ASC

// Settings
preset: grid
columns: 5
imageProperty: cover
cardSpacing: 4
```

## 11. Critérios de validade

Uma nota de local é válida se:

- possui tag `location`;
- possui `cover`;
- possui `territory`;
- possui `info` quando deve aparecer na Home;
- preserva callout/embeds de imagem quando há visual;
- não move imagem sem atualizar referência.

## 12. Riscos de migração futura

- Remover `info` deixa card sem descrição.
- Trocar `cover` por `thumbnail` quebra cards de locais.
- Renomear distrito/território quebra links de contexto.
- Remover tag `location` tira o local da Home.
- Apagar imagem aparentemente órfã pode quebrar callout.
