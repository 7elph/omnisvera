---
obsidianUIMode: preview
NoteIcon: race
NoteStatus: Active
type: race
status: Ativa
campaign_status: Ativa
visibility: Jogadores
spoiler_level: light
gm_secret: false
name: Kenku
aliases:
  - Kenkus
origin: Earthropo
territory: "[[Nimalia]]"
region:
faction:
religion:
level:
danger_level:
hooks:
  - Vozes imitadas
  - Alquimia de rua
  - Presságios urbanos
rumors: []
thumbnail: zz_media/thumbnails/th_kenku.png
cover: zz_media/races/kenku.png
chapters: []
tags:
  - raca
  - race
  - kenku
---

# Kenku

> [!NOTE|clean no-i right]+ Retrato
> ![[zz_media/races/kenku.png|400]]

## Visão Geral

Kenkus são humanoides de traços corvídeos, ligados a memória sonora, imitação vocal, segredo, rumor e sobrevivência urbana.

[[Varkh Nimalis]] é o exemplo central de kenku no início da campanha.

Dentro da taxonomia de Omnisvera, Kenku funciona como raça jogável específica e também como uma referência mecânica dentro do guarda-chuva maior dos [[Antropo|antropos]].

## Presença em Omnisvera

- Varkh nasceu em [[Nimalis]].
- Kenkus podem aparecer em mercados, becos, guildas, oficinas, laboratórios improvisados e redes de informação.
- A leitura simbólica de corvos pode variar entre mau presságio, esperteza, roubo, memória e sobrevivência.

## Cultura e Relações

Kenkus funcionam muito bem em histórias de voz, testemunho, falsificação, segredo e alquimia. Nem todo kenku precisa ser criminoso ou místico.

Em [[Maré Baixa]], a capacidade de imitar vozes, reconhecer padrões e falsificar marcas pode ser ferramenta de sobrevivência, investigação ou crime.

## Mecânica Resumida

> [!NOTE]
> Base mecânica: Kenku, do suplemento Old Dragon — Novas Raças.

| Elemento | Regra de consulta |
|---|---|
| Tamanho | Médio; cerca de 1,50m |
| Peso | 40kg a 55kg |
| Maturidade | 12 anos |
| Expectativa de vida | Até cerca de 60 anos |
| Movimento base | 9m |
| Atributos | +2 Destreza, +1 Sabedoria |
| Tendência comum | Neutro ou Caótico |
| Idiomas | Lê e escreve Comum e Élfico |
| Fala | Só fala por mimetismos |
| Voo | Não voa |
| Talentos de Ladrão | Furtividade, Pungar e Escalar, seguindo progressão de Ladrão |

### Mimetismo

Kenku pode imitar sons e vozes que já ouviu. Quem escuta pode perceber a imitação com JP modificada por Sabedoria, conforme decisão do mestre.

### Falsificação

Kenkus podem falsificar escrita e artesanato usando a progressão abaixo.

| Nível | D% |
|---:|---:|
| 1 | 15 |
| 2 | 20 |
| 3 | 25 |
| 4 | 30 |
| 5 | 35 |
| 6 | 40 |
| 7 | 45 |
| 8 | 50 |
| 9 | 52 |
| 10 | 54 |
| 11 | 56 |
| 12 | 60 |
| 13 | 62 |
| 14 | 64 |
| 15 | 66 |
| 16 | 70 |
| 17 | 75 |
| 18 | 80 |
| 19 | 85 |
| 20 | 90 |

### Adaptação para Varkh

Para [[Varkh Nimalis]], mimetismo e falsificação ajudam em:

- leitura de rótulos, marcas, selos e símbolos adulterados;
- investigação de frascos e receitas;
- disfarce social em Maré Baixa;
- rastreamento de mentiras e documentos falsos;
- conexão com [[Alquimista]] sem transformar isso em magia.

## Personagens Relacionados

```dataview
TABLE status, role, location, faction
FROM "Characters"
WHERE race = "Kenku" OR contains(string(race), "Kenku")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: voz roubada, memória de frases e presença urbana inquieta.
- O que os jogadores sabem: Varkh é kenku e alquimista.
- O que manter em aberto no [[ESTADO_DA_CAMPANHA]]: vozes imitadas podem virar pista ou arma social.
- Como entra em cena: mercado, laboratório, taverna, viela, guilda, rumor.
- Ganchos: máscara de médico da peste, frascos, falsificações, Conclave dos Errantes.
- Consequências possíveis: uma frase repetida por um kenku pode incriminar, salvar ou revelar alguém.

## Pendências do Sage

- Definir se kenku é raça comum ou rara em Nimalia.
- Definir limite mecânico da imitação vocal.
