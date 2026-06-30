---
obsidianUIMode: preview
NoteIcon: territory
NoteStatus: Active
type: territory
status: Ativo
campaign_status: Ativo
visibility: Jogadores
spoiler_level: light
gm_secret: false
thumbnail: zz_media/mapa-de-nimalia.png
cover: zz_media/mapa-de-nimalia.png
location: "[[Nimalis]]"
territory: "[[EARTHROPO/EARTHROPO|Earthropo]]"
info: Reino dos antropos em Earthropo, governado por Augustus Terra Decimus.
description: Reino dos antropos, tendo Nimalis como capital e fronteiras ainda em consolidação.
Alignment: Lawful Good
Government: Monarquia
reputation: civilizado
politics: Coroa de Nimalia
leader: "[[Augustus Terra Decimus]]"
region: 
  - Região central de Earthropo
size: Reino
population:
religion: 
  - Igreja das Chamas
exports: 
  - Grãos
  - Artesanato
  - Magia
imports: 
  - Minérios
  - Madeira
  - Pedra de Mana
tags:
  - territorio
  - reino
  - reino-de-nimalia
  - nimalia
  - antropo
  - earthropo
---

# Reino de Nimalia

> [!world]- SINOPSE PÚBLICA
> Nimalia é o reino dos antropos em Earthropo: um centro de comércio, coroa, rotas e tensões de fronteira. Sua capital é [[Nimalis]], uma cidade enorme e desigual governada pelo rei soberano [[Augustus Terra Decimus]].

## Visão Geral

> [!NOTE|clean no-i right]+ Reino de Nimalia
> ![[mapa-de-nimalia.png|400]]

Nimalia é o reino dos antropos apresentado até agora em Earthropo. Reúne diferentes povos antropo sob a autoridade de [[Augustus Terra Decimus]] e da [[Coroa de Nimalia]].

[[Nimalis]] é a capital do reino: uma grande cidade de torres de pedra, bairros densos e mercados movimentados, onde antropos convivem com comunidades humanas, élficas, anãs, dragonborns e estrangeiras.

Como referência inicial de cartografia, o reino ocupa as terras centrais ao redor da capital. Sua fronteira com a [[Floresta de Avenor]] está confirmada em conceito. Ao sudeste ficam as [[Ruínas de Valthor]], ao norte fica a [[Fortaleza de Gharok]] e [[Vale Dourado]] permanece como localização menor associada ao interior do reino.

---

## Regra Geográfica

| elemento | classificação |
|---|---|
| [[EARTHROPO/EARTHROPO|Earthropo]] | continente |
| Reino de Nimalia | território / reino |
| [[Nimalis]] | local / capital |
| [[Floresta de Avenor]] | território / região florestal fronteiriça |
| [[Ruínas de Valthor]] | local / ruínas de antigo reino ao sudeste |
| [[Fortaleza de Gharok]] | local / fortaleza anã antiga ao norte |
| [[Vale Dourado]] | local / vale, vila ou região menor |

---

## Capital do Reino

Os distritos da capital estão documentados em [[Nimalis]]. Esta nota mantém a visão de reino: fronteiras, governo, economia, povos e relações territoriais.

---

## Dados do Reino

- **Governante:** [[Augustus Terra Decimus]]
- **Capital:** [[Nimalis]]
- **População da capital:** aproximadamente 450.000 habitantes
- **Características da capital:** Biblioteca Real, Grande Templo das Chamas, Arena Divina
- **Mapa do reino:** [[MAPA DE NIMALIA]]
- **Mapa da capital:** [[MAPA DE NIMALIS]]

---

## Fronteiras e Regiões Conhecidas

- [[Nimalis]] — capital do reino.
- [[Floresta de Avenor]] — região florestal próxima e fronteiriça.
- [[Ruínas de Valthor]] — ruínas antigas ao sudeste.
- [[Fortaleza de Gharok]] — antiga fortaleza anã ao norte, associada à região do futuro reino anão.
- [[Vale Dourado]] — localização menor do interior, ainda em revisão.

## Relações Políticas e Territoriais

- [[Coroa de Nimalia]] — poder central do reino.
- [[Nobreza de Nimalia]] — casas nobres, privilégios e interesses políticos.
- [[Guilda dos Mercadores]] — força econômica relevante em Nimalia e em Earthropo.
- [[Guarda Real de Nimalia]] — braço de segurança e ordem ligado à Coroa.
- [[Igreja das Chamas]] — religião pública importante, ainda em revisão política.

## Uso em Mesa

- Como apresentar: o reino estável que dá contexto político inicial à campanha.
- O que os jogadores sabem: Nimalia é o reino dos antropos, governado por [[Augustus Terra Decimus]], com [[Nimalis]] como capital.
- Como entra em cena: por rotas comerciais, patrulhas da Coroa, rumores urbanos, fronteiras e conflitos próximos.
- Ganchos: fronteiras indefinidas, pressão de facções, rumores de ruínas e circulação de remédios falsos.

## Pendências do Sage

- Definir fronteiras exatas de Nimalia no mapa.
- Decidir quais regiões vizinhas pertencem formalmente ao reino e quais apenas fazem fronteira.
- Revisar religião oficial e relação com a Igreja das Chamas.

## Residentes do Reino de Nimalia

```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "nimalia") OR contains(lower(string(territory)), "nimalia") OR contains(lower(string(location)), "nimalis")
limit 10
```
