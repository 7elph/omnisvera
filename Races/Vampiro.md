---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Draft
type: race
status: Restrita
campaign_status: Em revisão
visibility: Mestre
spoiler_level: medium
gm_secret: true
name: Vampiro
aliases:
  - Vampiros
  - Sanguinallis
origin: Desconhecida
territory:
region:
faction:
  - "[[Clã Sanguinallis]]"
religion:
level:
danger_level: Alto
hooks:
  - Sangue Antigo
  - Clã Sanguinallis
  - Linhagens vampíricas
rumors: []
thumbnail: zz_media/th_raziel.PNG
cover: zz_media/raziel.PNG
chapters: []
tags:
  - raca
  - race
  - vampiro
---

# Vampiro

## Visão Geral

Vampiro, em Omnisvera, pode funcionar como raça, condição, linhagem, maldição ou classe especial, dependendo do caso.

Para [[Raziel]], a decisão atual é tratar Vampiro como classe/personagem especial com ligação ao [[Sangue Antigo]] e ao [[Clã Sanguinallis]].

## Presença em Omnisvera

- Vampiros estão ligados a histórias antigas, sangue, linhagem e segredos.
- O [[Clã Sanguinallis]] deve ser integrado conforme a lore já conta.
- A camada pública dessa informação deve ser controlada para não revelar demais aos jogadores antes da hora.

## Cultura e Relações

Vampiros podem ser aristocratas ocultos, predadores, amaldiçoados, sobreviventes de eras antigas ou herdeiros de sangue proibido.

## Mecânica Resumida

Não copiar regras de complemento no vault. A mecânica deve ser resumida em termos próprios, com separação entre:

- classe Vampiro;
- raça/condição Vampiro;
- [[Sangue Antigo]];
- poderes específicos de Raziel.

## Personagens Relacionados

```dataview
TABLE status, role, location, faction
FROM "Characters"
WHERE race = "Vampiro" OR contains(string(race), "Vampiro") OR class = "Vampiro" OR contains(string(class), "Vampiro")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: mistério, fome, linhagem e ameaça velada.
- O que os jogadores sabem: depende do que já foi revelado sobre Raziel.
- O que apenas o mestre sabe: origem, limites e consequências do Sangue Antigo.
- Como entra em cena: sangue, pactos, clãs, ruínas, inimigos antigos.
- Ganchos: Clã Sanguinallis, Sangue Antigo, poderes de Raziel.
- Consequências possíveis: revelar demais cedo pode quebrar mistério e tensão.

## Pendências do Sage

- Definir o limite entre raça, classe e condição.
- Definir poderes permitidos no nível 1.
- Definir o que pode aparecer publicamente sobre Raziel.
