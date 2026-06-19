---
NoteIcon: settlement
tags:
  - Category/Settlement
  - territory
  - earthropo
  - capital
cover: zz_media/t7.png
Alignment: Lawful Good
Government: Monarquia
reputation: civilizado
politics: Rei
leader: [[Augustus Terra Decimus]]
region: 
  - Reino Central
size: Reino
population: 450,000
religion: 
  - Igreja das Chamas
exports: 
  - Grãos, Artesanato, Magia
imports: 
  - Minérios, Madeira, Pedra de Mana
---

# NIMALIA

<h2>Overview</h2>

> [!NOTE|clean no-i right]+ ‎NIMALIA
> ![[t7.png|400]]

O coração da civilização humana. Um reino de planícies douradas e cidades muradas, governado pela [[Coroa de Nimalia]] há mais de duzentos anos.

A capital **Nimalia** é uma cidade de torres de pedra e mercados movimentados, onde a Biblioteca Real guarda os poucos registros que sobreviveram ao Cataclisma.

---

<h2>Regiões</h2>

#### Bairro dos Humanos

Lugar onde os humanos se estabeleceram na cidade.

---

#### Bairro dos Elfos

Lugar onde os elfos se estabeleceram na cidade.

---

#### Bairro dos Anões

Lugar onde os snões se estabeleceram na cidade.

---

#### Bairro dos Dragonbourns

Lugar onde os Dragonbourns se estabeleceram na cidade.

---

#### Bairro Nobre

Área de alto padrão da cidade, onde estão os nobres.

---

#### Mercado Central

Área comercial da cidade, onde estão localizados todos os produtos que se pode encontrar.

---

#### Distrito Comercial

Área com lojas especializadas onde pode se encontrar desde poções até escravos.

---

#### Bairro dos Forasteiros

Lugar onde qualquer um com pouca renda pode se estabelecer por um curto tempo. Local das favelas da cidade.

---

#### Porto de Nimalia

Lugar da cidade onde os barcos fazem sua movimentação, carga e descarga.

---

<h2>Capital: Nimalia</h2>

- **Populacao:** ~450.000
- **Governante:** [[Augustus Terra Decimus]]
- **Caracteristicas:** Biblioteca Real, Grande Templo das Chamas, Arena Divina

---

<h2>Residentes de Nimalia</h2>

  ```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "nimalia")
limit 10
```