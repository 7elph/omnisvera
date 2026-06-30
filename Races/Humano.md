---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Active
type: race
status: Ativa
campaign_status: Ativa
visibility: Jogadores
spoiler_level: none
gm_secret: false
name: Humano
aliases:
  - Humanos
origin: Earthropo
territory:
region:
faction:
religion:
level:
danger_level:
hooks:
  - Povos humanos espalhados por Earthropo
  - Presença importante, mas não majoritária em Nimalia
rumors: []
thumbnail: zz_media/earthropo.png
cover: zz_media/earthropo.png
chapters: []
tags:
  - raca
  - race
  - humano
---

# Humano

## Visão Geral

Humanos existem em Omnisvera como uma das raças centrais de Earthropo, mas não são automaticamente a maioria em todos os reinos.

Em [[Nimalia]], os antropos são predominantes. Humanos aparecem como comunidades estabelecidas, viajantes, nobres, aventureiros, mercadores, religiosos e povos de fronteira.

## Presença em Omnisvera

- [[Nimalis]] possui um Bairro dos Humanos.
- Humanos podem estar ligados a vilas, rotas comerciais, templos e regiões de fronteira.
- [[Mira Valen]] e o antigo chefe de [[Leth'valora]] são exemplos importantes de presença humana em comunidades não exclusivamente humanas.

## Cultura e Relações

Humanos são versáteis e politicamente adaptáveis. Em alguns lugares, são maioria local; em outros, uma comunidade entre muitas.

## Mecânica Resumida

Usar a base mecânica de humano do sistema adotado, com ajustes narrativos próprios quando necessário. Não reproduzir texto integral de regras no vault.

## Personagens Relacionados

```dataview
TABLE status, role, location, faction
FROM "Characters"
WHERE race = "Humano" OR race = "Humana" OR contains(string(race), "Humano") OR contains(string(race), "Humana")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: raça comum, mas não dominante em todos os contextos.
- O que os jogadores sabem: humanos vivem em Nimalia e em muitas regiões de Earthropo.
- O que apenas o mestre sabe: antigas linhagens humanas podem ter laços com ruínas, guerras ou pactos esquecidos.
- Como entra em cena: vilas, templos, guardas, nobres, mercadores e aventureiros.
- Ganchos: fronteira cultural, famílias antigas, disputa por posição em reinos não humanos.
- Consequências possíveis: conflitos humanos locais podem afetar relações raciais e políticas.

## Pendências do Sage

- Definir regiões onde humanos são maioria.
- Definir se há reinos humanos específicos fora de Nimalia.
