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
  - locations
  - locais
  - padronizacao
---

# Relatório — Padronização de Locations

## Status

LOTE 8 APLICADO.

Este lote padronizou a pasta `Locations/`, criou um índice operacional e ajustou consultas para evitar que tags genéricas puxem conteúdo de templates ou workflow.

## Arquivos Padronizados

| Local | Visibilidade | Observação |
|---|---|---|
| `Antiga Estrada Esquecida.md` | Mestre | Local sensível da origem de Vezemir. |
| `Fortaleza Abandonada de Avenor.md` | Mestre | Local sensível de formação de Vezemir. |
| `Leth'valora.md` | Jogadores | Vila élfica destruída, versão pública com pendências. |
| `Maré Baixa.md` | Jogadores | Região portuária pobre ligada a Varkh. |
| `Casa da Moeda de Nimalia.md` | Jogadores | Instituição econômica em revisão. |
| `Bairro dos Humanos.md` | Jogadores | Distrito racial/cultural de Nimalis. |
| `Bairro dos Elfos.md` | Jogadores | Distrito racial/cultural de Nimalis. |
| `Bairro dos Anões.md` | Jogadores | Distrito racial/cultural de Nimalis. |
| `Bairro dos Dragonborns.md` | Jogadores | Distrito racial/cultural de Nimalis. |
| `Bairro dos Forasteiros.md` | Jogadores | Região pobre e temporária. |
| `Bairro Nobre.md` | Jogadores | Área de nobreza e intriga. |
| `Mercado Central.md` | Jogadores | Comércio comum. |
| `Distrito Comercial.md` | Jogadores | Comércio especializado e conteúdo sensível. |
| `Porto de Nimalia.md` | Jogadores | Porto, carga, contrabando e rumores marítimos. |

Já estavam no padrão de lote anterior e foram preservados:

- `Nimalis.md`
- `Fortaleza de Gharok.md`
- `Ruínas de Valthor.md`

## Índice Criado

- `Locations/INDICE_DE_LOCAIS.md`

O índice separa:

- locais visíveis para jogadores;
- locais sensíveis do mestre.

## Consultas Corrigidas

| Arquivo | Ajuste |
|---|---|
| `Home.md` | Locais agora usam `FROM "Locations"` em vez de `FROM #location`. |
| `Home_Mestre.md` | DataCards de locais agora usam `FROM "Locations"`. |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | Locais em foco agora usam `FROM "Locations" OR "Territories"`. |

## Campos Padronizados

Todas as notas em `Locations/` agora possuem:

- `type`
- `campaign_status`
- `visibility`
- `spoiler_level`
- `gm_secret`
- `location`
- `territory`
- `tags`

## Regras Aplicadas

- Locais urbanos e de navegação ficam majoritariamente em `visibility: Jogadores`.
- Locais de origem sensível ficam em `visibility: Mestre`.
- Segredos e verdades completas continuam no `Estado da Campanha`.
- Tags antigas `Category/Location` foram removidas das notas padronizadas.

## Pendências

- Definir mapa interno ou pins para bairros de Nimalis.
- Definir se `Porto de Nimalia` é marítimo, fluvial ou ambos.
- Definir casas nobres, lojas recorrentes e lideranças locais.
- Decidir se `Antiga Estrada Esquecida` e `Fortaleza Abandonada de Avenor` terão versão pública futura.
- Revisar o uso de conteúdo sensível no `Distrito Comercial`.

## Próximo Lote Recomendado

Lote 9 — Territories restantes e mapas.

Objetivo: revisar territórios que ainda não foram consolidados, garantir relação correta entre `territory`, `location`, `region` e mapas, e preparar pins sem quebrar Leaflet/Dataview.
