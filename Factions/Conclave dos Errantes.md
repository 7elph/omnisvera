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
thumbnail: zz_media/conclave-dos-errantes.png
cover: zz_media/conclave-dos-errantes.png
info: Rede de aventureiros, investigadores e errantes de Earthropo.
description: Organização flexível que reúne aventureiros, escoltas, exploradores e pessoas sem bandeira fixa.
chapters: []
tags:
  - faction
  - faccao
  - conclave-dos-errantes
  - aventureiros
  - errantes
  - exploradores
---

# Conclave dos Errantes

> [!NOTE|clean no-i right]+ Retrato
> ![[conclave-dos-errantes.png|400]]

> [!world]- SINOPSE PÚBLICA
> O Conclave dos Errantes é uma rede de aventureiros, investigadores, escoltas e viajantes sem bandeira fixa. Onde a Coroa, guildas ou nobres não conseguem agir diretamente, os Errantes podem aceitar contratos e atravessar fronteiras.

## Visão Geral

Organização que reúne aventureiros e errantes de Earthropo. O nome substitui a antiga denominação provisória “Guilda de Aventureiros”.

[[Vezemir]] trabalhou ao lado do Conclave durante sua busca pelo dragão de colar dourado. [[Varkh Nimalis]] também faz parte do Conclave, trazendo para a organização sua experiência como alquimista de rua e investigador de remédios falsos.

## Função no Mundo

O Conclave funciona como rede de aventureiros, investigadores, escoltas, exploradores e pessoas sem bandeira fixa. Ele pode aceitar contratos, investigar ameaças, cruzar fronteiras e agir onde a Coroa, guildas ou nobres não conseguem agir diretamente.

## Tipo de Atuação

| atuação | uso em mesa |
|---|---|
| Contratos | Entrada simples para missões e ganchos. |
| Investigação | Pistas fora do alcance da Coroa. |
| Escolta | Viagens, rotas perigosas e caravanas. |
| Exploração | Ruínas, Avenor, fronteiras e locais esquecidos. |
| Mediação informal | Problemas que instituições oficiais preferem terceirizar. |

## Relações

- [[Vezemir]] — trabalhou com o Conclave durante sua busca.
- [[Varkh Nimalis]] — faz parte do Conclave.
- [[Coroa de Nimalia]] — pode contratar, tolerar ou desconfiar dos Errantes.
- [[Guilda dos Mercadores]] — pode disputar contratos, rotas e informações.
- [[Floresta de Avenor]] — região de atuação provável em missões iniciais.

## Membros e Associados

```dataview
TABLE thumbnail, location, status, role
FROM "Characters"
WHERE contains(lower(string(faction)), "conclave dos errantes")
OR contains(tags, "conclave-dos-errantes")
SORT file.name ASC
```

## Uso em Mesa

- Como apresentar: uma rede flexível de aventureiros, contratos e gente acostumada a resolver problemas fora dos salões nobres.
- O que os jogadores sabem: o Conclave existe e atua em Earthropo; Varkh faz parte dele.
- Como entra em cena: contratos, rumores, pistas, contatos de estrada, missões independentes.
- Ganchos: remédios falsos, investigação em Avenor, disputas com mercadores e problemas que a Coroa prefere terceirizar.

## Pendências do Sage

- Definir liderança atual.
- Definir sede principal ou se o Conclave é descentralizado.
- Definir relação formal com a Coroa.
- Definir símbolos, regras internas e reputação pública.
