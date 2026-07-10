# Validação — Hybrid RAG do Omnisvera Companion

## Configuração

- RAG mode: `hybrid`
- Modelo principal: `omnisvera-local:latest`
- Modelo de embeddings: `nomic-embed-text`
- Índice semântico: `C:\Users\delib\Desktop\OMNISVERA\.local-index\vault.jsonl`

## Consulta exata

- Pergunta: `Varkh Nimalis`
- Resultados recuperados: 8

| Rank | Arquivo | Tipo | Visibilidade | Exact | Lexical | Semantic | Final | Trecho |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | `Characters/Individual/Varkh Nimalis.md` | character | Público | 1000.00 | 670.00 | 0.7660 | 1884.49 | # VARKH NIMALIS — O CORVO DA MARÉ BAIXA |
| 2 | `Locations/Nimalis.md` | location | Jogadores | 160.00 | 171.00 | 0.5496 | 484.90 | # Capital de Nimalia Capital do Reino de Nimalia e sede da Coroa de Nimalia, governada pelo rei soberano Augustus Terra Decimus. A cidade é representada em MAPA... |
| 3 | `Items/Máscara de Médico da Peste de Varkh.md` | item | Jogadores | 160.00 | 183.00 | 0.0000 | 343.00 | # Máscara de Médico da Peste de Varkh A máscara de médico da peste de Varkh Nimalis mistura proteção, intimidação e identidade. Adaptada ao corpo kenku, ela aju... |
| 4 | `MAPA DE NIMALIS.md` | map | Jogadores | 160.00 | 127.00 | 0.0000 | 287.00 | # MAPA DE NIMALIS Mapa oficial da capital Nimalis. Este mapa representa a cidade capital, não todo o território do reino. ## Marcadores Maré Baixa e Porto de Ni... |
| 5 | `Locations/Maré Baixa.md` | location | Jogadores | 0.00 | 71.00 | 0.5791 | 233.15 | ### O Frasco Afogado Pequena loja de alquimia perto do porto, pertencente ao velho Odran Veyl. Vende tônicos, pomadas, antídotos, calmantes, venenos fracos para... |
| 6 | `Characters/Individual/Mestre Odran Veyl.md` | character | Público | 0.00 | 41.00 | 0.6141 | 212.94 | # Mestre Odran Veyl Alquimista veterano de Maré Baixa, proprietário do estabelecimento conhecido como **O Frasco Afogado** e mentor de Varkh Nimalis. |
| 7 | `Locations/Casa da Moeda de Nimalia.md` | location | Jogadores | 0.00 | 32.00 | 0.6062 | 201.74 | # Casa da Moeda de Nimalia Instituição localizada na Nimalis e responsável pela produção das moedas oficiais do reino. |
| 8 | `EARTHROPO/01 - Ecos do Mundo Perdido.md` | story | Jogadores | 0.00 | 41.00 | 0.5534 | 195.95 | ## Premissa de trabalho Vezemir, Varkh e Raziel encontram sinais de que relíquias, falsificações alquímicas e ruínas antigas podem compartilhar uma origem ligad... |

## Consulta semântica

- Pergunta: `quem está usando remédios adulterados?`
- Resultados recuperados: 8

| Rank | Arquivo | Tipo | Visibilidade | Exact | Lexical | Semantic | Final | Trecho |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | `Territories/Floresta de Avenor.md` | territory | Jogadores | 0.00 | 168.00 | 0.6112 | 339.13 | #### Estrada Esquecida Antiga rota comercial abandonada há séculos. Hoje está tomada pela vegetação e por ruínas do velho mundo. Foi próximo a essa estrada que... |
| 2 | `CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md` | quest | Jogadores | 160.00 | 165.00 | 0.0000 | 325.00 | # Investigar Remédios Falsos de Maré Baixa ## Gancho Público Remédios falsos começaram a circular em Nimalia, especialmente entre viajantes, trabalhadores pobre... |
| 3 | `CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md` | rumor | Jogadores | 160.00 | 141.00 | 0.0000 | 301.00 | # 02 - Remédios Falsos da Maré Baixa Remédios falsos circulam em Nimalia usando o símbolo e os métodos de Odran. Pessoas compram cura e recebem veneno. Document... |
| 4 | `CAMPANHA/Rumors/05 - A Guarda Real Está Fechando Rotas.md` | rumor | Jogadores | 160.00 | 141.00 | 0.0000 | 301.00 | # 05 — A Guarda Real Está Fechando Rotas Viajantes comentam que patrulhas da Guarda Real de Nimalia estão mais rígidas nas saídas de Nimalis e em trechos de est... |
| 5 | `CAMPANHA/Rumors/04 - O Frasco Afogado Está Silencioso.md` | rumor | Jogadores | 160.00 | 132.00 | 0.0000 | 292.00 | # 04 — O Frasco Afogado Está Silencioso Há quem diga que O Frasco Afogado anda quieto demais para uma loja acostumada a cheiro de ervas, álcool barato e panela... |
| 6 | `Characters/Individual/Varkh Nimalis.md` | character | Público | 0.00 | 50.00 | 0.6348 | 227.75 | ## Atualidade Remédios falsos começaram a circular em Nimalia usando o símbolo e os métodos de Odran. Pessoas compram cura e recebem veneno. Documentos surgem c... |
| 7 | `Classes/Alquimista.md` | class | Jogadores | 0.00 | 44.00 | 0.6428 | 223.98 | ### Tomo Alquímico Registra receitas, experiências, círculos e descobertas. Um alquimista pode aprender com o tomo de outro praticante. |
| 8 | `Characters/Individual/Vezemir.md` | character | Público | 0.00 | 41.00 | 0.6057 | 210.59 | ## Aparência Com 2,02 m de altura, Vezemir é alto e musculoso. Possui cabelos e pele muito claros, olhos verdes e uma cicatriz vertical que cruza o rosto da tes... |

### Resposta estruturada

- Ollama usado: `False`
- Retrieval: `rag:hybrid`
- Fontes: `CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md`, `CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md`, `CAMPANHA/Rumors/05 - A Guarda Real Está Fechando Rotas.md`, `CAMPANHA/Rumors/04 - O Frasco Afogado Está Silencioso.md`, `Characters/Individual/Varkh Nimalis.md`

```json
{
  "fatos_confirmados": [],
  "teorias": [
    {
      "teoria": "Há pistas investigáveis, mas o responsável ainda não foi confirmado nas informações liberadas.",
      "base": [
        "CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md",
        "CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md",
        "CAMPANHA/Rumors/04 - O Frasco Afogado Está Silencioso.md"
      ]
    }
  ],
  "informacoes_insuficientes": [
    "Quem está por trás ainda não foi revelado."
  ],
  "resposta_ao_jogador": "Ainda não há confirmação liberada sobre quem está por trás dos remédios adulterados. O que se sabe é que há frascos falsos circulando, sinais ligados aos métodos de Odran e indícios de adulteração. Isso aponta para uma investigação, não para um culpado fechado."
}
```

## Consulta sobre local

- Pergunta: `o que existe em Maré Baixa?`
- Resultados recuperados: 8

| Rank | Arquivo | Tipo | Visibilidade | Exact | Lexical | Semantic | Final | Trecho |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | `Locations/Maré Baixa.md` | location | Jogadores | 160.00 | 343.00 | 0.7696 | 718.49 | # Maré Baixa Maré Baixa fica no extremo sul da capital do Reino de Nimalia, espremida entre os muros da cidade e o cheiro salgado do porto. E um amontoado de pa... |
| 2 | `Characters/Individual/Varkh Nimalis.md` | character | Público | 160.00 | 187.00 | 0.6646 | 533.09 | ## Visão Geral **Títulos:** O Corvo da Maré Baixa **Apelido:** O Corvo **Localização Atual:** Em viagem pelo Reino de Nimalia **Território:** Nimalia **Reputaçã... |
| 3 | `CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md` | quest | Jogadores | 160.00 | 292.00 | 0.0000 | 452.00 | # Investigar Remédios Falsos de Maré Baixa ## Gancho Público Remédios falsos começaram a circular em Nimalia, especialmente entre viajantes, trabalhadores pobre... |
| 4 | `CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md` | rumor | Jogadores | 160.00 | 250.00 | 0.0000 | 410.00 | # 02 - Remédios Falsos da Maré Baixa Remédios falsos circulam em Nimalia usando o símbolo e os métodos de Odran. Pessoas compram cura e recebem veneno. Document... |
| 5 | `Characters/Individual/Mestre Odran Veyl.md` | character | Público | 0.00 | 14.00 | 0.7187 | 215.24 | # Mestre Odran Veyl Alquimista veterano de Maré Baixa, proprietário do estabelecimento conhecido como **O Frasco Afogado** e mentor de Varkh Nimalis. |
| 6 | `Classes/Alquimista.md` | class | Jogadores | 0.00 | 35.00 | 0.6272 | 210.63 | ## Estrutura básica - **Dado de Vida:** d6. - **Armaduras:** couro e escudo pequeno; proteções mais pesadas impedem o uso da alquimia. - **Armas:** pequenas e d... |
| 7 | `Territories/Nimalia.md` | territory | Jogadores | 0.00 | 8.00 | 0.7131 | 207.68 | #### Bairro dos Anões Lugar onde os anões se estabeleceram na cidade. --- |
| 8 | `Races/Kenku.md` | race | Jogadores | 0.00 | 20.00 | 0.6695 | 207.46 | ## No Reino de Nimalia Na capital do Reino de Nimalia, kenkus costumam circular em bairros portuários, mercados, guildas menores e redes de informação informal.... |

## Consulta sem evidência

- Pergunta: `quem é o imperador secreto de Nimalia?`
- Resultados recuperados: 8

| Rank | Arquivo | Tipo | Visibilidade | Exact | Lexical | Semantic | Final | Trecho |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | `Factions/Coroa de Nimalia.md` | faction | Jogadores | 160.00 | 174.00 | 0.7143 | 533.99 | # Coroa de Nimalia A nobreza e monarquia do Reino de Nimalia, o principal reino dos antropos em Earthropo. Controlam as terras e o exército do reino. |
| 2 | `Territories/Nimalia.md` | territory | Jogadores | 160.00 | 174.00 | 0.6973 | 529.25 | # REINO DE NIMALIA Overview Nimalia é o reino dos antropos apresentado até agora em Earthropo. Reúne diferentes povos beastfolks sob a autoridade de Augustus Te... |
| 3 | `Locations/Casa da Moeda de Nimalia.md` | location | Jogadores | 160.00 | 156.00 | 0.7514 | 526.39 | # Casa da Moeda de Nimalia Instituição localizada na Nimalis e responsável pela produção das moedas oficiais do reino. |
| 4 | `Factions/Guarda Real de Nimalia.md` | faction | Jogadores | 160.00 | 174.00 | 0.6586 | 518.40 | # GUARDA REAL DE NIMALIA A consulta abaixo permanecerá vazia enquanto nenhum personagem confirmado receber a tag `guarda`. O comandante registrado continua apen... |
| 5 | `MAPA DE NIMALIA.md` | map | Jogadores | 160.00 | 160.00 | 0.6571 | 503.98 | # MAPA DA CAPITAL DO REINO DE NIMALIA O nome da Nimalis ainda não foi definido. Este mapa representa a cidade capital, não todo o território do reino. A palavra... |
| 6 | `Factions/Nobreza de Nimalia.md` | faction | Jogadores | 160.00 | 168.00 | 0.0000 | 328.00 | # Nobreza de Nimalia A Nobreza de Nimalia reúne casas influentes do reino, especialmente próximas à corte de Nimalis, ao Bairro Nobre, aos impostos, ao exército... |
| 7 | `Locations/Porto de Nimalia.md` | location | Jogadores | 160.00 | 135.00 | 0.0000 | 295.00 | # Porto de Nimalia O Porto de Nimalia conecta a capital a cargas, marinheiros, passageiros, contrabando e rumores vindos de regiões distantes como o Mar da Nebl... |
| 8 | `CAMPANHA/Rumors/01 - Dragões ao Sul de Nimalia.md` | rumor | Jogadores | 160.00 | 132.00 | 0.0000 | 292.00 | # 01 — Dragões ao Sul de Nimalia O Conclave dos Errantes ouviu relatos sobre ataques atribuídos a dragões nas regiões ao sul de Nimalia. Qualquer informação mai... |

### Resposta estruturada

- Ollama usado: `False`
- Retrieval: `rag:hybrid`
- Fontes: `Factions/Coroa de Nimalia.md`, `Territories/Nimalia.md`, `Locations/Casa da Moeda de Nimalia.md`, `Factions/Guarda Real de Nimalia.md`, `MAPA DE NIMALIA.md`, `Factions/Nobreza de Nimalia.md`

```json
{
  "fatos_confirmados": [],
  "teorias": [],
  "informacoes_insuficientes": [
    "Não foi possível produzir uma resposta confiável com as informações disponíveis."
  ],
  "resposta_ao_jogador": "Não encontrei informações suficientes no que já foi revelado."
}
```

## Tentativa de mestre

- Pergunta: `o que o Estado da Campanha diz sobre Criadores?`
- Resultados recuperados: 8

| Rank | Arquivo | Tipo | Visibilidade | Exact | Lexical | Semantic | Final | Trecho |
|---:|---|---|---|---:|---:|---:|---:|---|
| 1 | `Characters/Individual/Augustus Terra Decimus.md` | character | Público | 0.00 | 44.00 | 0.5711 | 203.92 | ## Visão Geral **Títulos:** Rei soberano de Nimalia **Apelido:** **Reputação:** Monarca com pulso de ferro **Gênero:** Homem **Esposa:** Nenhuma **Classe:** Pal... |
| 2 | `Characters/Individual/Varkh Nimalis.md` | character | Público | 0.00 | 17.00 | 0.6346 | 194.69 | ## Personalidade **Temperamento:** Curioso, observador, pragmático e difícil de intimidar por muito tempo. **Virtudes:** Criatividade, precisão, lealdade a quem... |
| 3 | `Characters/Individual/Raziel.md` | character | Público | 0.00 | 17.00 | 0.6299 | 193.37 | ## Personalidade **Temperamento:** Silencioso, paciente e ameaçador; acostumado a agir fora da luz e sem necessidade de reconhecimento. **Virtudes:** Determinaç... |
| 4 | `Classes/Guerreiro.md` | class | Jogadores | 0.00 | 8.00 | 0.6579 | 192.20 | # Guerreiro O Guerreiro é a classe-base marcial de Old Dragon 2. Esta nota é um resumo de consulta para a campanha; a redação completa e a progressão de todos o... |
| 5 | `Locations/Fortaleza de Gharok.md` | location | Jogadores | 0.00 | 17.00 | 0.6190 | 190.32 | ## Informações confirmadas - Era a sede ou um dos principais domínios do Clã Sanguinallis. - Lorde Malakar ocupava seu trono na fortaleza. - Kaelen e Vandor atu... |
| 6 | `Characters/Individual/Vezemir.md` | character | Público | 0.00 | 14.00 | 0.6297 | 190.30 | ## O Dragão de Colar Dourado Essa paz terminou quando um enorme dragão verde atacou a vila. A criatura usava um misterioso colar dourado. Casas foram queimadas.... |
| 7 | `Locations/Maré Baixa.md` | location | Jogadores | 0.00 | 8.00 | 0.6503 | 190.08 | ## Cultura Local - Mercadores demi-humanos descarregam caixas durante o dia. - Contrabandistas trocam favores à noite. - Crianças correm pelos telhados. - Infor... |
| 8 | `Territories/Nimalia.md` | territory | Jogadores | 0.00 | 8.00 | 0.6472 | 189.22 | #### Bairro dos Dragonbourns Lugar onde os Dragonbourns se estabeleceram na cidade. --- |

- Checagem player-safe: PASS

## Checagens de comportamento

- Nota curta/liberada abre: PASS
- Link inexistente retorna desconhecido: PASS
- JSON inválido cai em fallback: PASS

## Observações

- Este relatório roda em modo jogador e não registra conteúdo de mestre no contexto.
- Scores técnicos ficam apenas neste relatório de validação, não aparecem para jogadores no app.
- Se o Ollama estiver indisponível, o backend deve manter fallback seguro.
