---
obsidianUIMode: preview
NoteIcon: location
NoteStatus: Active
status: Ativa
visibility: shared
territory: "[[Nimalia]]"
district: Capital
leader: "[[Augustus Terra Decimus]]"
population: 120000
info: Capital murada e principal ponto de encontro das rotas de Nimalia.
cover: zz_media/nimalia.png
tags:
  - location
  - capital
  - nimalia
  - earthropo
---

# Nimalis

> [!NOTE|clean no-i right]+ Nimalis
> ![[nimalia.png|400]]

Nimalis é a capital do Reino de [[Nimalia]] e sede da [[Coroa de Nimalia]]. A cidade cresceu onde rios navegáveis, estradas e rotas mercantis se encontram, tornando-se o principal ponto de partida para viajantes no centro de Earthropo.

Sua população de trabalho é de aproximadamente **120.000 habitantes**.

## Distritos

### Cidadela Real

Centro administrativo, religioso e cerimonial. Abriga o palácio, arquivos, salões da Coroa e parte das instalações da Guarda Real.

### Bairro dos Humanos

Um dos bairros mais antigos fora da cidadela, conhecido por hospedarias, oficinas, pátios de caravana e famílias vindas de diferentes regiões.

### Bairro Élfico

Comunidade de comerciantes, artesãos, estudiosos e viajantes élficos. Não representa o reino élfico nem fala por todos os elfos de Earthropo.

### Bairro Anão

Área de forjas, armazéns de pedra, metalurgia e casas comerciais ligadas às rotas do norte.

### Bairro Dracônico

Distrito associado a famílias dragonborn e outros povos de linhagem dracônica. O nome pode mudar conforme a cultura dragonborn for consolidada.

### Bairro Nobre

Residências de famílias influentes, embaixadas, jardins murados e casas vinculadas à administração do reino.

### Mercado Central

Praças, feiras e entrepostos onde produtos comuns chegam diariamente. É o lugar mais fácil para encontrar rumores, trabalho e viajantes.

### Distrito dos Ofícios

Lojas especializadas, alquimistas, escribas, armeiros, casas de câmbio e serviços que exigem licença ou conhecimento técnico.

### Bairro dos Forasteiros

Hospedarias baratas, cortiços e pátios para quem chega sem contatos ou pretende permanecer pouco tempo. É movimentado, precário e diverso.

### Porto Real

Docas oficiais, alfândega e grandes armazéns. Ao sul e fora de sua parte mais controlada começa [[Maré Baixa]].

### [[Maré Baixa]]

Distrito portuário de passarelas, pequenos ofícios, contrabando e redes comunitárias. É a origem de [[Players/Characters/Varkh Nimalis]].

## Residentes

```dataview
TABLE status, role, faction, occupation
FROM "Characters"
WHERE contains(string(location), this.file.name)
SORT file.name ASC
```

> [!gm]- Preparação
> [[Players/Characters/Raziel]] encontrará o grupo em Nimalis. A cena e o distrito exatos ainda serão definidos no capítulo inicial.
