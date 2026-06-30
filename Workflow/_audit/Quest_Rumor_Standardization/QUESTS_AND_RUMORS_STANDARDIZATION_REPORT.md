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
  - quest
  - rumor
  - padronizacao
---

# Relatório — Padronização de Quests e Rumores

## Status

LOTE 7 APLICADO COMO BASE INICIAL.

Este lote organizou a estrutura de quests e rumores para impedir que templates apareçam em consultas operacionais e para separar informações públicas de bastidores do mestre.

## Decisão Estrutural

| Item | Decisão |
|---|---|
| Quests reais | Ficam em `CAMPANHA/Quests`. |
| Rumores reais | Ficam em `CAMPANHA/Rumors`. |
| Templates | Ficam em `Templates/RPG`, sem conteúdo específico de campanha. |
| Segredos do mestre | Devem ficar em `CAMPANHA/ESTADO_DA_CAMPANHA.md`. |
| Consultas operacionais | Devem usar pastas reais, não apenas `FROM #quest` ou `FROM #rumor`. |

## Notas Criadas

| Arquivo | Função | Visibilidade | Observação |
|---|---|---|---|
| `CAMPANHA/Quests/Quest 01 - Investigar Avistamentos de Dragões.md` | Primeira quest real | Jogadores | Criada a partir do conteúdo que estava em `Templates/RPG/Quest 1.md`. |
| `CAMPANHA/Rumors/Rumor 01 - Dragões ao Sul de Nimalia.md` | Primeiro rumor real | Jogadores | Criada a partir do conteúdo que estava em `Templates/RPG/Rumor 1.md`. |

## Templates Atualizados

| Template | Ajuste |
|---|---|
| `Templates/RPG/Quest.md` | Virou modelo genérico, seguro para conteúdo de jogadores. |
| `Templates/RPG/Rumor.md` | Virou modelo genérico, sem “verdade completa” dentro da nota pública. |
| `Templates/RPG/Quest 1.md` | Removido de `Templates`; conteúdo virou quest real. |
| `Templates/RPG/Rumor 1.md` | Removido de `Templates`; conteúdo virou rumor real. |

## Consultas Corrigidas

| Arquivo | Ajuste |
|---|---|
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | `FROM #quest/#rumor` substituído por pastas reais. |
| `EARTHROPO/01 - Ecos do Mundo Perdido.md` | Consultas públicas agora usam pastas reais e filtros de visibilidade. |
| `Templates/RPG/Story.md` | Template atualizado para consultar `CAMPANHA/Quests` e `CAMPANHA/Rumors`. |

## Regra de Segurança

Quests e rumores podem aparecer para jogadores quando tiverem:

```dataview
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
```

Bastidores, verdades ocultas, causas reais, antagonistas secretos e consequências não reveladas devem ficar no `Estado da Campanha`.

## Pendências

- Confirmar se a quest de dragões entra no Capítulo 01 ou em frente paralela.
- Definir se os avistamentos têm relação real com o [[Dragão de Colar Dourado]].
- Criar quests/rumores futuros a partir dos ganchos já listados:
  - remédios falsos;
  - tremor na estrada;
  - símbolo antigo nos frascos;
  - rumor vindo do [[Mar da Neblina]];
  - investigação do [[Conclave dos Errantes]].

## Próximo Lote Recomendado

Lote 8 — Locations restantes.

Objetivo: padronizar os locais menores de [[Nimalis]], [[Maré Baixa]], bairros, mercados e pontos jogáveis que ainda estão mais crus.
