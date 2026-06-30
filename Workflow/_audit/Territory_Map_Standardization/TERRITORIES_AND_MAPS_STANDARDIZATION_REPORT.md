---
obsidianUIMode: preview
NoteIcon: audit
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
created_by: Codex
tags:
  - audit
  - territories
  - mapas
  - padronizacao
---

# Relatório — Padronização de Territórios e Mapas

## Status

LOTE 9 APLICADO.

Este lote consolidou a diferença entre territórios, locais e mapas oficiais.

## Estrutura Oficial

| Camada | Pasta/arquivo | Função |
|---|---|---|
| Continente | `MAPA DE EARTHROPO.md` | Mapa continental de Earthropo. |
| Reino | `MAPA DE NIMALIA.md` | Mapa do Reino de Nimalia. |
| Capital | `MAPA DE NIMALIS.md` | Mapa urbano da capital. |
| Territórios | `Territories/` | Reino, floresta regional, mar, campos amplos. |
| Locais | `Locations/` | Vila, bairro, ruína, fortaleza, estrada, vale, loja, porto. |

## Territórios Consolidados

| Arquivo | Status | Observação |
|---|---|---|
| `Territories/Nimalia.md` | Ativo | Reino dos antropos; capital em Nimalis; fronteiras em revisão. |
| `Territories/Floresta de Avenor.md` | Ativo | Região florestal fronteiriça de Nimalia. |
| `Territories/Mar da Neblina.md` | Em revisão | Região marítima e fonte de rumores. |
| `Territories/Campos de Earthropo.md` | Mestre / em revisão | Região ampla ligada à história de Raziel; sem marcador por enquanto. |

## Movidos Conceitualmente para Locations

| Antes | Depois | Motivo |
|---|---|---|
| `Territories/Vale Dourado.md` | `Locations/Vale Dourado.md` | Localização menor, não território independente. |
| `Territories/Bosque Sussurrante.md` | `Locations/Bosque Sussurrante.md` | Placeholder de local florestal, sem cânone confirmado. |

## Índice Criado

- `Territories/INDICE_DE_TERRITORIOS.md`

O índice lista territórios públicos e separa territórios de mestre.

## Mapas Oficiais

| Mapa | Escopo | Imagem | Visibilidade | Observação |
|---|---|---|---|---|
| `MAPA DE EARTHROPO.md` | Continente | `zz_media/earthropo.png` | Jogadores | Visão continental. |
| `MAPA DE NIMALIA.md` | Reino | `zz_media/mapa-de-nimalia.png` | Jogadores | Visão do reino e fronteiras em revisão. |
| `MAPA DE NIMALIS.md` | Cidade | `zz_media/mapa-de-nimalis.png` | Jogadores | Visão urbana da capital. |

## Consultas Corrigidas

| Arquivo | Ajuste |
|---|---|
| `Home_Mestre.md` | Territórios agora usam `FROM "Territories"`. |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | Exemplo de territórios atualizado para `FROM "Territories"`. |
| `Workflow/OMNISVERA_MEDIA_STANDARD.md` | Exemplo de mídia territorial atualizado para `FROM "Territories"`. |
| `Workflow/GEOGRAPHY.md` | Confirmada a estrutura de três mapas oficiais. |

## Regras Aplicadas

- `Territories/` é para regiões grandes.
- `Locations/` é para pontos onde cenas podem acontecer diretamente.
- `Vale Dourado` é local menor.
- `Bosque Sussurrante` é placeholder de local, oculto do jogador até decisão.
- `Campos de Earthropo` é território/região ampla de mestre até a lore de Raziel ser consolidada.
- Mapas oficiais são três: Earthropo, Nimalia e Nimalis.

## Pendências

- Definir fronteiras exatas de Nimalia.
- Decidir posição final de Avenor.
- Definir mapa/pins definitivos de Vale Dourado.
- Decidir se Bosque Sussurrante existe.
- Posicionar Campos de Earthropo apenas depois da revisão da lore de Raziel.
- Validar visualmente os três mapas no Obsidian/Leaflet.

## Próximo Lote Recomendado

Lote 10 — Earthropo / Story / B-Sides.

Objetivo: revisar a pasta `EARTHROPO`, garantir que capítulos públicos e B-Sides não misturem conteúdo secreto, e alinhar as notas de origem dos personagens com o modelo de Disgraceland sem carregar o tom antigo.
