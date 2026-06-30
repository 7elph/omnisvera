---
obsidianUIMode: preview
NoteIcon: workflow
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
status: Aplicado
tags:
  - workflow
  - audit
  - padronizacao
  - geografia
---

# Relatório de Padronização — Geografia Jogável

Status: aplicado em 2026-06-29.

## Objetivo

Padronizar o segundo lote da fila do vault: geografia jogável ligada ao início da campanha.

Este lote não renomeia pastas, não cria mapa novo, não remove mídia e não resolve toda a cartografia de Earthropo. A intenção é deixar as notas centrais coerentes, consultáveis por Dataview/DataCards e seguras para uso com jogadores.

## Escopo Aplicado

| nota | tipo | status |
|---|---|---|
| `Territories/Nimalia.md` | `territory` | padronizada |
| `Locations/Nimalis.md` | `location` | padronizada |
| `Territories/Floresta de Avenor.md` | `territory` | padronizada |
| `Territories/Mar da Neblina.md` | `territory` | padronizada |
| `Locations/Ruínas de Valthor.md` | `location` | padronizada |
| `Locations/Fortaleza de Gharok.md` | `location` | padronizada |

## Critério Aplicado

- `territory` foi usado para áreas amplas: reino, floresta regional e região marítima.
- `location` foi usado para pontos jogáveis: capital, ruínas e fortaleza.
- `visibility: Jogadores`, `spoiler_level: light` e `gm_secret: false` foram usados como padrão de geografia pública.
- Detalhes pesados de mestre foram evitados nas notas geográficas.
- Informações secretas devem continuar centralizadas no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]] ou em notas explicitamente de mestre.
- Tags Omnisvera foram priorizadas.
- A tag `location` foi mantida como ponte temporária para DataCards/Home.
- A tag `territory` não foi usada nas notas novas/padronizadas; o padrão operacional é `territorio`.

## Ajustes por Nota

### Reino de Nimalia

- Convertido para `type: territory`.
- Reforçado como reino dos antropos, não cidade.
- Confirmado que [[Nimalis]] é a capital.
- Adicionadas fronteiras/regiões conhecidas:
  - [[Floresta de Avenor]];
  - [[Ruínas de Valthor]];
  - [[Fortaleza de Gharok]];
  - [[Vale Dourado]].
- Convertidos títulos HTML para Markdown.
- Adicionado bloco `Uso em Mesa`.

### Nimalis

- Convertida para `type: location`.
- Mantida como capital do [[Nimalia|Reino de Nimalia]].
- Preservados os bairros e distritos existentes.
- Adicionadas relações com Coroa, Nobreza, Guilda dos Mercadores e Maré Baixa.
- Adicionado bloco `Uso em Mesa`.

### Floresta de Avenor

- Mantida como `type: territory`, porque funciona como região florestal ampla.
- Reforçada como fronteira próxima de Nimalia.
- Mantida relação com [[Leth'valora]], [[Vezemir]], [[Mira Valen]] e o [[Dragão de Colar Dourado]].
- Rascunhos internos foram preservados como não confirmados.
- Adicionado bloco `Uso em Mesa`.

### Mar da Neblina

- Padronizado como `type: territory`, subtendido como região marítima.
- Mantido como lore em revisão.
- Adicionadas relações com rotas comerciais, [[Porto de Nimalia]], [[Nimalis]] e [[Guilda dos Mercadores]].
- Adicionado bloco de aparições/menções e `Uso em Mesa`.

### Ruínas de Valthor

- Convertida para `type: location`.
- Mantida como ruína antiga ao sudeste de Nimalia.
- Informações explícitas demais sobre bastidores de Raziel foram suavizadas para versão pública.
- Relação com [[Raziel]] e [[Clã Sanguinallis]] foi mantida como gancho a revelar, não como exposição completa.
- Adicionado bloco `Uso em Mesa`.

### Fortaleza de Gharok

- Convertida para `type: location`.
- Mantida como antiga fortaleza anã ao norte de Nimalia.
- Informações explícitas demais sobre traição e domínio vampírico foram suavizadas para versão pública.
- Relação com [[Raziel]], [[Clã Sanguinallis]] e futuro reino anão foi mantida como pendência/gatilho de mesa.
- Adicionado bloco `Uso em Mesa`.

## Pendências do Sage

- Definir fronteiras exatas do [[Nimalia|Reino de Nimalia]].
- Decidir se [[Floresta de Avenor]] será apenas região fronteiriça ou também caminho para o futuro reino élfico.
- Definir posição exata do [[Mar da Neblina]].
- Definir se [[Ruínas de Valthor]] terá mapa/dungeon própria.
- Definir estado atual da [[Fortaleza de Gharok]].
- Decidir quando mover informações completas de Gharok/Valthor para o Estado da Campanha, caso ainda não estejam suficientemente centralizadas.

## Próximo Lote Recomendado

Seguir a fila:

1. Validar e commitar personagens + geografia, se o Sage quiser congelar esta etapa.
2. Padronizar facções ativas:
   - [[Coroa de Nimalia]];
   - [[Guarda Real de Nimalia]];
   - [[Conclave dos Errantes]];
   - [[Guilda dos Mercadores]];
   - [[Guardiões do Véu Cinzento]];
   - [[Clã Sanguinallis]];
   - [[Sentinelas de Leth'valora]];
   - [[Nobreza de Nimalia]].
