---
NoteIcon: settlement
tags:
  - Category/Settlement
  - territorio
  - earthropo
  - kingdom
  - antropo
cover: zz_media/mapa-de-nimalia.png
Alignment: Lawful Good
Government: Monarquia
reputation: civilizado
politics: Rei
leader: [[Augustus Terra Decimus]]
region: 
  - Região Central de Earthropo
size: Reino
population:
religion: 
  - Igreja das Chamas
exports: 
  - Grãos, Artesanato, Magia
imports: 
  - Minérios, Madeira, Pedra de Mana
---

# REINO DE NIMALIA

<h2>Overview</h2>

> [!NOTE|clean no-i right]+ ‎REINO DE NIMALIA
> ![[mapa-de-nimalia.png|400]]

Nimalia é o reino dos antropos apresentado até agora em Earthropo. Reúne diferentes povos antropo sob a autoridade de [[Augustus Terra Decimus]] e da [[Coroa de Nimalia]].

[[Nimalis]] é a capital do reino: uma grande cidade de torres de pedra, bairros densos e mercados movimentados, onde antropos convivem com comunidades humanas, élficas, anãs, dragonborns e estrangeiras.

Como referência inicial de cartografia, o reino ocupa as terras centrais ao redor da capital. Sua fronteira com a [[Floresta de Avenor]] está confirmada em conceito. Ao sudeste ficam as [[Ruínas de Valthor]], ao norte fica a [[Fortaleza de Gharok]] e [[Vale Dourado]] permanece como localização menor associada ao interior do reino.

---

<h2>Capital do Reino</h2>

Os distritos da capital estão documentados em [[Nimalis]]. Esta nota mantém a visão de reino: fronteiras, governo, economia, povos e relações territoriais.

---

<h2>Dados do Reino</h2>

- **Governante:** [[Augustus Terra Decimus]]
- **Capital:** [[Nimalis]]
- **População da capital:** aproximadamente 450.000 habitantes
- **Características da capital:** Biblioteca Real, Grande Templo das Chamas, Arena Divina
- **Mapa do reino:** [[MAPA DE NIMALIA]]
- **Mapa da capital:** [[MAPA DE NIMALIS]]

---

<h2>Residentes do Reino de Nimalia</h2>

  ```dataview
table location, status, faction
from "Characters"
where contains(lower(string(location)), "nimalia")
limit 10
```
