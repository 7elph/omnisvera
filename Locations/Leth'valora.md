---
obsidianUIMode: preview
NoteIcon: location
NoteStatus: Active
type: location
status: Destruída
campaign_status: Ativa
visibility: Jogadores
spoiler_level: light
gm_secret: false
created_by: Sage
territory: "[[Floresta de Avenor]]"
location:
region: Interior de Avenor
district:
danger_level: Médio
thumbnail: "zz_media/vila-de-leth'valora.png"
cover: "zz_media/vila-de-leth'valora.png"
info: Antiga vila élfica da Floresta de Avenor, destruída pelo dragão de colar dourado.
description: Vila élfica menor em Avenor, ligada à origem de Vezemir, Mira e aos Sentinelas de Leth'valora.
chapters:
  - 00 - O Bastardo de Ferro
tags:
  - location
  - local
  - lore
  - elfo
  - vila
  - lethvalora
  - avenor
  - bside
---

# Leth'valora

> [!NOTE|clean no-i right]+ Leth'valora
> ![[vila-de-leth'valora.png|400]]

> [!world]- SINOPSE PÚBLICA
> Leth'valora foi uma pequena vila élfica no interior da [[Floresta de Avenor]]. Ela foi destruída pelo [[Dragão de Colar Dourado]] e permanece como uma das feridas centrais da história de [[Vezemir]].

## Visão Geral

Leth'valora foi uma pequena vila élfica situada no interior da [[Floresta de Avenor]].

Seus habitantes eram principalmente elfos que escolheram viver fora do grande reino élfico, cuja localização e organização ainda serão apresentadas.

A vila preservava tradições antigas, mas não representava toda a civilização élfica de Earthropo.

Leth'valora foi destruída pelo [[Dragão de Colar Dourado]]. Suas ruínas permanecem em Avenor.

## Cultura Local

Casas, passarelas e construções comunitárias se misturavam às árvores, aos rios e às encostas de Avenor.

Por trás da beleza, existia uma comunidade tradicionalista:

- a pureza da linhagem era valorizada;
- a tradição valia mais que a inovação;
- quem nascia fora dos padrões esperados raramente encontrava lugar fácil.

Foi nesta vila que [[Vezemir]] cresceu.

## Pontos Internos

### Coração de Valora

Centro comunitário da vila. Abrigava a residência da família responsável pela chefia local e os espaços de reunião dos moradores.

### Bosque das Estrelas

Floresta sagrada utilizada para cerimônias religiosas e rituais ancestrais.

### A Fortaleza

Antiga fortaleza militar localizada nas elevações ao norte da vila.

Foi abandonada após séculos de paz e, mais tarde, tornou-se o lar de [[Elarion Vaelthor]] e [[Vezemir]].

### [[Sentinelas de Leth'valora]]

Pequena força responsável pela defesa da vila, de suas trilhas e dos acessos próximos.

Foi nesta organização que [[Elarion Vaelthor]] serviu durante séculos.

## Chefia de Leth'valora

A vila era liderada por um chefe humano cujo nome permanece não definido.

Ele morreu durante o ataque do dragão.

[[Mira Valen]] era filha desse chefe. O sobrenome Valen identifica sua família dentro da comunidade.

## Regra de Cânone

- Leth'valora era vila, não reino.
- A vila ficava em Avenor.
- Ela foi destruída pelo dragão de colar dourado.
- Os [[Sentinelas de Leth'valora]] eram guardas da vila e morreram no incidente.
- A existência de um grande reino élfico fica para apresentação futura.

## Residentes e Relações

```dataview
TABLE status, role, faction
FROM "Characters"
WHERE contains(lower(string(location)), "leth'valora")
OR contains(lower(string(faction)), "leth")
SORT file.name ASC
LIMIT 10
```

## Uso em Mesa

- Como apresentar: ruínas élficas belas, queimadas e silenciosas.
- O que os jogadores sabem: Leth'valora foi destruída por um dragão.
- O que apenas o mestre sabe: detalhes do ataque, do dragão e das tradições internas ainda podem ser dosados.
- Como entra em cena: memória, investigação, retorno a Avenor ou pista ligada a Mira/Vezemir.
- Ganchos: dragão de colar dourado, Mira, Sentinelas, preconceitos antigos, ruínas da fortaleza.
- Consequências possíveis: retornar à vila pode forçar Vezemir e Mira a confrontarem versões diferentes do passado.

## Pendências do Sage

- Definir nome do chefe morto, se algum dia for necessário.
- Definir o que restou fisicamente da vila.
- Definir se haverá mapa próprio de Leth'valora.
- Definir relação futura com o reino élfico.
