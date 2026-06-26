# MEDIA REFERENCE TEMPLATE CONTRACT

## 1. Função do template

Contrato funcional para referências de mídia no vault Disgraceland. Não é um tipo narrativo de nota, mas um padrão técnico usado por personagens, facções, territórios, locais, lore, Home, calendário, capítulos e mapa.

## 2. Pasta de origem

Mídia:

- `Workflow/Legacy/Disgraceland/zz_media`

Referências aparecem em:

- frontmatter de notas;
- embeds Markdown;
- HTML manual;
- blocos Leaflet;
- JSON de plugins;
- CSS/snippets, potencialmente.

## 3. Frontmatter real

Campos de mídia recorrentes:

- `thumbnail`
- `cover`
- `banner`

Outros campos relacionados:

- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`

Obrigatórios por contexto:

- personagem/facção: `thumbnail`;
- território/local/lore/story: `cover`;
- Home: `banner`;
- mapa: `cover` e imagem Leaflet.

Sensíveis:

- extensões e nomes de arquivo;
- caminhos `zz_media/...`;
- wikilinks de mídia `[[zz_media/...]]`;
- embeds com basename, como `![[ava.png|400]]`;
- HTML `<img src="wod.png">`.

Visuais:

- todos.

Usados por Dataview:

- `thumbnail` em tabela de personagens.

Usados por DataCards:

- `thumbnail`
- `cover`
- `imageProperty`

Usados por Supercharged Links:

- não diretamente.

Usados por CSS/snippets:

- parâmetros de imagem;
- classes de banner;
- callouts com imagens.

Desconhecidos, mas preservados por segurança:

- mídias sem referência textual simples podem ser usadas por CSS, Canvas, plugins ou Obsidian.

## 4. Exemplo de frontmatter

Personagem:

```yaml
thumbnail: zz_media/th_character.png
```

Território/local/chapter:

```yaml
cover: zz_media/location.png
```

Home:

```yaml
banner: "[[zz_media/big1.png]]"
banner-x: 51
banner-y: 34
banner-height: 280
content-start: 271
banner-fade: -45
```

## 5. Estrutura interna da nota

Padrões reais:

```markdown
> [!NOTE|clean no-i right]+ Portrait
> ![[image.png|400]]
```

```markdown
<div style="text-align: center;">
  <img src="wod.png" width="1300px">
</div>
```

```markdown
[![[sool.png|sban htiny ctr p+t]]](DISGRACELAND.md)
```

```leaflet
image: zz_media/Tribucia.png
```

## 6. Blocos especiais

Usa:

- embeds Obsidian;
- HTML `<img>`;
- imagens em callouts;
- campos `thumbnail`, `cover`, `banner`;
- Leaflet `image`;
- DataCards `imageProperty`;
- parâmetros de imagem Obsidian.

## 7. Dependências técnicas

- DataCards
- Dataview
- Leaflet
- Homepage
- snippets de callout
- CSS de banner/tema
- `zz_media`

## 8. Campos que não podem ser removidos

- `thumbnail`
- `cover`
- `banner`
- `banner-x`
- `banner-y`
- `banner-height`
- `content-start`
- `banner-fade`

## 9. Tags críticas

Mídia não depende de tags diretamente, mas é selecionada por templates que dependem de:

- `character`
- `faction`
- `territory`
- `location`
- `story`
- `home`

Essas tags determinam quais notas entram em DataCards que exigem mídia.

## 10. Consultas relacionadas

DataCards com thumbnail:

```datacards
TABLE thumbnail, location, status FROM #loyalist
imageProperty: thumbnail
```

DataCards com cover:

```datacards
TABLE cover, region, leader, population FROM #territory
imageProperty: cover
```

Dataview da Home:

```dataview
"<img src='" + thumbnail + "' width='60' ... />" as "IMAGE"
```

Leaflet:

```leaflet
image: zz_media/Tribucia.png
```

## 11. Critérios de validade

Uma referência de mídia é válida se:

- o arquivo existe;
- o caminho/extensão corresponde exatamente à referência;
- o tipo de campo corresponde ao template (`thumbnail` para cards pequenos, `cover` para cards de capa);
- embeds preservam parâmetros de tamanho quando usados;
- Leaflet encontra a imagem base;
- Home encontra imagens de navegação.

## 12. Riscos de migração futura

- Apagar mídia “órfã” por análise simples pode quebrar CSS, JSON, Canvas ou HTML.
- Converter extensão sem atualizar referências quebra renderização.
- Mover imagens para subpastas quebra embeds por basename.
- Trocar `thumbnail` por `cover` quebra DataCards.
- Trocar `cover` por `thumbnail` quebra Home/territórios/locais.
