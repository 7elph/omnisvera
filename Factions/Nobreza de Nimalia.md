---
obsidianUIMode: preview
NoteIcon: faction
NoteStatus: Active
type: faction
visibility: Jogadores
spoiler_level: light
gm_secret: false
status: Ativa
campaign_status: Ativa
leader:
location: "[[Nimalis]]"
territory: "[[Nimalia|Reino de Nimalia]]"
faction:
thumbnail: zz_media/coroa-de-nimalia.png
cover: zz_media/coroa-de-nimalia.png
chapters: []
tags:
  - faction
  - faccao
  - nobreza-de-nimalia
  - coroa-de-nimalia
  - nobreza
  - nimalia
---

# Nobreza de Nimalia

> [!NOTE]
> Estrutura política e social ligada às casas nobres do [[Nimalia|Reino de Nimalia]].

## Visão Geral

A Nobreza de Nimalia cobre as casas nobres ativas do reino, especialmente aquelas ligadas à corte de [[Nimalis]], ao [[Bairro Nobre]], ao exército, à cobrança de impostos e aos pactos políticos da [[Coroa de Nimalia]].

## Relação com a Coroa

A nobreza sustenta e disputa influência junto ao rei soberano [[Augustus Terra Decimus]]. Algumas casas servem diretamente à Coroa; outras podem agir por ambição, medo ou interesse próprio.

## Casas conhecidas

_Nenhuma casa nobre específica foi consolidada ainda._

## Ganchos

- Disputas por influência na corte.
- Casas tentando controlar contratos, impostos ou rotas.
- Nobres envolvidos com guildas, exército, comércio ou crimes.
- Possíveis vínculos com a circulação de remédios falsos.

## Relações

- [[Coroa de Nimalia]] — poder central que a nobreza sustenta e disputa.
- [[Augustus Terra Decimus]] — rei soberano.
- [[Nimalis]] — capital e principal centro político.
- [[Bairro Nobre]] — região urbana associada às casas influentes.
- [[Guilda dos Mercadores]] — possível parceira, rival ou financiadora.

## Personagens Relacionados

```dataview
TABLE thumbnail, location, status, role
FROM "Characters"
WHERE contains(lower(string(faction)), "nobreza de nimalia")
OR contains(tags, "nobreza-de-nimalia")
OR contains(tags, "coroa-de-nimalia")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: títulos, brasões, convites formais, intriga leve, favoritismos e acordos de bastidor.
- O que os jogadores sabem: existem casas nobres ativas em Nimalia, especialmente em [[Nimalis]].
- Como entra em cena: contratos, audiências, acusações, patrocínios, impostos ou escândalos.
- Ganchos: disputas entre casas, envolvimento econômico com a [[Guilda dos Mercadores]], influência sobre a [[Guarda Real de Nimalia]].

## Pendências do Sage

- Nomear casas nobres quando forem necessárias em mesa.
- Definir se há uma casa ligada diretamente a [[Augustus Terra Decimus]].
- Decidir se alguma casa está envolvida com remédios falsos, corrupção ou investigações de Varkh.
