# MAP TEMPLATE CONTRACT

## 1. Função do template

Template funcional para mapa interativo Leaflet de Tribucia. A nota contém frontmatter de escala e um bloco `leaflet`; os marcadores e ícones são persistidos no JSON do plugin.

## 2. Pasta de origem

- `Workflow/Legacy/Disgraceland/TRIBUCIA MAP.md`
- configuração relacionada: `Workflow/Legacy/Disgraceland/.obsidian/plugins/obsidian-leaflet-plugin/data.json`

## 3. Frontmatter real

Obrigatórios para funcionamento observado:

- `width`
- `height`
- `scale`
- `distance`
- `NoteIcon`
- `cover`
- `type`
- `tags`

Recorrentes:

- `Community-Size`
- `Alignment`
- `Government`
- `politics`
- `region`
- `size`
- `population`
- `religion`
- `exports`
- `imports`

Opcionais:

- campos vazios como `Alignment`, `religion`;
- listas em `region`, `exports`, `imports`.

Sensíveis:

- `width`, `height`, `scale`, `distance`: parâmetros de mapa/escala;
- `cover`;
- imagem base no bloco Leaflet;
- `id: tribucia-map`.

Visuais:

- `cover`
- bloco Leaflet
- tipos de marcadores.

Usados por Dataview:

- não é primariamente Dataview.

Usados por DataCards:

- `cover` se mapa aparece como card.

Usados por Supercharged Links:

- tags e links internos no mapa/notas conectadas.

Usados por CSS/snippets:

- Leaflet renderiza visual próprio.

Desconhecidos, mas preservados por segurança:

- campos territoriais reaproveitados no frontmatter do mapa.

## 4. Exemplo de frontmatter

```yaml
---
width: 3415
height: 2879
scale: 500
distance: 2746
NoteIcon: none
cover: zz_media/t4.png
Community-Size: Large
Alignment:
Government: Dictatorship
type: Settlement
politics: Duke
region:
  - This area
  - Of this area
size: Small Country
population: 300,000
religion:
exports:
  - Something
imports:
  - Something Else
tags:
  - title
---
```

## 5. Estrutura interna da nota

````markdown
```leaflet
id: tribucia-map
lock: true
recenter: false
noScrollZoom: false
image: zz_media/Tribucia.png
bounds: [[0, 0], [185.7, 274.6]]
height: 1000px
width: 95%
lat: 92.85
long: 137.3
minZoom: -1.5
maxZoom: 5
defaultZoom: 2.5
zoomDelta: 0.5
unit: miles
scale: 1
darkMode: false
```

## HELP:
Hold ALT + click & drag to measure the distance between one area and the next.
````

## 6. Blocos especiais

Usa:

- bloco `leaflet`;
- imagem base `zz_media/Tribucia.png`;
- JSON do plugin para marcadores;
- links de marcadores para notas;
- tipos de marcador com cor/ícone.

## 7. Dependências técnicas

- Obsidian Leaflet Plugin
- `zz_media/Tribucia.png`
- `TRIBUCIA MAP.md`
- `.obsidian/plugins/obsidian-leaflet-plugin/data.json`
- notas linkadas por marcadores

## 8. Campos que não podem ser removidos

- `width`
- `height`
- `scale`
- `distance`
- `NoteIcon`
- `cover`
- `type`
- `tags`
- `Community-Size`
- `Government`
- `politics`
- `region`
- `size`
- `population`
- `exports`
- `imports`

## 9. Tags críticas

- `title`, observada no mapa.
- Tags das notas linkadas por marcadores continuam críticas para cor/visual fora do mapa.

## 10. Consultas relacionadas

Bloco Leaflet:

```leaflet
id: tribucia-map
image: zz_media/Tribucia.png
```

Configuração de marcadores:

```text
.obsidian/plugins/obsidian-leaflet-plugin/data.json
```

Todos os marcadores auditados usam layer:

```text
zz_media%2FTribucia.png
```

## 11. Critérios de validade

O mapa é válido se:

- o bloco Leaflet renderiza;
- `id` corresponde ao `mapMarkers.id` no JSON;
- `image` existe;
- `zz_media/Tribucia.png` existe;
- links de marcadores apontam para notas existentes;
- tipos de marcadores continuam configurados.

## 12. Riscos de migração futura

- Renomear `TRIBUCIA MAP.md` pode quebrar associação de arquivo no JSON.
- Renomear notas quebra `link` dos marcadores.
- Mover `Tribucia.png` quebra a layer.
- Alterar `id` quebra vínculo com marcadores.
- Remover campos de escala pode prejudicar leitura e medição.
