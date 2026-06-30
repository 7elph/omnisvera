---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: Active
cover: zz_media/earthropo.png
cssclasses:
  - b-sides-script
type: lore
status: Ativo
campaign_status: Ativo
visibility: Mestre
spoiler_level: light
gm_secret: false
tags:
  - title
  - home
  - earthropo
  - omnisvera
  - lore
---

<div style="text-align: center;">
  <img src="zz_media/earthropo.png">
</div>
<br>

> [!world]- SINOPSE
> **Earthropo** é o continente em foco das Crônicas de Omnisvera: uma terra de reinos jovens sobre ruínas antigas, florestas vivas, portos inquietos, montanhas esquecidas e fronteiras que ainda não foram totalmente nomeadas.
>
> Ao sul e ao centro do mapa, o [[Nimalia|Reino de Nimalia]] reúne os antropos sob a autoridade de [[Augustus Terra Decimus]], tendo [[Nimalis]] como capital. Nas bordas de suas rotas, a [[Floresta de Avenor]] guarda vilas, fortalezas abandonadas, trilhas élficas e memórias que a Coroa ainda não controla por completo.
>
> Em [[Leth'valora]], uma pequena vila de Avenor, a vida de [[Vezemir]] foi marcada por rejeição, amor, perda e pelo ataque do [[Dragão de Colar Dourado]]. Em [[Nimalis]], [[Varkh Nimalis]] aprendeu que uma voz emprestada pode abrir portas, vender mentiras ou revelar crimes. Nas ruínas ligadas a [[Ruínas de Valthor|Valthor]] e à [[Fortaleza de Gharok|Gharok]], [[Raziel]] desperta de mais de trezentos anos de tormento com uma dívida de sangue antiga demais para morrer.
>
> Agora, as histórias desses personagens começam a se aproximar. Relíquias, remédios falsos, juramentos esquecidos, sangue antigo e o [[Véu Cinzento]] apontam para algo maior que qualquer vingança individual.
>
> Em Earthropo, o mundo não precisa estar pronto para ser explorado. Ele precisa apenas deixar rastros suficientes para que os jogadores descubram onde pisaram.

<div class="homepage">
<hr>
</div>

> [!infobox]
> **CRÔNICAS DE ORIGEM / B-SIDES**
> ---
> ```datacards
> TABLE cover, status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "origem-vezemir")
> AND contains(tags, "bside")
> AND contains(tags, "origem")
> SORT file.name ASC
> LIMIT 1
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> fontSize: small
> ```
> ---
> ```datacards
> TABLE cover, status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "origem-varkh")
> AND contains(tags, "bside")
> AND contains(tags, "origem")
> SORT file.name ASC
> LIMIT 1
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> fontSize: small
> ```
> ---
> ```datacards
> TABLE cover, status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "origem-raziel")
> AND contains(tags, "bside")
> AND contains(tags, "origem")
> SORT file.name ASC
> LIMIT 1
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> fontSize: small
> ```

> [!world]+ CAPÍTULOS
> ```datacards
> TABLE cover, status, campaign_status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "chapter")
> AND !contains(tags, "origem")
> AND !contains(tags, "bside")
> AND (visibility = "Jogadores" OR visibility = "Público")
> AND gm_secret != true
> SORT file.name ASC
>
> // Settings
> preset: grid
> columns: 4
> cardSpacing: 4
> imageProperty: cover
> showImageOnHover: true
> ```

---

## Personagens em Foco

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE contains(tags, "jogador")
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
SORT file.name ASC

// Settings
preset: compact
columns: 3
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## Estrutura do Mundo Conhecido

| Elemento | Definição operacional |
|---|---|
| Universo de campanha | Omnisvera |
| Continente em foco | Earthropo |
| Reino em foco | [[Nimalia]] |
| Capital de Nimalia | [[Nimalis]] |
| Região florestal em foco | [[Floresta de Avenor]] |
| Vila destruída ligada a Vezemir | [[Leth'valora]] |
| Sistema | Old Dragon 2E |

## Geografia Operacional

| lugar | classificação | decisão atual |
|---|---|---|
| [[EARTHROPO/EARTHROPO|Earthropo]] | Continente | Continente em foco da campanha, não o mundo inteiro. |
| [[Nimalia]] | Reino | Reino dos antropos, governado por [[Augustus Terra Decimus]]. |
| [[Nimalis]] | Capital / cidade | Capital de Nimalia e principal centro urbano conhecido. |
| [[Floresta de Avenor]] | Região florestal / território | Região de fronteira próxima a Nimalia; pode se conectar ao futuro reino élfico. |
| [[Leth'valora]] | Vila destruída | Pequena vila élfica em Avenor, destruída pelo dragão de colar dourado. |
| [[Ruínas de Valthor]] | Local / ruínas | Antigo reino próspero ao sudeste de Nimalia. |
| [[Fortaleza de Gharok]] | Local / fortaleza | Antiga fortaleza anã ao norte de Nimalia. |
| [[Mar da Neblina]] | Região marítima | Mar de névoas e rumores, ainda sem posição final. |
| [[Vale Dourado]] | Local menor | Vila, vale agrícola ou região rural pequena dentro de Nimalia. |

## Reinos e Povos Ainda em Apresentação

| povo/reino | posição de trabalho | status |
|---|---|---|
| Reino élfico | Sudoeste, possivelmente ligado a Avenor ou além dela | Futuro |
| Reino anão | Nordeste/norte, próximo de montanhas e Gharok | Futuro |
| Reino dragonborn | Noroeste | Futuro |
| Outros povos | A definir conforme campanha | Futuro |

> [!warning]
> As posições acima são bússola de criação, não fronteira final de mapa. Não criar fronteiras rígidas antes dos mapas e pinos estarem consolidados.

## Eixos Ativos

- O avanço do [[Véu Cinzento]] e seus fragmentos impossíveis.
- A memória dos [[Guardiões do Véu Cinzento]].
- A influência da [[Coroa de Nimalia]] sobre o reino e suas rotas.
- O peso da [[Igreja das Chamas]] e de outras crenças ainda em revisão.
- A aproximação gradual entre as histórias de [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]].
- A descoberta progressiva dos reinos, povos, fronteiras e segredos de Earthropo.

## Arcos Planejados

| # | Níveis | Título | Função | Status |
|:--|:--|:--|:--|:--|
| 0 | 1 | Crônicas de Origem | Registrar histórias pré-campanha dos personagens. | Em consolidação |
| 1 | 1-4 | Ecos do Mundo Perdido | Reunir os personagens e revelar os primeiros sinais do Véu, das relíquias e das ruínas antigas. | Planejado |
| 2 | 5-8 | O Despertar das Cinzas | Fragmentos perdidos colidem com Earthropo e tornam o impossível visível. | Rascunho |
| 3 | 9-12 | Os Deuses Mentiram | Fés, pactos e versões oficiais entram em conflito. | Rascunho |
| 4 | 13-16 | O Arquivo dos Criadores | A verdade sobre a construção do mundo começa a aparecer. | Rascunho |
| 5 | 17-20 | A Reconstrução | O grupo decide o que Omnisvera ainda pode se tornar. | Rascunho |

## Regras de Cânone desta Pasta

- Earthropo é continente, não mundo inteiro.
- Nimalia é reino dos antropos, não cidade.
- Nimalis é a capital de Nimalia.
- A [[Floresta de Avenor]] faz fronteira com Nimalia.
- [[Leth'valora]] é uma vila pequena na região de Avenor, não um reino élfico.
- A vila de Leth'valora foi destruída pelo [[Dragão de Colar Dourado]].
- `story` continua sendo a tag funcional de crônicas/capítulos por enquanto.
- `chapters` continua sendo o campo funcional de capítulos, partes ou story da campanha.
- Materiais históricos e rascunhos de template não fazem parte do cânone ativo até serem convertidos explicitamente para Omnisvera.

## Pendências do Sage

- Definir bordas exatas de Nimalia no mapa.
- Posicionar com precisão [[Fortaleza de Gharok|Gharok]], [[Ruínas de Valthor|Valthor]] e os domínios antigos do [[Clã Sanguinallis]].
- Definir posição final dos futuros reinos élfico, anão e dragonborn.
- Decidir o quanto da história dos Criadores será revelada no primeiro arco.
- Definir como Vezemir, Varkh e Raziel se encontram em mesa.
