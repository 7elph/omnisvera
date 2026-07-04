---
obsidianUIMode: preview
NoteIcon: story
NoteStatus: Active
type: story
subtype: campaign_state
visibility: Mestre
spoiler_level: heavy
gm_secret: true
status: Ativo
campaign_status: Ativo
created_by: MIA
updated_by: MIA
work_status: Em desenvolvimento
canon_status: Working Canon
requires_review: true
tags:
  - story
  - campanha
  - estado-da-campanha
  - mestre
  - gm-secret
  - omnisvera
---

## ESTADO DA CAMPANHA


## Painel Rápido

| Campo | Estado |
|---|---|
| Campanha | [[Omnisvera]] |
| Região atual | [[Nimalia]] |
| Capital em foco | [[Nimalis]] |
| Capítulo atual | [[01 - Ecos do Mundo Perdido]] |
| Sessão em preparação | Encontro inicial dos personagens |
| Personagens centrais | [[Vezemir]], [[Varkh Nimalis]], [[Raziel]] |
| Frente principal | Estrada, remédios falsos e ruínas antigas |
| Ameaça visível | Acidente da caravana e descoberta subterrânea |
| Ameaça oculta | Tecnologia antiga, Véu, falsificadores, Coroa e controle da verdade |
| Estado da mesa | Preparação |

---

## Regra de Separação do Vault

> [!important]
> **Nota principal** mostra o mundo.
> **Estado da Campanha** mostra a engrenagem por trás do mundo.
> **Home_Mestre** mostra atalhos, painéis e frentes ativas.

### O que fica nas notas principais

- descrição pública;
- aparência;
- reputação;
- função jogável;
- rumores sem resposta confirmada;
- relações conhecidas;
- ganchos sem revelar a verdade final;
- uso em mesa sem spoiler pesado.

### O que fica no Estado da Campanha

- segredos reais ou possíveis;
- culpados;
- verdades ocultas;
- envolvimento secreto de NPCs ou facções;
- condições de revelação;
- consequências futuras;
- relação entre frentes;
- decisões pendentes do Sage;
- interpretação de bastidor.

---

## Painel de Controle do Vault

| Área | Acesso rápido | Uso |
|---|---|---|
| Home do Mestre | [[Home_Mestre]] | navegação visual e atalhos |
| Home dos Jogadores | [[Home]] | consulta player-safe |
| Capítulos | [[01 - Ecos do Mundo Perdido]] | versão pública/jogável do capítulo |
| Estado da Campanha | [[ESTADO_DA_CAMPANHA]] | bastidores, frentes e decisões |
| Fila de Conteúdo | [[CONTENT_CREATION_QUEUE]] | notas que precisam desenvolvimento |
| Modelo Player-Safe | [[PLAYER_SAFE_ENTITY_MODEL]] | regra de separação entre nota pública e bastidor |

---

## Entidades em Desenvolvimento Prioritário

| Entidade | Tipo | Função no controle |
|---|---|---|
| [[O Frasco Afogado]] | local | loja/oficina, investigação dos remédios falsos |
| [[Maré Baixa]] | local | submundo portuário, origem de Varkh |
| [[Nimalis]] | cidade | capital e centro político |
| [[Augustus Terra Decimus]] | personagem | rei de Nimalia, peso político e controle da verdade |
| [[Coroa de Nimalia]] | facção | poder institucional |
| [[Varkh Nimalis]] | personagem | arco dos remédios falsos |
| [[Guilda dos Mercadores]] | facção | comércio, rotas e influência econômica |
| [[Porto de Nimalia]] | local | entrada de cargas, rumores e contrabando |
| [[Raziel]] | personagem | sangue antigo, Gharok e passado enterrado |
| [[Culto dos Sussurrantes]] | facção/rumor | ameaça em revisão ligada ao Véu |
| [[Unidade DORN-7]] | entidade/artefato | tecnologia antiga e primeiro contato com o Mundo Perdido |

---

## Capítulo Atual

> [!world]+ CAPÍTULO EM FOCO
> ```datacards
> TABLE cover, status, campaign_status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "capitulo01")
> SORT file.name ASC
>
> // Settings
> preset: grid
> columns: 1
> cardSpacing: 1
> imageProperty: cover
> showImageOnHover: true
> ```

---

## Próxima Sessão

- **Capítulo:** [[01 - Ecos do Mundo Perdido]]
- **Situação inicial provável:** estrada secundária entre [[Nimalis]] e [[Floresta de Avenor]].
- **Foco de mesa:** unir [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente comum.
- **Cena-motor:** uma caravana sofre acidente, frascos falsificados quebram e uma passagem antiga é revelada sob a estrada.
- **Mistério inicial:** os remédios falsos carregam algo que não é apenas alquimia.
- **Escalada:** a [[Unidade DORN-7]] desperta parcialmente.

### Objetivo de Mesa

Unir os personagens por consequência, não por amizade instantânea.

Eles não precisam confiar uns nos outros.

Só precisam perceber que estão presos no mesmo problema.

### Preparar Antes da Sessão

- Definir quem está na caravana.
- Definir quem transporta os remédios falsos.
- Escolher três a cinco pistas iniciais.
- Definir se a [[Guarda Real de Nimalia]] chega antes ou depois do despertar da [[Unidade DORN-7]].
- Preparar uma descrição curta da estrada cedendo.
- Preparar a primeira fala da [[Unidade DORN-7]].
- Decidir se a descoberta chega aos ouvidos da [[Coroa de Nimalia]] já na primeira sessão.

---

## Consequências Recentes

- Nenhuma consequência jogada ainda.

---

## Índices Dinâmicos

### Personagens em Foco

```dataview
TABLE status, location, faction
FROM "Characters/Individual"
WHERE visibility = "Mestre" OR visibility = "Jogadores" OR visibility = "Público"
SORT file.name ASC
LIMIT 12
```

### Quests Ativas

```dataview
TABLE quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE type != "index"
AND quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

### Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
WHERE type != "index"
SORT file.name ASC
```

### Facções em Movimento

```dataview
TABLE status, location, territory
FROM "Factions"
WHERE type != "index"
SORT file.name ASC
```

### Locais em Foco

```dataview
TABLE territory, status, danger_level
FROM "Locations" OR "Territories"
WHERE type != "index"
SORT file.name ASC
LIMIT 12
```

### Itens Revelados

```dataview
TABLE status, location
FROM "Items"
WHERE type != "index"
AND (contains(tags, "item") OR contains(tags, "artefato"))
SORT file.name ASC
```

---

# FRENTES DE CONTROLE

> [!IMPORTANT]
> Estas frentes guardam bastidores e decisões do mestre.
> As notas principais devem permanecer player-safe.

---

## Frente — Capítulo 01: Ecos do Mundo Perdido

### Entidades Ligadas

- [[01 - Ecos do Mundo Perdido]]
- [[Vezemir]]
- [[Varkh Nimalis]]
- [[Raziel]]
- [[Unidade DORN-7]]
- [[Nimalis]]
- [[Floresta de Avenor]]
- [[O Frasco Afogado]]
- [[Remédios Falsos de Maré Baixa]]
- [[Véu Cinzento]]
- [[Criadores]]
- [[Guardiões do Véu Cinzento]]

### Status Atual

Capítulo em preparação.
Serve como primeiro ponto de convergência entre os personagens principais.

O capítulo começa com um incidente aparentemente local: uma caravana, remédios falsificados e uma estrada que cede.

No bastidor, o incidente revela a existência de estruturas antigas sob Earthropo e prepara a entrada da [[Unidade DORN-7]].

### O que está visível aos jogadores

- Há remédios falsos circulando.
- Uma caravana sofreu acidente.
- A estrada cedeu de forma estranha.
- Há algo artificial sob a terra.
- Cada personagem encontra um motivo pessoal para se envolver.

### Segredos do Mestre

- O acidente da caravana não é puro acaso.
- Parte dos remédios falsos contém reagente antigo.
- O reagente veio de fragmentos tecnológicos retirados de ruínas menores.
- O contato do líquido com uma pedra enterrada ativou parcialmente um sistema antigo.
- A [[Unidade DORN-7]] não é única.
- A passagem sob a estrada faz parte de uma rede antiga sob Earthropo.
- Alguém em [[Nimalis]] pode já saber da existência de estruturas semelhantes.
- A [[Coroa de Nimalia]] provavelmente tentará controlar a descoberta se souber da verdade.

### Pistas

Escolher três a cinco para a primeira sessão:

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

### Condições de Revelação

- Revelar por exploração da passagem.
- Revelar por análise dos frascos.
- Revelar por reação da [[Unidade DORN-7]].
- Revelar por chegada da Guarda Real.
- Revelar por reconhecimento parcial dos símbolos por Vezemir, Varkh ou Raziel.

### Consequências

Se a Coroa tomar o local:

- a estrada é fechada;
- testemunhas são interrogadas;
- documentos somem;
- surgem rumores sobre uma arma antiga;
- a Guarda Real passa a observar os personagens.

Se os personagens esconderem a descoberta:

- ganham uma fonte perigosa de pistas;
- podem ser perseguidos;
- precisam lidar com reparos, energia e memória falha da [[Unidade DORN-7]];
- carregam um segredo que pode colocar todos em risco.

### Decisões Pendentes do Sage

- Definir ponto inicial da mesa.
- Definir quem está na caravana.
- Definir quem transporta os remédios falsos.
- Definir qual símbolo antigo aparece nos frascos.
- Definir se a Guarda Real chega antes ou depois do despertar da [[Unidade DORN-7]].
- Definir se a [[Unidade DORN-7]] fica consciente no fim da sessão ou desliga temporariamente.

---

## Frente — O Frasco Afogado e os Remédios Falsos

### Entidades Ligadas

- [[O Frasco Afogado]]
- [[Maré Baixa]]
- [[Varkh Nimalis]]
- [[Mestre Odran Veyl]]
- [[Remédios Falsos de Maré Baixa]]
- [[Rede de Falsificadores de Maré Baixa]]
- [[Guilda dos Mercadores]]
- [[Coroa de Nimalia]]

### Status Atual

Frente de investigação urbana ligada à origem de [[Varkh Nimalis]], à memória de [[Mestre Odran Veyl]] e à circulação de remédios falsos em [[Nimalia]].

A nota principal de [[O Frasco Afogado]] deve mostrar loja, atmosfera, produtos, rumores e ligação com Varkh.

A verdade sobre falsificadores, Odran, Guilda e Coroa fica aqui.

### O que está visível aos jogadores

- O Frasco Afogado existe em [[Maré Baixa]].
- Odran foi mentor de Varkh.
- Remédios falsos circulam com marcas parecidas com as de Odran.
- Moradores de Maré Baixa comentam sobre frascos adulterados.
- Varkh reconhece que há algo errado nos métodos usados.

### Segredos do Mestre

- Não confirmar ainda se Odran está envolvido nas falsificações.
- Não decidir automaticamente se [[O Frasco Afogado]] está aberto, fechado, abandonado, tomado ou vigiado.
- Se houver estoque escondido, fórmula perdida ou registro comprometedor, tratar como revelação futura.
- A [[Guilda dos Mercadores]] pode saber mais sobre a rota dos produtos do que admite.
- A [[Coroa de Nimalia]] pode tentar controlar a investigação se houver risco público.
- O reagente antigo usado nos remédios falsos pode ligar esta frente à [[Unidade DORN-7]] e às ruínas.

### Verdades Possíveis

- Alguém está usando o símbolo de Odran sem autorização.
- Odran foi incriminado.
- Odran criou uma fórmula antiga e alguém roubou a base.
- A Rede de Falsificadores encontrou material antigo sem saber o que era.
- Um agente da Guilda financiou a rota.
- Um agente da Coroa encobriu o problema para evitar pânico.

### Pistas

- Rótulos antigos.
- Frascos adulterados.
- Ingredientes baratos demais.
- Assinatura perfeita demais.
- Testemunhas de [[Maré Baixa]] que conhecem Odran.
- Resíduo que não se comporta como alquimia comum.
- Documento comercial apontando para o [[Porto de Nimalia]].

### Condições de Revelação

- Revelar por investigação dos frascos.
- Revelar por retorno de Varkh a [[Maré Baixa]].
- Revelar por contato com antigos clientes de Odran.
- Revelar por confronto com falsificadores.
- Revelar por reação da [[Unidade DORN-7]] ao material contaminado.

### Consequências

- Expor a falsificação pode atrair criminosos, mercadores, guardas ou clientes desesperados.
- Se a Coroa intervier, Varkh pode virar testemunha, suspeito ou bode expiatório.
- Se a Guilda for envolvida cedo demais, a investigação pode escalar para crise econômica.

### Decisões Pendentes do Sage

- Estado atual do Frasco.
- Papel real de Odran.
- Identidade de quem usa o símbolo falso.
- Nível de envolvimento da Guilda e da Coroa.
- Origem exata do reagente antigo.

---

## Frente — Nimalis, Coroa, Porto e Guarda

### Entidades Ligadas

- [[Nimalis]]
- [[Coroa de Nimalia]]
- [[Guarda Real de Nimalia]]
- [[Porto de Nimalia]]
- [[Guilda dos Mercadores]]
- [[Maré Baixa]]
- [[Bairro Nobre]]
- [[Mercado Central]]
- [[Distrito Comercial]]

### Status Atual

Frente estrutural da capital. Define como poder, comércio, segurança, rumor e circulação de informações funcionam em [[Nimalis]].

### O que está visível aos jogadores

- Nimalis é capital e centro político.
- A Coroa domina a imagem pública da cidade.
- A Guarda Real representa ordem e repressão.
- O Porto de Nimalia move carga, rumores e contrabando.
- A Guilda dos Mercadores é economicamente relevante.
- Maré Baixa escapa parcialmente ao controle formal.

### Segredos do Mestre

- Rotas ilícitas, cargas suspeitas e autoridade portuária ainda precisam ser definidas.
- O grau de controle real da Coroa sobre o porto permanece aberto.
- A influência da Guilda pode ser pública, indireta ou clandestina.
- A Coroa pode usar crise sanitária, falsificações ou descoberta antiga como justificativa para intervenção.
- A Guarda Real pode agir sem entender totalmente o que está protegendo.

### Pistas

- Carga atrasada.
- Navio sem registro.
- Guarda comprada.
- Documento comercial contraditório.
- Mercador que sabe demais.
- Testemunha de Maré Baixa desaparecida.
- Ordem real fechando uma rua, galpão ou trecho do porto.

### Consequências

- Problemas no porto afetam abastecimento, reputação da Coroa, submundo de [[Maré Baixa]] e poder da Guilda.
- Se a Coroa endurecer o controle, a população pobre sofre primeiro.
- Se a Guilda for pressionada, pode retaliar por preço, escassez ou silêncio comercial.

### Decisões Pendentes do Sage

- Autoridade portuária.
- Rotas principais.
- Relação entre Coroa, Guarda Real e Guilda.
- Quanto o povo de Nimalis percebe da corrupção ou tensão econômica.
- Se a Guarda Real age por dever, medo, corrupção ou ignorância.

---

## Frente — Augustus Terra Decimus, Coroa e Véu

### Entidades Ligadas

- [[Augustus Terra Decimus]]
- [[Coroa de Nimalia]]
- [[Nobreza de Nimalia]]
- [[Guarda Real de Nimalia]]
- [[Igreja das Chamas]]
- [[Nimalis]]
- [[Nimalia]]
- [[Guilda dos Mercadores]]
- [[Culto dos Sussurrantes]]
- [[Véu Cinzento]]
- [[A Grande Fratura]]
- [[Criadores]]
- [[Raziel]]
- [[Varkh Nimalis]]
- [[Vezemir]]

### Status Atual

Augustus Terra Decimus é o rei soberano de [[Nimalia]] e a principal face institucional da [[Coroa de Nimalia]].

Na superfície, ele deve aparecer como monarca rígido, paladino idoso, devoto da [[Igreja das Chamas]] e governante de pulso de ferro.

No bastidor, Augustus representa o peso político da campanha: controle, censura, estabilidade, medo, fé institucional e possíveis verdades ocultas sobre o reino.

### O que está visível aos jogadores

- Augustus é o rei de [[Nimalia]].
- Governa a partir de [[Nimalis]].
- É ligado à [[Coroa de Nimalia]].
- É associado à [[Igreja das Chamas]].
- Possui reputação de monarca severo.
- A [[Guarda Real de Nimalia]] age em nome da ordem real.
- A nobreza o respeita publicamente.
- O povo comum o teme, respeita ou critica conforme sua posição social.
- A [[Guilda dos Mercadores]] mantém relação tensa e necessária com a Coroa.

### Segredos do Mestre

- Augustus sabe mais sobre o [[Véu Cinzento]] do que admite publicamente.
- A [[Coroa de Nimalia]] pode ter herdado, ocultado ou protegido um segredo antigo.
- A relação entre Coroa, Igreja, Véu e Criadores ainda não deve ser revelada.
- A ausência de herdeiro público pode ser apenas detalhe político ou sinal de algo maior.
- Augustus pode estar protegendo o reino de uma ameaça real, mesmo usando métodos autoritários.
- A [[Igreja das Chamas]] pode não ter controle total sobre ele.
- A [[Guilda dos Mercadores]] é tolerada por necessidade, não por confiança.
- O [[Culto dos Sussurrantes]] pode usar o medo da Coroa como ferramenta de recrutamento.
- A Guarda Real pode estar protegendo arquivos, prisioneiros ou locais cujo significado nem ela compreende totalmente.

### O Conhecimento sobre o Véu

Augustus possui, ou pode possuir, acesso a registros antigos, confissões de cultistas, mapas censurados, arquivos da [[Igreja das Chamas]] e documentos da Coroa que indicam que o [[Véu Cinzento]] não é apenas uma ameaça externa.

A versão pública diz:

> O Véu é perigo.

A versão secreta pode ser:

> O Véu é herança, prisão, ferida ou porta.

Augustus não quer que o povo descubra isso porque teme que medo vire culto, revolta, heresia ou colapso de autoridade.

### O Pecado da Coroa

Existe a possibilidade de que a [[Coroa de Nimalia]] tenha herdado, ocultado ou se beneficiado de algum pacto antigo ligado ao Véu, aos [[Criadores]], à [[A Grande Fratura]] ou à fundação política de [[Nimalia]].

Augustus pode não ser o autor desse pecado.

Mas é seu guardião atual.

E escolheu preservar o silêncio.

### A Fé em Crise

Augustus ainda acredita na [[Igreja das Chamas]], mas sua fé pode não ser serena.

Em segredo, ele pode se perguntar se a Chama revela a verdade ou apenas queima aquilo que a Coroa manda apagar.

Esse conflito não deve aparecer na nota pública como fato confirmado. Pode surgir em cenas de confronto moral, confissão, ritual, sonho ou crise.

### O Herdeiro Ausente

Augustus não possui esposa nem herdeiro público consolidado.

Isso cria instabilidade futura.

Possibilidades:

- recusou alianças matrimoniais para não submeter a Coroa às famílias nobres;
- perdeu alguém antes do início da campanha;
- possui herdeiro secreto;
- acredita que ninguém é digno de herdar o peso do trono;
- teme que sua linhagem carregue alguma marca ligada ao Véu;
- a sucessão está sendo disputada silenciosamente pela nobreza.

Nenhuma dessas opções deve virar cânone sem decisão do Sage.

### O Tirano Necessário

Augustus pode ter impedido catástrofes reais.

Algumas revoltas suprimidas podem ter sido manipuladas por cultos. Alguns estudiosos presos podem ter encontrado verdades perigosas. Alguns arquivos queimados podem ter evitado rituais.

Isso não absolve suas ações.

Mas impede que ele seja reduzido a caricatura.

### Verdades Possíveis

> [!question]- Escolher quando a campanha exigir
> Não tratar todas as opções como cânone ao mesmo tempo.

#### Opção A — O Guardião Trágico

Augustus sabe que existe uma ameaça real ligada ao Véu e acredita que sua tirania é o preço para manter Nimalia viva.

Ele está errado nos métodos, mas certo sobre o perigo.

#### Opção B — O Rei Manipulado

Augustus acredita controlar a verdade, mas parte das informações que recebe vem de conselheiros, sacerdotes ou nobres contaminados por interesses ocultos.

Ele é menos vilão e mais peça central de uma máquina contaminada.

#### Opção C — O Paladino Corrompido pela Ordem

Augustus começou como protetor verdadeiro, mas décadas de medo e poder transformaram sua fé em ferramenta de repressão.

Ele ainda fala em luz, mas já não percebe quantas sombras criou.

#### Opção D — O Último Selo

A linhagem Terra Decimus pode estar ligada a um juramento antigo de contenção.

Nesse caso, Augustus não é apenas rei: é parte viva de um mecanismo antigo.

Sua morte poderia enfraquecer algo que ninguém compreende totalmente.

#### Opção E — O Falso Leão

Augustus pode estar escondendo doença, maldição, pacto, desgaste espiritual ou dependência de uma relíquia.

Sua imagem pública de força talvez seja sustentada por ritual, fé, mentira política ou recurso antigo.

### Relações Secretas e Pressões

#### Com [[Varkh Nimalis]]

Augustus provavelmente não conhece Varkh pessoalmente no início.

Mas se o arco dos [[Remédios Falsos de Maré Baixa]] provocar crise pública, morte em massa ou instabilidade urbana, a Coroa pode transformar Varkh em:

- bode expiatório;
- testemunha forçada;
- informante;
- ferramenta;
- ameaça pública;
- peça descartável.

Para Augustus, Varkh não é importante até virar símbolo.

#### Com [[Raziel]]

Raziel é uma anomalia inaceitável para Augustus.

Um vampiro antigo, ligado à hemomancia, ao passado enterrado e a poderes anteriores à ordem atual, é exatamente o tipo de verdade que a Coroa tentaria destruir, prender ou usar.

Se Augustus descobrir quem Raziel é, dificilmente o tratará como criminoso comum.

Ele o tratará como arquivo vivo.

E arquivos vivos são perigosos.

#### Com [[Vezemir]]

Vezemir pode despertar respeito e desconfiança em Augustus.

É guerreiro, disciplinado, marcado por guerra e ligado a memórias antigas da [[Floresta de Avenor]]. Pode ser visto como arma útil ou risco livre demais.

Augustus reconhece guerreiros marcados pela perda.

Mas não confia em pessoas cuja lealdade maior está presa aos mortos.

### Função Real na Campanha

Augustus não deve ser tratado apenas como “rei tirano”.

Ele funciona melhor como antagonista institucional, patrono ambíguo ou muralha política. Pode estar certo sobre parte do perigo e errado sobre os métodos.

Seu papel é colocar os jogadores diante de perguntas difíceis:

- A Coroa protege Nimalia ou aprisiona Nimalia?
- Um rei pode esconder verdades para evitar pânico?
- Ordem ainda é virtude quando depende de silêncio?
- Se Augustus cair, o reino melhora ou se parte?
- O que acontece quando um governante cruel talvez esteja impedindo algo pior?

### Pistas

- Decreto real proibindo investigação sobre certos artefatos.
- Documento antigo com selo da Coroa e trecho apagado.
- Prisioneiro sem registro oficial.
- Sacerdote da [[Igreja das Chamas]] contradizendo a versão pública.
- Guarda Real removendo provas antes dos personagens chegarem.
- Arquivo real citando nome, linhagem ou símbolo ligado a um personagem.
- Nobre insinuando que Augustus sabe demais sobre todos.
- Relatório antigo mencionando cultistas, ruínas e “contenção da verdade”.
- Ordem sigilosa para confiscar qualquer peça ligada à [[Unidade DORN-7]].
- Selo real em documento ligado a uma carga falsificada.

### Rumores: Verdadeiros, Falsos ou Incompletos

| Rumor público | Natureza sugerida | Observação do Mestre |
|---|---|---|
| Augustus nunca dorme duas noites seguidas no mesmo aposento | Possivelmente verdadeiro | Pode indicar segurança real, paranoia ou medo de assassinato |
| A espada real foi abençoada pela primeira chama de Nimalia | Incompleto | Pode ser propaganda, relíquia ou ambos |
| Ele mantém prisioneiros sem registro | Possivelmente verdadeiro | Bom gancho para masmorras, arquivos ou desaparecidos |
| A Coroa queima livros perigosos | Parcialmente verdadeiro | Pode ser contenção de conhecimento |
| A Igreja das Chamas teme o rei tanto quanto o aconselha | Possivelmente verdadeiro | Indica tensão entre fé e trono |
| Augustus não possui herdeiro por causa do sangue Terra Decimus | Em aberto | Pode ser mentira, maldição ou intriga nobre |
| Ele conhece o nome de algo além do Véu | Em aberto | Usar apenas se o arco do Véu avançar |
| Ele já morreu uma vez e voltou por juramento | Em aberto | Pode ser lenda, milagre, mentira ou pacto |

### Condições de Revelação

Revelar partes desta frente apenas se:

- os personagens investigarem arquivos reais;
- houver audiência com Augustus;
- a Coroa intervier diretamente nos remédios falsos;
- o [[Culto dos Sussurrantes]] provocar crise pública;
- [[Raziel]] for identificado como criatura antiga;
- [[Vezemir]] ou [[Varkh Nimalis]] se tornarem símbolos políticos;
- a [[Guarda Real de Nimalia]] cometer abuso visível;
- um sacerdote da [[Igreja das Chamas]] romper silêncio;
- uma relíquia antiga contradizer a história oficial;
- a [[Unidade DORN-7]] registrar algo que a Coroa reconhece.

### Consequências

Se os personagens confrontarem Augustus ou a Coroa cedo demais:

- podem ser declarados criminosos;
- podem ser vigiados pela Guarda Real;
- podem perder acesso seguro a [[Nimalis]];
- podem ser usados por nobres rivais;
- podem ser manipulados pelo [[Culto dos Sussurrantes]];
- podem descobrir que parte da tirania de Augustus tinha motivo real;
- podem iniciar crise política antes de entender o tabuleiro.

### Decisões Pendentes do Sage

- Confirmar se Augustus é oficialmente antropo leonino.
- Definir se “O Leão da Chama” será epíteto canônico.
- Definir se ele terá herdeiro secreto, herdeiro ausente ou sucessão totalmente aberta.
- Definir o nível real de conhecimento dele sobre o [[Véu Cinzento]].
- Definir se sua fé na [[Igreja das Chamas]] é pura, política, abalada ou contaminada.
- Definir se a linhagem Terra Decimus possui ligação antiga com o Véu, Criadores ou Grande Fratura.
- Definir se ele será antagonista direto, patrono ambíguo ou figura trágica de fundo.
- Confirmar quais rumores são verdadeiros, falsos ou parcialmente verdadeiros.
- Definir até onde a Guarda Real sabe dos segredos da Coroa.

### Uso em Mesa pelo Mestre

- Augustus deve aparecer primeiro como peso institucional, não necessariamente em pessoa.
- Usar decretos, guardas, brasões, impostos, cerimônias e medo antes da audiência direta.
- Quando aparecer, ele deve transmitir majestade, cansaço e perigo.
- Evitar vilanizar cedo demais.
- Deixar os jogadores se perguntarem se ele é tirano, protetor ou os dois.
- Se ele lutar, a cena deve parecer julgamento, duelo ritual, defesa desesperada do trono ou colapso de uma ordem inteira.

---

## Frente — Varkh Nimalis

### Entidades Ligadas

- [[Varkh Nimalis]]
- [[O Frasco Afogado]]
- [[Mestre Odran Veyl]]
- [[Conclave dos Errantes]]
- [[Remédios Falsos de Maré Baixa]]
- [[Rede de Falsificadores de Maré Baixa]]

### Status Atual

Arco pessoal ligado à origem em [[Maré Baixa]], à alquimia de rua e à investigação dos remédios falsos.

### Segredos do Mestre

- A identidade de quem está usando os métodos de Odran ainda é desconhecida.
- A extensão real da fama de Varkh como assassino pode ser maior ou menor do que os rumores indicam.
- A classe mecânica definitiva de Varkh ainda precisa ser reconciliada com a ficha sem nome recebida do jogador.
- Varkh pode ser usado pela Coroa como bode expiatório se os remédios falsos virarem crise pública.

### Condições de Revelação

- Revelar por pistas em frascos.
- Revelar por testemunhas de Maré Baixa.
- Revelar por contato do Conclave.
- Revelar por retorno ao Frasco.
- Revelar se a Coroa ou a Guarda Real tentarem controlar a narrativa.

---

## Frente — Vezemir, Avenor e o Dragão

### Entidades Ligadas

- [[Vezemir]]
- [[Mira Valen]]
- [[Padre Oric]]
- [[Elarion Vaelthor]]
- [[Dragão de Colar Dourado]]
- [[Floresta de Avenor]]
- [[Leth'valora]]
- [[O Medalhão]]
- [[Grisalma]]
- [[Muralha de Dorn]]
- [[Guardiões do Véu Cinzento]]

### Status Atual

Frente pessoal de Vezemir e da destruição de [[Leth'valora]].
As notas principais devem mostrar memória, impacto e rumores sem explicar cedo demais o dragão, os Guardiões ou a origem dos sinais.

### Segredos do Mestre

- Relação completa entre Vezemir, o dragão, o medalhão, Grisalma e os Guardiões deve ser revelada em etapas.
- Detalhes do ataque a Leth'valora e do que Elarion/Mira/Oric sabiam ainda podem ser dosados.
- O Dragão de Colar Dourado deve permanecer parcialmente misterioso enquanto o jogador descobre pistas.
- [[O Medalhão]] pode estar ligado à verdadeira origem de Vezemir.
- [[Padre Oric]] desapareceu investigando conexões entre os Guardiões e o dragão de colar dourado.
- O dragão pode ter reconhecido Vezemir durante o ataque à vila.
- [[Elarion Vaelthor]] pode ter ocultado informações sobre seus pais biológicos.
- Existe a possibilidade de Vezemir descender de alguma linhagem élfica.

### Condições de Revelação

- Revelar por lembranças.
- Revelar por reações de relíquias.
- Revelar por viagem a Avenor.
- Revelar por rumores sobre Leth'valora.
- Revelar por contato com símbolos dos Guardiões.
- Revelar por reação da [[Unidade DORN-7]].

---

## Frente — Raziel, Gharok e Sangue Antigo

### Entidades Ligadas

- [[Raziel]]
- [[Clã Sanguinallis]]
- [[Fortaleza de Gharok]]
- [[Ruínas de Valthor]]
- [[Sangue Antigo]]
- [[Ancião Primordial]]
- [[Adagas de Espectro Fantasma]]
- [[Manto Primordial do Ancião]]

### Status Atual

Arco pessoal ligado a sangue antigo, traição, Gharok e estruturas anteriores ao presente.

### Segredos do Mestre

- O verdadeiro motivo pelo qual o Ancião Primordial libertou Raziel permanece desconhecido.
- A heresia rúnica usada como pretexto para sua captura ainda não foi definida.
- A forma como as [[Adagas de Espectro Fantasma]] permaneceram ligadas a Raziel durante o aprisionamento continua em aberto.
- Sua relação com o [[Véu Cinzento]] e com os [[Criadores]] ainda não foi confirmada.
- A sobrevivência atual, influência remanescente e função futura de Malakar, Kaelen e Vandor devem permanecer no bastidor.
- A relação exata entre Sanguinallis, Sangue Antigo e Raziel deve ser revelada por cenas, não por exposição.
- Se Augustus descobrir quem Raziel é, pode tentar prendê-lo, destruí-lo ou usá-lo como arquivo vivo.

### Condições de Revelação

- Revelar por reação a ruínas antigas.
- Revelar por sangue.
- Revelar por máquinas.
- Revelar por memórias fragmentadas.
- Revelar por antagonistas ligados a Gharok.
- Revelar por reação da Coroa.

---

## Frente — Culto dos Sussurrantes

### Entidades Ligadas

- [[Culto dos Sussurrantes]]
- [[Véu Cinzento]]
- [[Igreja das Chamas]]
- [[Coroa de Nimalia]]
- [[Augustus Terra Decimus]]

### Status Atual

Em revisão. Pode ser ameaça ativa, rumor distorcido, culto menor ou rascunho a arquivar.

### Segredos do Mestre

- Não confirmar ainda se o culto é ameaça ativa.
- Não revelar o Arauto Sombrio sem decidir se ele será mantido.
- Evitar usar o culto como explicação fácil para todo mistério do Véu.
- O culto pode usar o medo da Coroa para recrutar.
- O culto pode estar parcialmente certo sobre uma verdade antiga, mesmo sendo perigoso.

### Decisões Pendentes do Sage

- Confirmar existência canônica.
- Definir relação real com o [[Véu Cinzento]].
- Decidir se o Arauto Sombrio permanece, muda ou sai.
- Definir se o culto fica como facção, religião, rumor ou arquivo.
- Definir se Augustus sabe mais sobre o culto do que declara publicamente.

---

## Frente — Cosmologia, Véu e Criadores

### Entidades Ligadas

- [[Criadores]]
- [[O Fraturamento]]
- [[Eclipse de Obsidiana]]
- [[Véu Cinzento]]
- [[Guardiões do Véu Cinzento]]
- [[Ancião Primordial]]
- [[Sangue Antigo]]
- [[Vampiro Sanguinallis]]
- [[Unidade DORN-7]]
- [[Augustus Terra Decimus]]

### Status Atual

Frente de bastidor cosmológico.
As notas principais devem apresentar mitos, fenômenos, rumores e versões conhecidas sem resolver a verdade final do mundo.

### Segredos do Mestre

- A natureza real dos [[Criadores]] ainda está em definição.
- A cosmologia real do [[O Fraturamento]] não deve ser fechada publicamente.
- Causa, escala verdadeira e relação do [[Eclipse de Obsidiana]] com Criadores/Fraturamento permanecem em aberto.
- A natureza verdadeira do [[Véu Cinzento]] ainda está em construção.
- A função real dos [[Guardiões do Véu Cinzento]] ainda deve ser dosada.
- O [[Ancião Primordial]] pode ter objetivos próprios e planos ainda não definidos.
- Origem, custo real e consequências de longo prazo do [[Sangue Antigo]] ficam no bastidor.
- Diferenças entre vampirismo comum e [[Vampiro Sanguinallis]] devem ser reveladas gradualmente.
- A [[Coroa de Nimalia]] pode guardar arquivos antigos sobre essas verdades.
- Augustus pode estar praticando contenção política de conhecimento cosmológico.

### Condições de Revelação

- Revelar por ruínas antigas.
- Revelar por reação de Raziel.
- Revelar por sinais do Véu.
- Revelar por registros pré-cataclísmicos.
- Revelar por cultos.
- Revelar por máquinas antigas.
- Revelar por eventos ligados ao primeiro capítulo.
- Revelar por arquivos confiscados pela Coroa.

### Decisões Pendentes do Sage

- Natureza real dos Criadores.
- Papel do Véu na criação, corrupção ou proteção do mundo.
- Custo narrativo do Sangue Antigo.
- Relação entre Ancião Primordial, Sanguinallis e estruturas antigas.
- Relação entre Coroa, Igreja das Chamas e contenção da verdade.

---

## Frente — Religiões e Doutrinas

### Entidades Ligadas

- [[RELIGION]]
- [[Igreja das Chamas]]
- [[Fé dos Antigos]]
- [[Caminho dos Errantes]]
- [[Culto dos Sussurrantes]]
- [[Clérigo]]
- [[Augustus Terra Decimus]]

### Status Atual

Frente de crenças públicas e tensões espirituais.
As notas principais devem mostrar prática, imagem pública e uso em mesa sem confirmar verdades metafísicas.

### Segredos do Mestre

- Verdades antigas, cultos perigosos e manipulações institucionais ficam no Estado da Campanha.
- Possíveis contradições doutrinárias da [[Igreja das Chamas]] ainda precisam ser confirmadas.
- A relação real da [[Fé dos Antigos]] com os Criadores está em aberto.
- O [[Caminho dos Errantes]] pode ter ligação com ciclos reais, destino ou memória, mas isso não está fechado.
- Segredos religiosos ligados à classe [[Clérigo]] ainda não estão consolidados.
- A fé de Augustus pode estar em crise, mas isso não deve aparecer como fato público.
- A [[Igreja das Chamas]] pode temer o rei tanto quanto o aconselha.

### Condições de Revelação

- Revelar por sermões.
- Revelar por relíquias.
- Revelar por conflitos entre crenças.
- Revelar por milagres ambíguos.
- Revelar por registros antigos.
- Revelar por contato com o Véu.
- Revelar por audiência ou confissão envolvendo Augustus.

### Decisões Pendentes do Sage

- Quais crenças são canônicas como religião ativa.
- O que é verdade, interpretação ou mentira institucional.
- Como clérigos acessam poder no cenário.
- Definir a relação real entre Chama, Coroa e Véu.

---

## Frente — Povos, Reinos e Classes

### Entidades Ligadas

- [[Antropo]]
- [[Anão]]
- [[Dragonborn]]
- [[Elfo]]
- [[Halfling]]
- [[Humano]]
- [[Kenku]]
- [[Vampiro]]
- [[Alquimista]]
- [[Guerreiro]]
- [[Ladrão]]
- [[Mago]]
- [[Paladino]]

### Status Atual

Frente de bastidores culturais, linhagens e limites mecânicos.
Notas principais devem ser úteis aos jogadores sem entregar política futura, linhagens ocultas ou segredos de classe.

### Segredos do Mestre

- Linhagens específicas de antropos, humanos e meio-elfos podem esconder tradições, pactos ou rivalidades locais.
- Obras anãs antigas podem guardar segredos de eras anteriores.
- Reino élfico, reino dragonborn e suas políticas ainda serão revelados.
- Vozes imitadas por kenkus podem virar pista ou arma social.
- Origem, limites e consequências do vampirismo/Sangue Antigo ficam no bastidor.
- Limites de alquimia perigosa, magia antiga, vínculos criminais e ajustes específicos de classe ficam pendentes até uso em mesa.
- A linhagem Terra Decimus pode esconder tradição, maldição, pacto, juramento ou função antiga.

### Condições de Revelação

- Revelar por origem de personagem.
- Revelar por viagem a reinos raciais.
- Revelar por ruínas.
- Revelar por tutores.
- Revelar por falhas de magia.
- Revelar por contatos de classe.
- Revelar por consequências de uso perigoso.

### Decisões Pendentes do Sage

- Quais reinos raciais entram primeiro em jogo.
- Quais linhagens têm segredo real.
- Quais limites mecânicos entram em Old Dragon sem quebrar nível baixo.
- Definir se a linhagem Terra Decimus é apenas política ou possui peso antigo real.

---

# DOSSIÊ DO MESTRE — CAPÍTULO 01: ECOS DO MUNDO PERDIDO

#### _Crônicas de [[EARTHROPO/EARTHROPO|Earthropo]] — capítulo em preparação_

> [!NOTE|clean no-i right]+ 01 - Ecos do Mundo Perdido
> ![[zz_media/covers/banner_ecos_do_mundo_perdido.png|400]]

> [!world]- SINOPSE
> O primeiro capítulo aproxima [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]].
> Uma caravana sofre um acidente depois de um tremor localizado, frascos de remédios falsificados se quebram e uma passagem artificial surge sob a terra.
> O que parecia contrabando comum revela sinais de tecnologia antiga, símbolos ligados ao [[Véu Cinzento]] e ecos de estruturas esquecidas sob Earthropo.

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

---

## A Unidade DORN-7

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

### Frases possíveis

> “Setor comprometido.”

> “Autoridade de reconstrução ausente.”

> “Identifiquem-se.”

> “Ciclos excedidos.”

> “Registro de superfície indisponível.”

> “Núcleo local sem resposta.”

> “Material contaminado detectado.”

> “Uso indevido de componente médico.”

> “A contenção foi violada.”

> “A superfície permanece habitável?”

> “Onde estão os responsáveis pelo setor?”

> “Este local deveria permanecer selado.”

---

## Conexão com Cada Personagem

### [[Vezemir]]

Vezemir pode notar que algumas marcas no local lembram símbolos associados aos [[Guardiões do Véu Cinzento]], mas em uma versão mais antiga, incompleta ou distorcida.

A [[Unidade DORN-7]] também pode reagir à presença de Vezemir de forma estranha, como se identificasse nele traços de exposição prolongada a algo ligado ao Véu, às ruínas ou ao dragão.

Frase possível:

> “Resíduo de ruptura detectado.”

### [[Varkh Nimalis]]

Varkh reconhece nos frascos falsos elementos do método de [[Mestre Odran Veyl]], mas adulterados por alguém que não dominava a técnica original.

A [[Unidade DORN-7]] identifica os frascos como “material médico contaminado” ou “componente clínico corrompido”.

Isso dá a Varkh uma pista concreta:

> os falsificadores estão usando restos antigos como matéria-prima.

### [[Raziel]]

Raziel pode sentir que a estrutura pertence a uma camada de mundo anterior ao presente.

A [[Unidade DORN-7]] pode reagir a Raziel com uma falha específica:

> “Registro biológico incompatível.”

Ou:

> “Assinatura vital instável.”

Isso não explica Raziel.

Apenas cria tensão.

---

## Primeiro Conflito Prático

Depois que a [[Unidade DORN-7]] desperta, três problemas acontecem quase ao mesmo tempo:

1. a estrutura começa a colapsar;
2. a Guarda Real se aproxima da entrada;
3. alguém tenta roubar uma peça ou documento da carga.

Os personagens precisam decidir o que priorizar:

- salvar feridos;
- impedir a fuga dos falsificadores;
- conversar com a unidade;
- esconder a descoberta;
- chamar reforços;
- fugir antes que sejam culpados;
- proteger a passagem;
- impedir que a Guarda tome tudo.

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

# SEGREDOS CENTRALIZADOS DE PERSONAGENS E ENTIDADES

> [!WARNING]
> Conteúdo movido das notas de personagem e entidade para manter o vault operacionalmente público.
> Revisar e consolidar depois.

---

## [[Augustus Terra Decimus]]

- Augustus sabe mais sobre o [[Véu Cinzento]] do que admite publicamente.
- A [[Coroa de Nimalia]] pode ter herdado, ocultado ou protegido um segredo antigo.
- A relação entre Coroa, Igreja, Véu e Criadores ainda não deve ser revelada.
- A ausência de herdeiro público pode ser apenas detalhe político ou sinal de algo maior.
- Augustus pode estar protegendo o reino de uma ameaça real, mesmo usando métodos autoritários.
- A [[Igreja das Chamas]] pode não ter controle total sobre ele.
- A [[Guilda dos Mercadores]] é tolerada por necessidade, não por confiança.
- O [[Culto dos Sussurrantes]] pode usar o medo da Coroa como ferramenta de recrutamento.
- Se Augustus descobrir quem [[Raziel]] é, pode tratá-lo como arquivo vivo.
- Se os remédios falsos virarem crise pública, a Coroa pode usar [[Varkh Nimalis]] como bode expiatório.
- [[Vezemir]] pode ser visto por Augustus como arma útil ou risco livre demais.
- A linhagem Terra Decimus pode estar ligada a juramento antigo, maldição, pacto ou função de contenção.
- O rei pode ser guardião trágico, manipulado, corrompido pela ordem, último selo ou falso leão. Não confirmar sem decisão do Sage.

---

## [[Elarion Vaelthor]]

- Sabia muito mais sobre a origem de [[Vezemir]] do que jamais revelou.
- Possivelmente possuía ligações com os [[Guardiões do Véu Cinzento]].
- Demonstrava preocupação incomum com a magia que habitava o jovem meio-elfo.
- Pode ter escondido documentos, artefatos ou registros em [[Leth'valora]].
- Seu desaparecimento ocorreu pouco tempo após a partida de Vezemir.

---

## [[Raziel]]

- O verdadeiro motivo pelo qual o [[Ancião Primordial]] libertou Raziel permanece desconhecido.
- A heresia rúnica usada como pretexto para sua captura ainda não foi definida.
- A forma como as [[Adagas de Espectro Fantasma]] permaneceram ligadas a Raziel durante o aprisionamento continua em aberto.
- Sua relação com o [[Véu Cinzento]] e com os [[Criadores]] ainda não foi confirmada.
- A reação de estruturas antigas a Raziel deve criar tensão, não explicação completa.

---

## [[Unidade DORN-7]]

- A [[Unidade DORN-7]] não é única.
- Ela fazia parte de uma rede antiga sob Earthropo.
- A ativação dela foi causada por reagente antigo presente nos remédios falsificados.
- Ela pode reconhecer traços incomuns em [[Vezemir]], [[Varkh Nimalis]] ou [[Raziel]], mas não deve explicar tudo.
- Ela não reconhece a Coroa, a Guarda Real ou reinos modernos.
- Seu mapa fragmentado aponta para outro setor ativo.

---

## [[Varkh Nimalis]]

- A identidade de quem está usando os métodos de Odran ainda é desconhecida.
- O envolvimento de Odran com as falsificações, caso exista, ainda não foi definido.
- A extensão real da fama de Varkh como assassino pode ser maior ou menor do que os rumores indicam.
- A classe mecânica definitiva de Varkh ainda precisa ser reconciliada com a ficha sem nome recebida do jogador.
- O arco de Varkh pode escalar de investigação de rua para crise política se a Coroa intervier.

---

## [[Vezemir]]

- [[O Medalhão]] pode estar ligado à verdadeira origem de Vezemir.
- [[Padre Oric]] desapareceu investigando conexões entre os Guardiões e o dragão de colar dourado.
- O dragão demonstrou reconhecer Vezemir durante o ataque à vila.
- [[Elarion Vaelthor]] pode ter ocultado informações sobre seus pais biológicos.
- Existe a possibilidade de Vezemir descender de alguma linhagem élfica.
- As relíquias de Vezemir devem reagir em camadas, sem explicar tudo cedo demais.

---

# DECISÕES PENDENTES GERAIS DO SAGE

- Definir ponto inicial da mesa.
- Definir quem está na caravana.
- Definir quem está transportando os remédios falsos.
- Definir qual símbolo antigo aparece nos frascos.
- Definir se a Guarda Real chega antes ou depois do despertar da [[Unidade DORN-7]].
- Definir quais pistas aparecem no primeiro encontro.
- Decidir se a [[Unidade DORN-7]] fica consciente no fim da sessão ou desliga temporariamente.
- Confirmar se Augustus é oficialmente antropo leonino.
- Definir se “O Leão da Chama” será epíteto canônico.
- Definir o nível real de conhecimento de Augustus sobre o [[Véu Cinzento]].
- Definir se a linhagem Terra Decimus possui segredo antigo.
- Confirmar o papel real de Odran nas falsificações.
- Confirmar o grau de envolvimento da Guilda e da Coroa nos remédios falsos.
- Definir a natureza real dos [[Criadores]].
- Definir o custo narrativo do [[Sangue Antigo]].
- Definir quais verdades religiosas são reais, interpretadas ou manipuladas.

---

# USO EM MESA

- **Como usar esta nota:** abrir antes e durante a sessão para consultar frentes, segredos, pistas e consequências.
- **O que não fazer:** ler trechos diretamente para jogadores.
- **O que mostrar:** apenas descrições player-safe vindas das notas públicas ou adaptadas em fala de mesa.
- **Ritmo recomendado:** começar por problema concreto; revelar lore por reação, pista e consequência.
- **Tom da campanha:** fantasia medieval com ruínas antigas, política de Coroa, fé institucional, investigação urbana e segredos enterrados.
- **Regra de ouro:** cada revelação deve abrir uma pergunta maior, não fechar o universo inteiro.
