---
obsidianUIMode: preview
NoteIcon: story
NoteStatus: Active
type: story
visibility: Mestre
spoiler_level: heavy
gm_secret: true
status: Ativo
campaign_status: Ativo
created_by: MIA
tags:
  - story
  - campanha
---

# Estado da Campanha

> [!NOTE]
> Painel manual do Mestre para acompanhar a situação atual da campanha. A nota pública do capítulo fica em [[01 - Ecos do Mundo Perdido]]. A versão completa de mestre fica nesta página.
>
> [[Home_Mestre]] é a navegação visual. Esta nota é o caderno operacional: preparação, bastidores, segredos, consequências e decisões antes/depois da mesa.

## Capítulo Atual

> [!world]+ CAPÍTULO EM FOCO
> ```datacards
> TABLE cover, status, campaign_status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "chapter01")
> SORT file.name ASC
>
> // Settings
> preset: grid
> columns: 1
> cardSpacing: 1
> imageProperty: cover
> showImageOnHover: true
> ```

## Próxima Sessão

- Capítulo: [[01 - Ecos do Mundo Perdido]]
- Situação inicial provável: estrada secundária entre [[Nimalis]] e [[Floresta de Avenor]].
- Foco de mesa: unir [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente comum.

## Personagens em Foco

```dataview
TABLE status, location, faction
FROM "Characters/Individual"
WHERE visibility = "Mestre" OR visibility = "Jogadores" OR visibility = "Público"
SORT file.name ASC
LIMIT 12
```

## Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
SORT file.name ASC
```

## Facções em Movimento

```dataview
TABLE status, location, territory
FROM "Factions"
SORT file.name ASC
```

## Locais em Foco

```dataview
TABLE territory, status, danger_level
FROM "Locations" OR "Territories"
SORT file.name ASC
LIMIT 12
```

## Itens Revelados

```dataview
TABLE status, location
FROM "Items"
WHERE contains(tags, "item") OR contains(tags, "artefato")
SORT file.name ASC
```

## Consequências Recentes

- Nenhuma consequência jogada ainda.

## Notas para a Próxima Sessão

- Escolher quais três a cinco pistas do capítulo entram em cena.
- Definir quem está na caravana.
- Definir quem transporta os remédios falsos.
- Definir se a [[Guarda Real de Nimalia]] chega antes ou depois do despertar da [[Unidade DORN-7]].
- Preparar uma versão curta da cena inicial para leitura em mesa.

---

## Dossiê do Mestre — Capítulo 01: Ecos do Mundo Perdido

#### _Crônicas de [[EARTHROPO/EARTHROPO|Earthropo]] — capítulo em preparação_

> [!NOTE|clean no-i right]+ 01 - Ecos do Mundo Perdido
> ![[banner-ecos-do-mundo-perdido.png|400]]

> [!world]- SINOPSE
> O primeiro capítulo aproxima [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]]. Uma caravana sofre um acidente depois de um tremor localizado, frascos de remédios falsificados se quebram e uma passagem artificial surge sob a terra. O que parecia contrabando comum revela sinais de tecnologia antiga, símbolos ligados ao [[Véu Cinzento]] e ecos de estruturas esquecidas sob Earthropo. Cada personagem encontra ali uma pista íntima: o dragão e os Guardiões para Vezemir, os remédios falsos de Odran para Varkh, e as marcas de sangue antigo para Raziel.

## Elenco Principal

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE (
  contains(chapters, "01 - Ecos do Mundo Perdido")
  OR contains(tags, "chapter01")
  OR file.name = "Vezemir"
  OR file.name = "Varkh Nimalis"
  OR file.name = "Raziel"
)
SORT file.name ASC

// Settings
preset: compact
columns: 5
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

> [!warning]- SPOILERS DO MESTRE
> O acidente da caravana não é acaso. Parte dos remédios falsos ligados aos métodos de [[Mestre Odran Veyl]] foi adulterada com um reagente antigo retirado de fragmentos tecnológicos encontrados em ruínas menores. Quando o líquido toca uma pedra enterrada, um sistema adormecido tenta reiniciar um protocolo de manutenção e defesa. A estrutura chama a [[Unidade DORN-7]], uma entidade mecânica antiga, danificada e incapaz de entender o mundo moderno. O encontro deve revelar que Earthropo vive sobre ruínas ainda parcialmente funcionais, sem explicar de uma vez o [[Véu Cinzento]], os [[Criadores]], os [[Guardiões do Véu Cinzento]] ou a origem completa das relíquias.

---

## Função do Capítulo

Este capítulo deve servir como o primeiro ponto de convergência entre as histórias de [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]].

A função dele não é revelar todo o mundo. É colocar os jogadores diante de sinais concretos de que suas buscas individuais tocam o mesmo problema maior:

- relíquias antigas;
- falsificações alquímicas;
- ruínas esquecidas;
- marcas do [[Véu Cinzento]];
- histórias que sobreviveram como rumor, medo ou superstição;
- estruturas antigas que ainda funcionam parcialmente sob [[EARTHROPO/EARTHROPO|Earthropo]].

O [[Conclave dos Errantes]] ouviu rumores recentes sobre tremores na rota entre [[Nimalis]] e a [[Floresta de Avenor]]. Dizem que parte do caminho cedeu, revelando algo no subterrâneo. Alguns viajantes juram ter ouvido vozes ecoando debaixo da terra, como se algo tentasse falar através da pedra.

---

## Pontos Sustentados pelo Vault

- [[Vezemir]] busca o dragão de colar dourado e respostas sobre os [[Guardiões do Véu Cinzento]].
- [[Varkh Nimalis]] investiga remédios falsos ligados aos métodos de [[Mestre Odran Veyl]].
- [[Raziel]] despertou após mais de trezentos anos e procura os responsáveis por sua traição.
- [[Nimalia]] é o reino dos antropos, com [[Nimalis]] como capital.
- A [[Floresta de Avenor]] faz fronteira com Nimalia.
- [[Leth'valora]] foi destruída pelo [[Dragão de Colar Dourado]].
- [[Ruínas de Valthor]] e [[Fortaleza de Gharok]] são pontos antigos ligados à camada esquecida de Earthropo.
- A forma exata como os três personagens se encontram ainda pode ser escolhida durante a preparação da sessão.

---

## Premissa de Trabalho

Cada personagem tem uma razão própria para seguir esse rastro.

- Vezemir vê uma possível ligação com o dragão e com os Guardiões do Véu Cinzento: uma história sobre névoa cinzenta contada por gente que jura não acreditar em lendas.
- Varkh vê uma pista sobre quem está usando os métodos de Odran: um símbolo antigo em um frasco falso, parecido com uma runa que Odran lhe ensinou.
- Raziel vê ecos de poderes antigos ligados às [[Ruínas de Valthor]], à [[Fortaleza de Gharok]] e ao sangue que o reconstruiu: uma inscrição apagada que pode indicar o clã ao qual pertencia.

Os rumores dizem que o local sob a abertura contém pedras antigas, inscrições desconhecidas e o reflexo de metal opaco visível de cima. Onde há passagem de água, há ferrugem, sugerindo que a estrutura está ali há muito tempo. Vozes ecoam do subterrâneo sem que ninguém entenda o que significam. Até agora, parece haver uma tentativa de abafar o caso e afastar curiosos.

---

## Primeiro Incidente Visível

O primeiro sinal concreto do capítulo acontece em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]], próxima a um antigo marco de pedra que a maioria dos viajantes trata apenas como ruína de beira de caminho.

Uma pequena caravana de suprimentos sofre um acidente após um tremor curto, seco e localizado, como se algo pesado tivesse se movido debaixo da terra.

A estrada cede.

Uma carroça tomba.

Caixas se quebram.

Entre mantimentos comuns, surgem frascos de remédio falso, ferramentas alquímicas baratas e pequenas placas metálicas marcadas com símbolos que não pertencem a nenhum ferreiro, boticário ou templo conhecido.

Um dos frascos se rompe sobre uma pedra enterrada. O líquido escorre pelas rachaduras.

A pedra responde.

Linhas quase apagadas começam a emitir uma luz fraca, azulada, como brasas frias sob poeira antiga. Em seguida, uma abertura circular aparece parcialmente sob a terra, revelando uma passagem artificial.

Não parece uma caverna.

Não parece uma tumba.

Não parece uma mina.

Parece uma instalação esquecida.

O cheiro que vem de baixo mistura terra molhada, ferrugem, óleo velho e algo parecido com pedra queimada.

Poucos minutos depois, um som metálico ecoa do fundo.

Algo lá embaixo ouviu o chamado.

---

## O Que Aconteceu de Verdade

A carga da caravana não era comum.

Parte dos remédios falsos ligados aos métodos de [[Mestre Odran Veyl]] foi adulterada com um reagente antigo, retirado ilegalmente de fragmentos encontrados em ruínas menores de Earthropo.

Quem falsificou os remédios não entendia a origem do material. Usavam apenas porque estabilizava misturas, preservava líquidos por mais tempo e dava aos frascos uma aparência milagrosa.

Mas o reagente não era alquímico.

Era resíduo de uma tecnologia antiga ligada a estruturas anteriores à história conhecida de Nimalia.

Quando o líquido entrou em contato com a pedra enterrada, ativou parcialmente um sistema adormecido.

Esse sistema não despertou uma ameaça mágica.

Ele tentou reiniciar um protocolo antigo.

E o protocolo chamou uma unidade de manutenção e defesa esquecida.

---

## Local Principal — A Passagem Sob a Estrada

A abertura leva a um corredor inclinado, parcialmente soterrado.

As paredes são lisas demais para terem sido escavadas com picareta. Em alguns trechos, parecem pedra. Em outros, metal escuro. Raízes atravessam juntas e placas como se a floresta tivesse crescido tentando engolir a estrutura.

A sensação deve ser de lugar antigo, funcional e quebrado.

Não é uma masmorra feita para aventureiros.

É uma parte morta de um sistema que já serviu a algum propósito real.

### Elementos Visíveis

- marcas de arrasto no chão;
- símbolos repetidos em placas quebradas;
- pequenas luzes falhando atrás de superfícies translúcidas;
- portas sem dobradiças aparentes;
- corredores parcialmente bloqueados por terra;
- ossos muito antigos presos sob escombros;
- restos de pequenos mecanismos esmagados;
- uma inscrição parcialmente legível;
- uma sala circular no fim do corredor.

---

## A Sala Circular

No fim da passagem existe uma sala ampla, circular, com o teto rachado e parcialmente coberto por raízes.

No centro, há uma figura caída de joelhos, presa entre cabos petrificados, pedra partida e suportes metálicos rompidos.

À primeira vista, pode parecer uma estátua.

Mas há detalhes errados demais:

- articulações mecânicas;
- placas sobrepostas como armadura;
- marcas de impacto antigas;
- um núcleo apagado no peito;
- dedos grossos, feitos para força e precisão;
- inscrições gravadas em partes do corpo;
- uma fenda no rosto onde uma luz fraca começa a surgir.

Quando os personagens se aproximam, o chão vibra.

A figura tenta mover um braço.

Falha.

Tenta erguer a cabeça.

Consegue.

Então uma voz grave, quebrada e irregular sai de dentro da estrutura:

> “Setor comprometido.”

Depois de alguns segundos:

> “Autoridade de reconstrução ausente.”

E então:

> “Identifiquem-se.”

---

## A [[Unidade DORN-7]]

Nome de trabalho: **[[Unidade DORN-7]]**

Outros nomes possíveis dentro da campanha:

- Vigia Dorn;
- Sentinela Dorn;
- O Homem de Pedra e Ferro;
- O Guardião Soterrado;
- A Máquina da Estrada Velha.

A [[Unidade DORN-7]] não foi criada para conquistar, matar ou servir reis.

Ela fazia parte de uma estrutura antiga de proteção, manutenção e contenção. Sua função era preservar setores importantes depois de uma catástrofe ou falha estrutural.

Ela não entende Nimalia como reino.

Não reconhece a Coroa.

Não reconhece a Guarda Real.

Não entende títulos nobres modernos.

Para ela, todos os presentes são “cidadãos não identificados”, “autoridades sem credencial” ou “sobreviventes fora de registro”.

Ela está danificada, incompleta e confusa. Isso torna o contato perigoso.

Não porque ela seja maligna.

Mas porque ainda tenta obedecer regras que ninguém conhece.

---

## Como a [[Unidade DORN-7]] Deve Agir

A [[Unidade DORN-7]] não deve atacar imediatamente.

Ela primeiro tenta entender a situação.

Suas ações iniciais:

1. tenta se erguer;
2. escaneia os personagens visualmente;
3. identifica armas como risco;
4. identifica sangue, ferimentos ou doença;
5. reage ao símbolo antigo nos frascos falsos;
6. tenta acessar um “núcleo local” que não responde;
7. entra em instabilidade quando percebe que o setor está exposto.

Frases possíveis:

> “Ciclos excedidos.”

> “Registro de superfície indisponível.”

> “Núcleo local sem resposta.”

> “Material contaminado detectado.”

> “Uso indevido de componente médico.”

> “A contenção foi violada.”

> “A superfície permanece habitável?”

> “Onde estão os responsáveis pelo setor?”

> “Este local deveria permanecer selado.”

A [[Unidade DORN-7]] não explica o que é o Véu.

Não explica quem foram os Criadores.

Não explica a Grande Fratura.

Ela apenas deixa claro que o mundo atual está vivendo sobre ruínas que ainda funcionam parcialmente.

---

## Conexão com Cada Personagem

### [[Vezemir]]

Vezemir pode notar que algumas marcas no local lembram símbolos associados aos [[Guardiões do Véu Cinzento]], mas em uma versão mais antiga, incompleta ou distorcida.

Isso não prova que os Guardiões criaram a estrutura.

Pode indicar o contrário: os Guardiões talvez tenham herdado, protegido ou reinterpretado sinais muito mais antigos.

A [[Unidade DORN-7]] também pode reagir à presença de Vezemir de forma estranha, como se identificasse nele traços de exposição prolongada a algo ligado ao Véu, às ruínas ou ao dragão.

Frase possível:

> “Resíduo de ruptura detectado.”

Vezemir não precisa entender o que isso significa.

Mas deve sentir que aquilo toca sua busca.

### [[Varkh Nimalis]]

Varkh reconhece nos frascos falsos elementos do método de [[Mestre Odran Veyl]], mas adulterados por alguém que não dominava a técnica original.

Isso liga sua investigação pessoal ao acidente.

Ele pode perceber:

- rótulos falsificados;
- dosagens erradas;
- resíduos incomuns;
- uso de estabilizante desconhecido;
- tentativa de imitar uma fórmula legítima.

A [[Unidade DORN-7]] identifica os frascos como “material médico contaminado” ou “componente clínico corrompido”.

Isso dá a Varkh uma pista concreta:

> os falsificadores estão usando restos antigos como matéria-prima.

### [[Raziel]]

Raziel pode sentir que a estrutura pertence a uma camada de mundo anterior ao presente.

Não como visão divina.

Não como revelação completa.

Mas como reconhecimento físico: o ar pesa diferente, as inscrições parecem antigas demais, e a presença da máquina desperta ecos de sua própria reconstrução, traição ou vínculo com sangue antigo.

A [[Unidade DORN-7]] pode reagir a Raziel com uma falha específica:

> “Registro biológico incompatível.”

Ou:

> “Assinatura vital instável.”

Isso não precisa explicar Raziel.

Apenas cria tensão.

A máquina percebe que há algo errado ou incomum nele.

---

## Forças em Movimento

### [[Guarda Real de Nimalia]]

A Guarda quer isolar a estrada, controlar testemunhas e impedir que rumores se espalhem.

Eles não entendem o que foi encontrado, mas sabem que algo assim pode gerar pânico ou interesse político.

Se a [[Unidade DORN-7]] for vista por muita gente, a Guarda tentará tomar custódia dela.

### Falsificadores

Alguém ligado aos remédios falsos quer recuperar a carga antes que ela seja rastreada.

Esses agentes não precisam ser vilões grandiosos ainda.

Podem ser capangas, atravessadores, boticários corruptos ou mensageiros pagos.

Eles sabem pouco.

Mas sabem o suficiente para fugir quando veem a estrutura ativar.

### [[Conclave dos Errantes]]

O [[Conclave dos Errantes]] pode aparecer como intermediário, contratante ou fonte de rumor.

Eles não precisam saber tudo.

Mas podem ter ouvido histórias sobre “estradas que respiram luz” ou “homens de pedra sob as raízes de Avenor”.

### [[Guardiões do Véu Cinzento]]

Os [[Guardiões do Véu Cinzento]] não precisam aparecer diretamente.

Melhor que apareçam por sinal:

- símbolo antigo;
- advertência riscada;
- fragmento de frase;
- marca em uma parede;
- objeto deixado por alguém que esteve ali antes.

Isso mantém o mistério.

---

## Pistas Concretas do Primeiro Encontro

Escolher de três a cinco para aparecerem na primeira sessão.

1. Um frasco falso com símbolo raspado no fundo.
2. Uma placa metálica marcada com o mesmo símbolo encontrado na galeria.
3. Um mapa incompleto queimado nas bordas.
4. Uma inscrição antiga parcialmente legível: “SETOR DORN — CONTENÇÃO”.
5. Uma peça retirada do corpo de um pequeno mecanismo destruído.
6. Uma lista de entregas apontando para [[Nimalis]].
7. Um nome repetido nos documentos falsificados.
8. Marcas de garras antigas em uma porta interna.
9. Uma parede onde alguém escreveu: “não acordem o vigia”.
10. Uma coordenada ou marcação apontando para outra ruína.

---

## Possíveis Pontos de Encontro

> [!note]
> Escolher apenas um quando a sessão for preparada. Não canonizar todos ao mesmo tempo.

- Uma rota entre [[Nimalis]] e a [[Floresta de Avenor]].
- Uma investigação sobre remédios falsos que chega perto de território ligado ao Véu.
- Uma ruína menor conectada indiretamente às [[Ruínas de Valthor]].
- Um pedido do [[Conclave dos Errantes]] envolvendo uma relíquia ou escolta.
- Um rumor vindo do Mar da Neblina que cruza com documentos da Coroa.

---

## Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
SORT file.name ASC
```

---

## Primeiro Conflito Prático

Depois que a [[Unidade DORN-7]] desperta, três problemas acontecem quase ao mesmo tempo:

1. a estrutura começa a colapsar;
2. a Guarda Real se aproxima da entrada;
3. alguém tenta roubar uma peça ou documento da carga.

Os personagens precisam decidir o que priorizar:

- salvar feridos;
- impedir a fuga dos falsificadores;
- conversar com o golem;
- esconder a descoberta;
- chamar reforços;
- fugir antes que sejam culpados;
- proteger a passagem;
- impedir que a Guarda tome tudo.

Esse conflito força a união dos personagens sem parecer artificial.

Eles não precisam confiar uns nos outros.

Só precisam perceber que todos estão presos no mesmo problema.

---

## Escolhas Possíveis dos Jogadores

Ao fim do capítulo ou da primeira sessão, os personagens podem decidir:

- entregar a [[Unidade DORN-7]] à Guarda Real;
- esconder a existência do golem;
- tentar reativá-lo com segurança;
- levar a informação ao Conclave dos Errantes;
- investigar a origem dos frascos falsos;
- seguir o ponto marcado no mapa;
- procurar alguém que reconheça os símbolos;
- selar a passagem e fingir que nada aconteceu.

Nenhuma escolha deve encerrar o mistério.

Cada escolha deve abrir uma consequência.

---

## Consequências para Sessões Futuras

### Se a Coroa tomar o local

- a estrada é fechada;
- testemunhas são interrogadas;
- documentos somem;
- surgem rumores sobre uma “arma antiga”;
- a Guarda Real passa a observar os personagens.

### Se os personagens esconderem o golem

- ganham uma fonte perigosa de pistas;
- podem ser perseguidos;
- precisam lidar com reparos, energia e memória falha;
- carregam um segredo que pode colocar todos em risco.

### Se os falsificadores escaparem

- a rede de remédios falsos muda de rota;
- provas desaparecem;
- Varkh ganha um inimigo ativo;
- alguém passa a saber que os personagens viram demais.

### Se o símbolo dos Guardiões for reconhecido

- Vezemir encontra uma pista nova;
- mas também pode atrair atenção indesejada;
- os Guardiões do Véu Cinzento deixam de ser apenas uma lembrança distante.

### Se Raziel interagir com a máquina

- a [[Unidade DORN-7]] pode registrar sua presença como anomalia;
- isso pode ligar Raziel a estruturas antigas sem explicar tudo ainda;
- alguma parte da instalação pode reagir a ele de forma inesperada.

---

## Possível Cena de Encerramento

A [[Unidade DORN-7]], mesmo danificada, consegue sair da sala circular ou ser parcialmente libertada.

Ao ver o céu pela primeira vez em séculos, ela permanece imóvel.

Observa Nimalis ao longe.

Observa a floresta.

Observa os personagens.

Então diz:

> “Reconstrução incompleta.”

Depois seu núcleo falha novamente.

Antes de apagar, projeta no chão um mapa fragmentado de Earthropo.

Vários pontos estão apagados.

Um ponto pisca.

Não é ali.

E a última frase antes do silêncio é:

> “Outro setor respondeu.”

---

## Segredos do Mestre

- A conexão real entre o [[Véu Cinzento]], os Guardiões e os [[Criadores]] ainda não deve ser revelada de uma vez.
- A relação entre o dragão de colar dourado e os eventos antigos deve ser mostrada por pistas, não por exposição direta.
- As pistas de Varkh devem parecer mundanas antes de apontarem para algo maior.
- Raziel deve entrar com peso, mas sem resolver o mistério inteiro sozinho.
- A [[Unidade DORN-7]] não é única.
- A passagem sob a estrada faz parte de uma rede antiga sob Earthropo.
- O reagente usado nos remédios falsos veio de fragmentos de tecnologia antiga.
- Alguém em Nimalis pode já saber da existência de estruturas semelhantes.
- A Coroa provavelmente tentará controlar a descoberta se souber da verdade.
- O mapa fragmentado projetado pela [[Unidade DORN-7]] aponta para outro setor ativo.

---

## Pendências Antes de Jogar

- Definir ponto inicial da mesa.
- Definir quem está na caravana.
- Definir quem está transportando os remédios falsos.
- Definir qual símbolo antigo aparece nos frascos.
- Definir se a Guarda Real chega antes ou depois do despertar da [[Unidade DORN-7]].
- Separar informação pública de segredo do mestre.
- Confirmar quais imagens serão usadas como capa, retrato ou handout.
- Definir quais pistas aparecem no primeiro encontro.
- Decidir se a [[Unidade DORN-7]] fica consciente no fim da sessão ou desliga temporariamente.

---

## Uso em Mesa

- **Como apresentar:** começar por uma consequência concreta, não por explicação de lore. A estrada cede, a carroça tomba, os frascos quebram e a passagem antiga aparece.
- **O que os jogadores sabem:** cada personagem sabe sua própria motivação inicial e percebe que o incidente toca sua busca pessoal.
- **O que apenas o mestre sabe:** as conexões entre Véu, dragão, sangue antigo, falsificações e estruturas subterrâneas.
- **Como entra em cena:** por acidente, investigação, contrato, perseguição ou descoberta durante a rota entre Nimalis e a Floresta de Avenor.
- **Ganchos:** frasco falso, símbolo antigo, sobrevivente assustado, ruína interditada, mapa incompleto, golem danificado, carga adulterada.
- **Consequências possíveis:** os personagens se unem por conveniência, dívida, suspeita ou ameaça compartilhada.

---

## Segredos de Personagens Centralizados

> [!WARNING]
> Conteúdo movido das notas de personagem para manter o vault operacionalmente público. Revisar e consolidar depois.

### Elarion Vaelthor

- Sabia muito mais sobre a origem de [[Vezemir]] do que jamais revelou.
    
- Possivelmente possuía ligações com os [[Guardiões do Véu Cinzento]].
    
- Demonstrava preocupação incomum com a magia que habitava o jovem meio-elfo.
    
- Pode ter escondido documentos, artefatos ou registros em [[Leth'valora]].
    
- Seu desaparecimento ocorreu pouco tempo após a partida de Vezemir.
    

---

### Raziel

- O verdadeiro motivo pelo qual o Ancião Primordial libertou Raziel permanece desconhecido.

- A heresia rúnica usada como pretexto para sua captura ainda não foi definida.

- A forma como as Adagas de Espectro Fantasma permaneceram ligadas a Raziel durante o aprisionamento continua em aberto.

- Sua relação com o Véu Cinzento e com os Criadores ainda não foi confirmada.

---

### Unidade DORN-7

- A Unidade DORN-7 não é única.
- Ela fazia parte de uma rede antiga sob Earthropo.
- A ativação dela foi causada por reagente antigo presente nos remédios falsificados.
- Ela pode reconhecer traços incomuns em [[Vezemir]], [[Varkh Nimalis]] ou [[Raziel]], mas não deve explicar tudo.

### Varkh Nimalis

- A identidade de quem está usando os métodos de Odran ainda é desconhecida.

- O envolvimento de Odran com as falsificações, caso exista, ainda não foi definido.

- A extensão real da fama de Varkh como assassino pode ser maior ou menor do que os rumores indicam.

- A classe mecânica definitiva de Varkh ainda precisa ser reconciliada com a ficha sem nome recebida do jogador.

---

### Vezemir

- [[O Medalhão]]  pode estar ligado à verdadeira origem de Vezemir.
    
- [[Padre Oric]] desapareceu investigando conexões entre os Guardiões e o dragão de colar dourado.
    
- O dragão demonstrou reconhecer Vezemir durante o ataque à vila.
    
- [[Elarion Vaelthor]] pode ter ocultado informações sobre seus pais biológicos.
    
- Existe a possibilidade de Vezemir descender de alguma linhagem élfica.
    

---
