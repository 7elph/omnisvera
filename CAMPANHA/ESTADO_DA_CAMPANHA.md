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

## Painel de Controle do Vault

| Área | Acesso rápido | Uso |
|---|---|---|
| Home do Mestre | [[Home_Mestre]] | navegação visual e atalhos |
| Home dos Jogadores | [[Home]] | consulta player-safe |
| Capítulos | [[01 - Ecos do Mundo Perdido]] | versão pública/jogável do capítulo |
| Roteiro da Sessão 01 | [[SESSAO_01_ROTEIRO_DE_MESA]] | condução prática da próxima mesa |
| Fila de Conteúdo | [[Workflow/Content_Development/CONTENT_CREATION_QUEUE]] | notas que precisam desenvolvimento |
| Modelo Player-Safe | [[Workflow/Content_Development/PLAYER_SAFE_ENTITY_MODEL]] | regra de separação entre nota pública e bastidor |

> [!todo]- Regras Jogáveis — Classes e Raças
> - [[Antropo|Antropos]] são o nome canônico de Omnisvera para beastfolk.
> - Homem-Tigre é base mecânica/referência para antropos felinos, não nome comum do cenário.
> - [[Kenku]] é raça jogável de [[Varkh Nimalis]] e também uma linhagem específica dentro do guarda-chuva antropo.
> - [[Alquimista]] usa o suplemento Old Dragon — Expansão de Classes como base jogável.
> - [[Guerreiro]] está consolidado como classe marcial de [[Vezemir]].
> - [[Hemomante]] está consolidado como classe de sangue de [[Raziel]].
> - [[Vampiro]] é raça/condição de [[Raziel]], não classe.
> - [[Dragonborn]] possui base mecânica Omnisvera para teste de mesa.
> - Varkh combina [[Kenku]] + [[Alquimista]].
> - Homúnculos, Pedra Filosofal, Quimeras e transmutações avançadas devem ser controlados pelo mestre antes de aparecerem em mesa.
> - Regras perigosas ou de nível alto ficam disponíveis como opção, não como promessa automática.

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
- **Roteiro de mesa:** [[SESSAO_01_ROTEIRO_DE_MESA]]
- **Situação inicial provável:** estrada secundária entre [[Nimalis]] e [[Floresta de Avenor]].
- **Foco de mesa:** unir [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente comum.
- **Cena-motor:** uma caravana sofre acidente, frascos falsificados quebram e uma passagem antiga é revelada sob a estrada.
- **Mistério inicial:** os remédios falsos carregam algo que não é apenas alquimia.
- **Escalada:** a [[Unidade DORN-7]] desperta parcialmente.

## Próxima Sessão — Decisões Aplicadas

- **Local inicial:** estrada entre [[Nimalis]] e [[Floresta de Avenor]].
- **Caravana:** parece formada por mercadores comuns; no bastidor, há selo, contrato ou documento que sugere proteção indireta da [[Coroa de Nimalia]].
- **Remédios falsos:** transporte facilitado por um agente menor da [[Guilda dos Mercadores]]; a pessoa carregando os frascos não sabe o que leva.
- **Guarda Real:** a [[Guarda Real de Nimalia]] chega no fim da sessão, como pressão, complicação ou cliffhanger.
- **DORN-7:** a [[Unidade DORN-7]] termina parcialmente ativa, danificada e seguindo os personagens.
- **Símbolo inicial:** os frascos apontam primeiro para [[Mestre Odran Veyl]], mas há sinais de adulteração.
- **Tom:** investigação sombria + exploração.
- **Final ideal:** mapa fragmentado aponta outro setor, enquanto um falsificador escapa com prova importante.
- **Mistério:** os jogadores entendem pouco no sentido cosmológico, mas percebem a existência de uma rede subterrânea antiga ou estrutura maior.

### Objetivo de Mesa

Unir os personagens por consequência, não por amizade instantânea.

Eles não precisam confiar uns nos outros.

Só precisam perceber que estão presos no mesmo problema.

### Preparar Antes da Sessão

- Revisar [[SESSAO_01_ROTEIRO_DE_MESA]].
- Ajustar ou confirmar os três NPCs descartáveis da caravana.
- Confirmar quais pistas iniciais serão usadas.
- Preparar a chegada final da [[Guarda Real de Nimalia]] como pressão política, não como interrupção do primeiro contato.
- Decidir, se necessário, qual prova específica escapa com o falsificador.

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

```datacards
TABLE cover, quest_status, location, faction
FROM "CAMPANHA/Quests"
WHERE type != "index"
AND quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

### Rumores Ativos

```datacards
TABLE cover, status, visibility, spoiler_level
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

## Dossiês do Mestre

| Dossiê | Quando abrir |
|---|---|
| [[SESSAO_01_ROTEIRO_DE_MESA]] | condução direta da próxima sessão |
| [[DOSSIE - Capitulo 01 e DORN-7]] | preparação da sessão, incidente da estrada, DORN-7 e final com mapa fragmentado |
| [[DOSSIE - Remedios Falsos e Odran]] | O Frasco Afogado, símbolos adulterados, Odran, Varkh e falsificações |
| [[DOSSIE - Coroa Augustus e Nimalis]] | Coroa, Guarda Real, Augustus, Nimalis, arquivos restritos e pressão política |
| [[DOSSIE - Personagens Jogadores e Arcos Pessoais]] | Varkh, Vezemir, Raziel e entradas individuais no arco |
| [[DOSSIE - Cosmologia Veu Criadores e Religioes]] | Véu, Criadores, culto, religiões, povos e segredos de mundo |
| [[DOSSIE - Segredos Centrais e Pendencias]] | verdades possíveis, pendências do Sage e segredos de longo prazo |

## P0 — Próxima Sessão

### Capítulo 01 — Ecos do Mundo Perdido

- **Agora:** estrada entre [[Nimalis]] e [[Floresta de Avenor]], caravana comercial comum, remédios falsos e passagem antiga.
- **Mesa:** investigação sombria + exploração.
- **Não revelar:** origem total da estrutura, cosmologia, Véu, Criadores ou rede subterrânea.
- **Dossiê:** [[DOSSIE - Capitulo 01 e DORN-7]].

### DORN-7

- **Agora:** entidade antiga danificada desperta parcialmente.
- **Uso:** tensão, falas quebradas, detecção de material contaminado, mapa fragmentado.
- **Fim da sessão:** DORN-7 segue os personagens de forma limitada e perigosa.
- **Dossiê:** [[DOSSIE - Capitulo 01 e DORN-7]].

### Remédios Falsos e O Frasco Afogado

- **Agora:** frascos apontam para [[Mestre Odran Veyl]], mas há adulteração.
- **Mesa:** Varkh percebe que alguém imitou ou corrompeu o método de Odran.
- **Não confirmar:** culpa de Odran, Guilda inteira ou Coroa.
- **Dossiê:** [[DOSSIE - Remedios Falsos e Odran]].

### Guarda Real

- **Agora:** chega no fim, não interrompe o primeiro contato com DORN-7.
- **Uso:** isolar área, controlar testemunhas, pressionar politicamente, confiscar provas.
- **Não revelar:** quanto a Coroa sabe.
- **Dossiê:** [[DOSSIE - Coroa Augustus e Nimalis]].

## P1 — Primeiro Arco

### Coroa, Augustus e Nimalis

- **Agora:** pano de fundo político.
- **Uso:** autoridade, estabilidade, arquivos restritos, medo público e pressão institucional.
- **Player-safe:** Augustus aparece como rei severo, paladino idoso e símbolo da ordem.
- **Dossiê:** [[DOSSIE - Coroa Augustus e Nimalis]].

### Personagens Jogadores

- **Varkh:** Odran, remédios falsos, reputação e Maré Baixa.
- **Vezemir:** Avenor, Leth'valora, dragão e passado perdido.
- **Raziel:** estruturas antigas, anomalia e vingança antiga.
- **Dossiê:** [[DOSSIE - Personagens Jogadores e Arcos Pessoais]].

## P2 — Cosmologia / Futuro

- **Véu, Criadores e Fraturamento:** manter como mistério gradual.
- **Religiões profundas:** não transformar em verdade fechada cedo demais.
- **Povos, reinos e classes:** estruturar quando afetarem mesa ou criação de personagem.
- **Dossiê:** [[DOSSIE - Cosmologia Veu Criadores e Religioes]].

## Pendências Rápidas do Sage

> [!todo]- Agora
> - Revisar as pistas iniciais em [[SESSAO_01_ROTEIRO_DE_MESA]].
> - Confirmar se os NPCs descartáveis da caravana serão usados como estão.
> - Definir qual prova o falsificador leva no final da sessão.

> [!todo]- Depois
> - Confirmar papel real de [[Mestre Odran Veyl]] nas falsificações.
> - Confirmar grau de envolvimento da [[Guilda dos Mercadores]] e da [[Coroa de Nimalia]].
> - Confirmar se Augustus é oficialmente antropo leonino.
> - Definir se “O Leão da Chama” ou “O Leão de Nimalia” será epíteto canônico.

> [!abstract]- Talvez / Segredos futuros
> - Segredo da linhagem Terra Decimus.
> - Natureza real dos [[Criadores]].
> - Custo narrativo do [[Sangue Antigo]].
> - Verdades religiosas reais, interpretadas ou manipuladas.

---

## Uso em Mesa

- **Como usar esta nota:** abrir antes e durante a sessão para consultar frentes, segredos, pistas e consequências.
- **O que não fazer:** ler trechos diretamente para jogadores.
- **O que mostrar:** apenas descrições player-safe vindas das notas públicas ou adaptadas em fala de mesa.
- **Ritmo recomendado:** começar por problema concreto; revelar lore por reação, pista e consequência.
- **Tom da campanha:** fantasia medieval com ruínas antigas, política de Coroa, fé institucional, investigação urbana e segredos enterrados.
- **Regra de ouro:** cada revelação deve abrir uma pergunta maior, não fechar o universo inteiro.
