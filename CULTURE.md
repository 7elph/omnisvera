---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: Draft
type: lore
status: Cânone de trabalho
campaign_status: Ativo
visibility: Jogadores
spoiler_level: light
gm_secret: false
thumbnail: zz_media/culture.png
cover: zz_media/culture.png
info: Cultura geral de Earthropo como ferramenta de mesa.
description: Costumes, convivência, festivais, informação e textura social do continente de Earthropo.
chapters: []
tags:
  - home
  - lore
  - culture
  - cultura
  - earthropo
---

# Cultura de Earthropo

> [!NOTE|clean no-i right]+ Cultura de Earthropo
> ![[culture.png|400]]

> [!world]- SINOPSE
> Earthropo é um continente moldado por diversas raças, reinos e tradições. Embora cada território possua costumes próprios, algumas práticas são reconhecidas em muitas regiões: feiras sazonais, histórias de estrada, cultos locais, notícias carregadas por arautos e um respeito ambíguo por aventureiros.

## Status

> [!warning]
> Documento em revisão. Cânone parcial.

Este arquivo organiza a cultura geral de Earthropo como ferramenta de mesa. Detalhes específicos de povos, reinos, cidades e religiões devem ser confirmados em notas próprias antes de virarem cânone definitivo.

## Função em Mesa

- Dar tom para cenas sociais.
- Ajudar improviso de tavernas, estradas, feiras, templos e festivais.
- Registrar costumes recorrentes sem transformar cada ideia em nota separada.
- Separar o que já é utilizável do que ainda precisa decisão do Sage.

## Painel Cultural

| área | estado | uso em jogo |
|---|---|---|
| Povos e convivência | Cânone de trabalho | Ajuda a interpretar cidades mistas, preconceitos, alianças e tensões sociais. |
| Aventureiros | Cânone de trabalho | Define como contratos, guildas, nobres e vilas reagem ao grupo. |
| Festivais e costumes | Rascunho utilizável | Dá cor a cenas de cidade, estrada, templo e mercado. |
| Notícias e informação | Cânone de trabalho | Define como boatos, ordens reais e rumores chegam aos jogadores. |
| Cultura regional | Em desenvolvimento | Deve ser expandida em notas de Nimalia, Avenor, Gharok, Valthor e futuros reinos. |

## Índice de Notas Culturais

> [!infobox]
> ```datacards
> TABLE thumbnail, status, territory, description
> FROM #cultura OR #culture
> WHERE file.name != this.file.name
> SORT file.name ASC
>
> // Settings
> preset: compact
> columns: 4
> imageProperty: thumbnail
> cardSpacing: 4
> ```

## Povos e Convivência

Humanos, elfos, anões, antropos e outros povos convivem nos grandes centros, mas isso não significa ausência de tensão. A convivência é mais prática que idealizada: comércio, sobrevivência e ameaças antigas forçam cooperação.

Em Nimalia, os antropos são predominantes no universo de Omnisvera, ainda que humanos sejam a maioria no Old Dragon clássico. Essa diferença deve ser tratada como decisão de cenário, não como erro mecânico.

## Aventureiros na Sociedade

Aventureiros são vistos como úteis, perigosos e imprevisíveis. Em regiões próximas a ruínas, fronteiras e rotas perigosas, sua presença é tolerada ou até desejada. Em cortes, templos e bairros nobres, costumam ser tratados com cautela.

O [[Conclave dos Errantes]] pode servir como ponto de entrada social para aventureiros, mas sua estrutura ainda precisa ser desenvolvida.

## Festivais e Costumes

### Festival da Colheita

Celebra o fim da estação agrícola e a chegada de grandes feiras comerciais.

### Dia dos Heróis

Data dedicada a figuras históricas, protetores locais e aventureiros que defenderam comunidades.

### Festival das Chamas

Comum entre seguidores da [[Igreja das Chamas]]. Fogueiras, vigílias e ritos de memória são elementos prováveis, mas a doutrina ainda está em revisão.

## Notícias e Informação

Notícias circulam por:

- mensageiros reais;
- arautos;
- guildas mercantis;
- bardos e viajantes;
- templos;
- quadros de aviso;
- contatos do [[Conclave dos Errantes]].

## Categorias Futuras

As categorias abaixo não possuem estrutura operacional suficiente para dashboard ativo:

- entretenimento;
- música;
- esportes;
- notícias.

Não usar `#entertainment`, `#music`, `#sport` ou `#news` como consulta operacional até existirem notas reais suficientes.

## Pontos Pendentes

- Diferenças culturais entre Nimalia, futuros reinos élficos, anões e outras regiões.
- Papel social dos antropos no Reino de Nimalia.
- Costumes de Leth'valora antes de sua destruição.
- Festivais realmente canônicos da [[Igreja das Chamas]].
- Como o [[Véu Cinzento]] afetou tradições, luto e memória.

## Uso em Mesa

- Como apresentar: usar costumes locais como textura curta, não como palestra.
- O que os jogadores sabem: costumes públicos, festivais e reputação de aventureiros.
- O que apenas o mestre sabe: tensões históricas, contradições religiosas e tradições ligadas aos Criadores devem ficar no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]] até revelação.
- Como entra em cena: feiras, tavernas, anúncios, ritos, funerais, boatos e contratos.
- Ganchos: festival interrompido, arauto mentindo, bardos espalhando versão falsa de um evento.
- Consequências possíveis: reputação pública, acesso a contatos, apoio popular ou hostilidade local.
