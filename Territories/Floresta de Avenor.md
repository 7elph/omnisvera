---
obsidianUIMode: preview
NoteIcon: territory
NoteStatus: Active
type: territory
visibility: Jogadores
spoiler_level: light
gm_secret: false
status: Ativa
campaign_status: Em jogo
thumbnail: zz_media/avenor.png
cover: zz_media/avenor.png
location:
territory: "[[EARTHROPO/EARTHROPO|Earthropo]]"
info: Região florestal próxima ao Reino de Nimalia, ligada a Leth'valora e à história de Vezemir.
description: Floresta regional na fronteira de Nimalia, marcada por trilhas antigas, ruínas e segredos ainda em revisão.
Alignment: Neutral  
Government: Nenhum  
reputation: misteriosa  
politics: Nenhum  
leader:  
region:
  - Fronteira do Reino de Nimalia
size: Floresta  
population: Desconhecida  
religion:
exports:
  - Madeira  
  - Ervas Medicinais 
  - Peles
  - Cogumelos Raros  
imports:
  - Ferramentas 
  - Suprimentos
chapters: []
tags:
  - territorio
  - floresta
  - avenor
  - earthropo

---

# Floresta de Avenor

> [!world]- SINOPSE PÚBLICA
> Avenor é uma região florestal fronteiriça ao [[Nimalia|Reino de Nimalia]], cheia de trilhas antigas, ruínas cobertas pela mata e memórias ligadas à queda de [[Leth'valora]].

## Visão Geral

> [!NOTE|clean no-i right]+ Floresta de Avenor
> ![[avenor.png|400]]

Uma grande floresta das terras centrais de Earthropo. No mapa de trabalho, ocupa a região florestal próxima à [[Nimalis]], estendendo-se ao longo da fronteira do Reino de [[Nimalia]].

Avenor é conhecida por suas trilhas esquecidas, ruínas cobertas pela vegetação e pela enorme quantidade de criaturas selvagens que habitam suas profundezas. Caçadores, aventureiros e eremitas frequentemente atravessam a floresta, mas poucos conhecem seus verdadeiros segredos.

Em uma de suas regiões encontram-se as ruínas de [[Leth'valora]], uma pequena vila élfica que era habitada por elfos que viviam fora do reino élfico ainda não apresentado.

Foi nas estradas abandonadas de Avenor que o meio-elfo [[Vezemir]] foi encontrado ainda bebê por [[Elarion Vaelthor]].

---

## Relações Territoriais

- Faz fronteira com o [[Nimalia|Reino de Nimalia]].
- Contém ou abriga caminhos para [[Leth'valora]].
- Pode servir como região de contato futuro com povos élficos.
- É uma das regiões em foco para histórias ligadas a [[Vezemir]], [[Mira Valen]] e ao [[Dragão de Colar Dourado]].

## Regra de Cânone

- Avenor não é o reino élfico.
- [[Leth'valora]] era uma vila pequena dentro da região de Avenor.
- O futuro reino élfico pode ficar em Avenor, além dela ou conectado a ela, mas isso ainda não está decidido.
- Avenor faz fronteira com Nimalia, mas não deve ser tratada automaticamente como parte do reino.

## Locais Relacionados

- [[Leth'valora]]
- [[Antiga Estrada Esquecida]]
- [[Fortaleza Abandonada de Avenor]]
- [[Bosque Sussurrante]]

## Rascunhos de Regiões Internas

> [!warning] Nomes não confirmados
> Os lugares abaixo foram preservados de rascunhos anteriores. Nenhum deles deve receber nota própria, marcador ou peso de cânone até aprovação explícita.

#### Bosque das Névoas

Uma região constantemente coberta por névoa densa. Viajantes costumam relatar sons estranhos vindos entre as árvores.

---

#### Estrada Esquecida

Antiga rota comercial abandonada há séculos. Hoje está tomada pela vegetação e por ruínas do velho mundo.

Foi próximo a essa estrada que [[Vezemir]] foi encontrado quando ainda era uma criança.

---

#### Lago Espelhado

Um lago de águas cristalinas que reflete o céu com perfeição. Muitas histórias locais afirmam que espíritos observam os viajantes através de sua superfície.

---

#### Bosque de Mira

Uma pequena clareira próxima a uma antiga vila de caçadores.

Foi nessa região que [[Mira Valen]] encontrou [[Vezemir]] pela primeira vez, iniciando a amizade que mudaria o destino de ambos.

---

#### Ruínas de Arkenfall

Vestígios de uma fortificação esquecida pelas guerras antigas. Pouco se sabe sobre seus antigos habitantes.

Exploradores afirmam que túneis subterrâneos ainda existem sob as ruínas.


---

## Uso em Mesa

- Como apresentar: floresta de fronteira, viva e perigosa, mas ainda próxima o suficiente de Nimalia para afetar a campanha inicial.
- O que os jogadores sabem: Avenor contém trilhas antigas, ruínas e histórias ligadas à queda de [[Leth'valora]].
- Como entra em cena: por viagem, investigação, rastreamento, perseguição, encontros com criaturas e pistas sobre o passado.
- Ganchos: ruínas cobertas pela mata, fronteira com Nimalia, presença de sentinelas antigas e rumores élficos.

## Pendências do Sage

- Confirmar posição final de Avenor no mapa.
- Definir se o futuro reino élfico ficará dentro, próximo ou além de Avenor.
- Revisar quais rascunhos internos viram locais reais.

## Residentes Notáveis

```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "leth'valora")
limit 10
```
