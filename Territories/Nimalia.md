---
obsidianUIMode: preview
NoteIcon: settlement
NoteStatus: Active
status: Ativo
visibility: shared
type: Reino
capital: "[[Nimalis]]"
leader: "[[Augustus Terra Decimus]]"
government: Monarquia
region: Bacia central de Earthropo
population: 750000
religion:
  - "[[Igreja das Chamas]]"
exports:
  - Grãos
  - Artesanato
  - Equipamentos
imports:
  - Minérios
  - Madeira
  - Pedra de Mana
cover: zz_media/ui/card-nimalia.webp
tags:
  - territory
  - earthropo
  - kingdom
  - beastfolk
  - antropo
---

# Reino de Nimalia

> [!NOTE|clean no-i right]+ Reino de Nimalia
> ![[zz_media/ui/card-nimalia.webp|400]]

Nimalia é o reino dos antropos na região central de Earthropo. Diferentes linhagens beastfolk vivem sob a autoridade do rei [[Augustus Terra Decimus]] e da [[Coroa de Nimalia]], ao lado de comunidades humanas, élficas, anãs, dragonborns e estrangeiras.

Sua capital é [[Nimalis]], uma grande cidade murada construída onde rios e estradas convergem.

## Geografia

- **Leste:** fronteira com a [[Floresta de Avenor]].
- **Norte:** rios superiores e elevações anteriores à cordilheira.
- **Sul:** campos centrais, confluências e rotas para as montanhas meridionais.
- **Oeste:** colinas, estradas e caminhos para cidades costeiras.

As fronteiras são conhecidas pelo mestre, mas podem ser descobertas gradualmente pelos jogadores.

## Governo

- **Governante:** [[Augustus Terra Decimus]].
- **Capital:** [[Nimalis]].
- **Instituição central:** [[Coroa de Nimalia]].
- **Força oficial:** [[Guarda Real de Nimalia]].

A política existe como parte do cenário, mas a campanha não gira em torno da corte. O reino funciona principalmente como ponto de partida, mercado, abrigo e ligação entre rotas de exploração.

## População

A estimativa de trabalho é de aproximadamente **750.000 habitantes** em todo o reino. Antropos são maioria dentro de Nimalia, embora humanos sejam o povo mais numeroso de Earthropo como um todo.

## Economia

Nimalia produz grãos, artesanato e equipamentos e importa madeira, minérios e materiais raros. A moeda real circula além das fronteiras do reino, mas não é necessariamente o padrão de todo o continente.

## Localizações

```dataview
TABLE status, info, population
FROM "Locations"
WHERE contains(string(territory), this.file.name)
SORT file.name ASC
```

> [!gm]- Bastidores
> A Coroa mantém registros sobre fenômenos e artefatos ligados ao Véu, mas o alcance desse conhecimento ainda não está definido. Augustus pode funcionar como aliado, obstáculo ou antagonista circunstancial sem ser um vilão automático.
