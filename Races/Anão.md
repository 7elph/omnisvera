---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Active
type: race
status: Ativa
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
name: Anão
aliases:
  - Anões
origin: Earthropo
territory: "[[Fortaleza de Gharok]]"
region: Norte/Nordeste de Nimalia
faction:
religion:
level:
danger_level:
hooks:
  - Reinos anões ao norte e nordeste
  - Fortalezas antigas e ruínas subterrâneas
rumors: []
thumbnail: zz_media/thumbnails/th_anao.png
cover: zz_media/thumbnails/th_anao.png
chapters: []
tags:
  - raca
  - race
  - anao
---

# Anão

> [!NOTE|clean no-i right]+ Retrato
> ![[zz_media/races/anao.png|400]]

## Visão Geral

Anões são povos ligados a montanhas, fortalezas, metalurgia, memória de clãs e construções antigas.

Em Omnisvera, o reino anão ainda será revelado aos poucos e deve ficar ao norte ou nordeste do mapa, próximo a regiões montanhosas e vulcânicas.

## Presença em Omnisvera

- [[Fortaleza de Gharok]] é uma antiga fortaleza anã.
- O reino anão futuro deve se conectar a montanhas e estruturas antigas.
- [[Nimalis]] possui um Bairro dos Anões.

## Cultura e Relações

Anões podem ser tratados como povo de tradição, técnica, juramentos e memória arquitetônica. Nem todo anão precisa estar ligado diretamente a minas ou guerra.

A rivalidade com elfos pode ser usada como tensão cultural antiga, mas não precisa definir todos os personagens.

## Mecânica de Consulta

| Elemento | Regra de consulta |
|---|---|
| Tendência comum | Geralmente ordeiro |
| Altura comum | 1,30m a 1,50m |
| Peso comum | 50kg a 70kg |
| Maturidade | Cerca de 70 anos |
| Expectativa de vida | Cerca de 350 anos |
| Idiomas iniciais | Anão e comum |
| Idiomas adicionais | Por Inteligência alta; povos aliados ou inimigos como orc, gigante e goblin |
| Atributos | +2 Constituição, -2 Carisma |
| Visão no escuro | 15m |
| Mineradores | Detecta desníveis, fossos ou armadilhas de pedra com resultado 1-2 em 1d6 |
| Movimento base | 6m |

O vault não deve transformar todos os anões em mineiros ou soldados. A mecânica serve à mesa; a cultura de Omnisvera ainda será expandida.

## Personagens Relacionados

```dataview
TABLE status, role, location, faction
FROM "Characters"
WHERE race = "Anão" OR contains(string(race), "Anão") OR contains(string(race), "Anões")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: povo de fortalezas, clãs e obras antigas.
- O que os jogadores sabem: Gharok tem origem anã.
- O que manter em aberto no [[ESTADO_DA_CAMPANHA]]: antigas obras anãs podem guardar segredos de eras anteriores.
- Como entra em cena: ruínas, escudos, artesãos, guardas, fortalezas.
- Ganchos: Gharok, Muralha de Dorn, rotas do norte.
- Consequências possíveis: mexer em ruínas anãs pode envolver clãs ou reinos ainda não apresentados.

## Pendências do Sage

- Definir nome do reino anão.
- Definir relação entre Gharok e o reino anão atual.
