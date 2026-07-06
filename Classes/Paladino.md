---
obsidianUIMode: preview
NoteIcon: class
NoteStatus: Draft
type: class
subtype: specialization
status: Especialização em revisão
rules_status: Especialização de Guerreiro / adaptação de mesa
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
created_by: Sage
name: Paladino
aliases:
  - Paladino Real
  - Paladino da Coroa
system: Old Dragon / Omnisvera
class_group: Especialização de Guerreiro
parent_class: "[[Guerreiro]]"
primary_attribute:
level:
danger_level: Médio
thumbnail:
cover:
chapters: []
tags:
  - classe
  - paladino
  - class
---

# Paladino

> [!NOTE]
> Paladino é uma especialização de [[Guerreiro]] ligada a causa, ordem, proteção e combate contra forças caóticas.

## Visão Geral

Paladinos dedicam sua força marcial a uma causa. Em Omnisvera, essa causa pode estar ligada à Coroa, à fé, à proteção de inocentes, à defesa de uma ordem política ou a um juramento pessoal.

[[Augustus Terra Decimus]] e [[General Cassian Valerius]] são referências atuais de paladinos no vault.

## Base Mecânica

| Elemento | Regra de consulta |
|---|---|
| Classe-base | [[Guerreiro]] |
| Requisito narrativo | dedicação a uma causa |
| Alinhamento base | ordeiro |
| Tema | ordem contra caos |
| Atributo importante | Carisma |

## Progressão da Especialização

| Nível | Benefício |
|---:|---|
| 5 | Detecta caos a 1 km de distância se estiver concentrado; recebe +1 para cada 3 pontos de Carisma em ataques contra criaturas caóticas |
| 8 | Causa +1d6 de dano para cada 3 pontos de Carisma contra criaturas caóticas; emana aura de proteção contra o caos de 3m; criaturas caóticas na área recebem penalidade de -1 para cada 3 pontos de Carisma em jogadas e CA |
| 16 | A aura de proteção contra o caos também irradia em torno de aliados ordeiros, usando o Carisma do paladino como parâmetro |

## Restrições

- Se usar item mágico caótico, mesmo sem saber, perde 2 níveis e não pode usar poderes enquanto estiver portando o item.
- Se deixar de ser ordeiro, perde 3 níveis e todos os poderes até retornar ao alinhamento apropriado.

## Uso em Omnisvera

- Pode representar cavaleiros sagrados, campeões reais, inquisidores, guardiões de templo ou oficiais juramentados.
- Não precisa revelar segredos da Coroa ou da Igreja na nota pública.
- Em NPCs, pode funcionar como linguagem de autoridade e ameaça institucional.

## Personagens Relacionados

```dataview
TABLE status, race, location, faction
FROM "Characters"
WHERE class = "Paladino" OR class = this.file.link OR contains(string(role), "paladino")
SORT file.name ASC
```

## Pendências

- Definir se Paladino será opção jogável ou apenas especialização de NPCs no início da campanha.
- Definir relação pública entre paladinos, [[Igreja das Chamas]], [[Coroa de Nimalia]] e [[Guarda Real de Nimalia]].
