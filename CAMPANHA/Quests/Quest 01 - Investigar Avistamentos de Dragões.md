---
obsidianUIMode: preview
NoteIcon: quest
NoteStatus: Draft
type: quest
status: Rascunho
quest_status: Aberta
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
revealed_in:
created_by: Sage
name: Investigar Avistamentos de Dragões
location:
territory: "[[Nimalia]]"
faction:
  - "[[Conclave dos Errantes]]"
danger_level: Médio
hooks:
  - "[[Rumor 01 - Dragões ao Sul de Nimalia]]"
rumors:
  - "[[Rumor 01 - Dragões ao Sul de Nimalia]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail:
cover:
tags:
  - quest
  - story
  - chapter01
  - conclave-dos-errantes
---

# Quest 01 — Investigar Avistamentos de Dragões

## Gancho Público

O [[Conclave dos Errantes]] tem interesse em investigar relatos de dragões nas regiões ao sul de [[Nimalia]].

Os rumores falam de ataques a viajantes, mercadores, vilarejos e até criaturas selvagens. Por enquanto, a informação ainda é confusa demais para separar ameaça real, exagero de estrada e medo popular.

## Objetivo Conhecido

Descobrir se há de fato dragões ou criaturas dracônicas envolvidas nos ataques relatados.

## Locais Relacionados

- [[Nimalia]]
- [[Nimalis]]
- estradas ao sul do reino

## Envolvidos Conhecidos

- [[Conclave dos Errantes]]
- viajantes e mercadores que circulam pelas estradas

## Pistas Públicas

- Relatos de ataques a viajantes e mercadores.
- Histórias contraditórias sobre vilarejos ameaçados.
- Medo crescente em rotas comerciais.
- O Conclave quer informação antes de mobilizar recursos maiores.

## Rumores Relacionados

```dataview
TABLE status, visibility, location
FROM "CAMPANHA/Rumors"
WHERE contains(hooks, this.file.link) OR contains(rumors, this.file.link)
SORT file.name ASC
```

## Estado

Quest inicial em rascunho. Ainda precisa ser conectada de forma definitiva ao primeiro capítulo ou a uma frente posterior.

## Uso em Mesa

- Como os jogadores descobrem: contato do Conclave, conversa de taverna, mercador assustado ou aviso em Nimalis.
- Objetivo claro: verificar a origem dos ataques e trazer informação confiável.
- Complicação: relatos podem misturar dragões, monstros comuns, falsos testemunhos e interesses de facções.
- Recompensa: pagamento do Conclave, acesso a contatos ou reputação como investigadores.
- Consequência se ignorada: os rumores crescem, rotas comerciais ficam mais perigosas e outras facções podem agir primeiro.

## Pendências do Sage

- Confirmar se esta quest pertence ao Capítulo 01 ou a uma frente paralela.
- Definir se os avistamentos têm ligação com o [[Dragão de Colar Dourado]].
- Definir localização exata dos ataques ao sul de Nimalia.
