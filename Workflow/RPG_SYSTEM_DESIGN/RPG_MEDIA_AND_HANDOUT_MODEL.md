> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG MEDIA AND HANDOUT MODEL

Modelo para imagens, capas, retratos, tokens, mapas e handouts em um vault de RPG.

Não aplica mudanças. Não remove mídia. Não compara com Omnisvera.

## 1. Princípio central

Mídia é parte do sistema técnico, não apenas decoração.

No Disgraceland, `thumbnail`, `cover`, banner, embeds e Leaflet dependem de arquivos em `zz_media`. Em RPG, a mídia precisa ser ainda mais explícita, porque algumas imagens podem ser mostradas aos jogadores e outras são só do mestre.

## 2. Campos de mídia

| campo | uso |
| --- | --- |
| `thumbnail` | imagem pequena para DataCards e listas |
| `cover` | capa visual de nota/card grande |
| `portrait` | retrato de personagem/NPC |
| `map_image` | mapa base ou mapa de nota |
| `handout_image` | imagem preparada para entregar aos jogadores |
| `token_image` | token para combate/VTT |
| `banner` | banner de dashboard ou página principal |
| `media_status` | estado operacional da mídia |
| `handout_status` | estado de liberação de handout |

## 3. Status de mídia

```yaml
media_status: active
```

Valores propostos:

- `active`: usada em nota ou dashboard.
- `draft`: ainda em revisão.
- `candidate`: possível uso futuro.
- `unused`: sem uso confirmado.
- `archived`: preservada por segurança.
- `broken`: referência quebrada.

## 4. Imagem pública vs imagem secreta

Campos:

```yaml
visibility: Mestre
player_known: false
handout_status: hidden
```

Regras:

- `portrait` pode ser privado até o NPC ser revelado.
- `handout_image` só deve aparecer em dashboard de jogador se `handout_status = revealed`.
- `map_image` pode ter versão do mestre e versão pública.

## 5. Mídia usada em DataCards

Padrões:

```yaml
thumbnail: zz_media/th_npc.png
cover: zz_media/location.png
```

DataCards:

```datacards
TABLE thumbnail, location, status FROM #npc
imageProperty: thumbnail
```

```datacards
TABLE cover, territory, info FROM #location
imageProperty: cover
```

Regra: não trocar `thumbnail` por `cover` sem atualizar `imageProperty`.

## 6. Mídia usada no mapa

```yaml
map_image: zz_media/maps/region.png
```

Leaflet:

```leaflet
image: zz_media/maps/region.png
```

Regras:

- renomear imagem exige atualizar bloco Leaflet e JSON;
- mapa de mestre e mapa público devem ser arquivos diferentes ou claramente identificados;
- marcadores precisam linkar notas existentes.

## 7. Mídia usada como retrato

```yaml
portrait: zz_media/characters/npc.png
thumbnail: zz_media/characters/th_npc.png
```

Callout:

```markdown
> [!NOTE|clean no-i right]+ NPC Name
> ![[npc.png|400]]
```

Regra: retrato pode ser maior e mais expressivo; thumbnail deve ser leve e legível em card.

## 8. Handouts

Campos propostos:

```yaml
type: handout
handout_image: zz_media/handouts/clue.png
handout_status: ready
visibility: Mestre
player_known: false
revealed_in:
```

Estados:

- `hidden`: existe, não mostrar.
- `ready`: pronto para mostrar.
- `revealed`: já entregue.
- `retired`: não será mais usado.

## 9. Mídia órfã

Regra absoluta: nunca apagar mídia só porque não foi encontrada em Markdown.

Antes de apagar, checar:

- frontmatter;
- embeds;
- HTML;
- CSS;
- JSON de plugins;
- Canvas;
- Leaflet;
- Dataview/DataCards;
- notas futuras/rascunhos;
- handouts ainda não revelados.

## 10. Organização conceitual

Sem aplicar agora, uma organização RPG poderia separar:

- `zz_media/characters`
- `zz_media/characters/thumbnails`
- `zz_media/factions`
- `zz_media/locations`
- `zz_media/maps`
- `zz_media/handouts`
- `zz_media/items`
- `zz_media/ui`

Mas isso só deve ser decidido depois de mapear o vault real.

## 11. Critérios de validade

Uma mídia é válida se:

- arquivo existe;
- campo aponta para caminho correto;
- tipo de campo corresponde ao uso;
- imagem pública não contém spoiler;
- handout tem status;
- mapa Leaflet renderiza;
- DataCards encontra `imageProperty`.

## 12. Riscos

- conversão de extensão quebrar referências;
- mover imagem quebrar embeds por basename;
- usar imagem secreta em dashboard público;
- apagar mídia candidata;
- confundir `cover`, `thumbnail` e `portrait`;
- deixar `handout_status` vazio;
- renomear mapa sem atualizar Leaflet.
