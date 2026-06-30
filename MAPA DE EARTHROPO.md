---
width: 3415
height: 2879
scale: 500
distance: 2746
NoteIcon: none
NoteStatus: Active
obsidianUIMode: preview
cover: zz_media/earthropo.png
Community-Size: Continental
Alignment:
Government: Diversos
type: map
map_scope: continent
status: Ativo
campaign_status: Ativo
politics: Diversos reinos
region:
  - Earthropo
size: Continente
population:
religion:
exports:
imports:
visibility: Jogadores
spoiler_level: light
gm_secret: false
tags:
  - title
  - map
  - earthropo
  - territorio
---

# MAPA DE EARTHROPO

Mapa oficial do continente de [[EARTHROPO/EARTHROPO|Earthropo]].

Esta camada mostra a escala continental. Fronteiras finas, reinos futuros e coordenadas exatas ainda podem ser refinados.

```leaflet
id: earthropo-map
lock: true
recenter: false
noScrollZoom: false
image: zz_media/earthropo.png
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
marker: Territory, 105, 128, [[Nimalia]]
marker: Location, 91, 137, [[Nimalis]]
marker: Territory, 108, 169, [[Floresta de Avenor]]
marker: Location, 99, 182, [[Leth'valora]]
marker: Location, 78, 199, [[Ruínas de Valthor]]
marker: Location, 63, 132, [[Fortaleza de Gharok]]
```

## Marcadores

Esta camada fixa apenas lugares com existência e região aproximada sustentadas pelo cânone:

- [[Nimalia]] ocupa provisoriamente a região central do continente.
- [[Nimalis]] corresponde à capital do Reino de Nimalia.
- A [[Floresta de Avenor]] fica a leste/nordeste da capital e faz fronteira com o reino.
- As ruínas de [[Leth'valora]] ficam dentro de Avenor.
- As [[Ruínas de Valthor]] ficam no sudeste de Earthropo.
- A [[Fortaleza de Gharok]] fica ao norte de Nimalia, na região associada ao futuro reino anão.

## Estado cartográfico

| Elemento | Estado |
|:--|:--|
| Posição geral de Nimalia | Provisória |
| Nimalis como capital | Confirmado |
| Fronteira Nimalia–Avenor | Confirmada; traçado exato em aberto |
| Leth'valora dentro de Avenor | Confirmado; coordenada aproximada |
| Valthor no sudeste | Confirmado; coordenada aproximada |
| Gharok | Norte de Nimalia; coordenada aproximada |
| Reino élfico | Sudoeste; nome e fronteira em aberto |
| Reino anão | Nordeste; nome e fronteira em aberto |
| Reino dos dragonborns | Noroeste; nome e fronteira em aberto |
| Demais fronteiras | Não posicionadas |

As coordenadas podem ser refinadas sem alterar o cânone. Consulte [[Workflow/GEOGRAPHY|Registro Geográfico de Earthropo]] antes de criar outros marcadores.

## Mapas relacionados

- [[MAPA DE EARTHROPO]] representa o continente.
- [[MAPA DE NIMALIA]] representa o reino em foco.
- [[MAPA DE NIMALIS]] representa a capital.

## HELP:

Hold ALT + click & drag to measure the distance between one area and the next.
