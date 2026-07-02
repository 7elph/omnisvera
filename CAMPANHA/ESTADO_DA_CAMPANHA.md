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

## Painel de Controle do Vault

| área | acesso rápido | uso |
|---|---|---|
| Home do Mestre | [[Home_Mestre]] | navegação visual e atalhos |
| Home dos Jogadores | [[Home]] | consulta player-safe |
| Capítulos | [[01 - Ecos do Mundo Perdido]] | versão pública/jogável do capítulo |
| Estado da Campanha | [[ESTADO_DA_CAMPANHA]] | bastidores, frentes e decisões |
| Fila de Conteúdo | [[CONTENT_CREATION_QUEUE]] | notas que precisam desenvolvimento |
| Modelo Player-Safe | [[PLAYER_SAFE_ENTITY_MODEL]] | regra de separação entre nota pública e bastidor |

## Entidades em Desenvolvimento Prioritário

| entidade | tipo | função no controle |
|---|---|---|
| [[O Frasco Afogado]] | local | loja/oficina, investigação dos remédios falsos |
| [[Maré Baixa]] | local | submundo portuário, origem de Varkh |
| [[Nimalis]] | cidade | capital e centro político |
| [[Coroa de Nimalia]] | facção | poder institucional |
| [[Varkh Nimalis]] | personagem | arco dos remédios falsos |
| [[Guilda dos Mercadores]] | facção | comércio, rotas e influência econômica |
| [[Porto de Nimalia]] | local | entrada de cargas, rumores e contrabando |
| [[Raziel]] | personagem | sangue antigo, Gharok e passado enterrado |
| [[Culto dos Sussurrantes]] | facção/rumor | ameaça em revisão ligada ao Véu |

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
WHERE type != "index"
AND quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
WHERE type != "index"
SORT file.name ASC
```

## Facções em Movimento

```dataview
TABLE status, location, territory
FROM "Factions"
WHERE type != "index"
SORT file.name ASC
```

## Locais em Foco

```dataview
TABLE territory, status, danger_level
FROM "Locations" OR "Territories"
WHERE type != "index"
SORT file.name ASC
LIMIT 12
```

## Itens Revelados

```dataview
TABLE status, location
FROM "Items"
WHERE type != "index"
AND (contains(tags, "item") OR contains(tags, "artefato"))
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

## Frentes de Controle

> [!IMPORTANT]
> Estas frentes guardam bastidores e decisões do mestre. As notas principais devem permanecer player-safe.

### Frente — O Frasco Afogado e os Remédios Falsos

#### Entidades Ligadas

- [[O Frasco Afogado]]
- [[Maré Baixa]]
- [[Varkh Nimalis]]
- [[Mestre Odran Veyl]]
- [[Remédios Falsos de Maré Baixa]]
- [[Rede de Falsificadores de Maré Baixa]]

#### Status Atual

Em desenvolvimento. A frente conecta a origem de Varkh, a memória de Odran e a circulação de remédios falsos em Nimalia.

#### Segredos do Mestre

- Não confirmar ainda se Odran está envolvido nas falsificações.
- Não decidir automaticamente se [[O Frasco Afogado]] está aberto, fechado, abandonado, tomado ou vigiado.
- Se houver estoque escondido, fórmula perdida ou registro comprometedor, tratar como revelação futura.

#### Verdades Possíveis

- Alguém pode estar usando o símbolo de Odran sem autorização.
- A [[Guilda dos Mercadores]] pode saber mais sobre a rota dos produtos do que admite.
- A [[Coroa de Nimalia]] pode tentar controlar a investigação se houver risco público.

#### Pistas

- Rótulos antigos.
- Frascos adulterados.
- Ingredientes baratos demais.
- Assinatura perfeita demais.
- Testemunhas de [[Maré Baixa]] que conhecem Odran.

#### Rumores: Verdadeiros, Falsos ou Incompletos

- Rumores sobre remédios falsos devem aparecer primeiro como problema de rua, não como conspiração resolvida.
- A verdade de cada rumor fica pendente até decisão do Sage.

#### Condições de Revelação

- Revelar pistas por investigação, compra de remédio adulterado, retorno de Varkh a [[Maré Baixa]] ou contato com falsificadores.

#### Consequências

- Expor a falsificação pode atrair criminosos, mercadores, guardas ou clientes desesperados.

#### Decisões Pendentes do Sage

- Estado atual do Frasco.
- Papel real de Odran.
- Identidade de quem usa o símbolo falso.
- Nível de envolvimento da Guilda e da Coroa.

### Frente — Nimalis, Coroa e Porto

#### Entidades Ligadas

- [[Nimalis]]
- [[Coroa de Nimalia]]
- [[Guarda Real de Nimalia]]
- [[Porto de Nimalia]]
- [[Guilda dos Mercadores]]

#### Status Atual

Frente estrutural da capital. Define como poder, comércio, segurança e circulação de informações funcionam em Nimalis.

#### Segredos do Mestre

- Rotas ilícitas, cargas suspeitas e autoridade portuária ainda precisam ser definidas.
- O grau de controle real da Coroa sobre o porto permanece aberto.
- A influência da Guilda pode ser pública, indireta ou clandestina.

#### Pistas

- Carga atrasada.
- Navio sem registro.
- Guarda comprada.
- Documento comercial contraditório.
- Mercador que sabe demais.

#### Consequências

- Problemas no porto afetam abastecimento, reputação da Coroa, submundo de [[Maré Baixa]] e poder da Guilda.

#### Decisões Pendentes do Sage

- Autoridade portuária.
- Rotas principais.
- Relação entre Coroa, Guarda Real e Guilda.
- Quanto o povo de Nimalis percebe da corrupção ou tensão econômica.

### Frente — Varkh Nimalis

#### Entidades Ligadas

- [[Varkh Nimalis]]
- [[O Frasco Afogado]]
- [[Mestre Odran Veyl]]
- [[Conclave dos Errantes]]
- [[Remédios Falsos de Maré Baixa]]

#### Status Atual

Arco pessoal ligado à origem em [[Maré Baixa]], à alquimia de rua e à investigação dos remédios falsos.

#### Segredos do Mestre

- A identidade de quem está usando os métodos de Odran ainda é desconhecida.
- A extensão real da fama de Varkh como assassino pode ser maior ou menor do que os rumores indicam.
- A classe mecânica definitiva de Varkh ainda precisa ser reconciliada com a ficha sem nome recebida do jogador.

#### Condições de Revelação

- Revelar por pistas em frascos, testemunhas de Maré Baixa, contato do Conclave ou retorno ao Frasco.

### Frente — Raziel

#### Entidades Ligadas

- [[Raziel]]
- [[Clã Sanguinallis]]
- [[Fortaleza de Gharok]]
- [[Sangue Antigo]]
- [[Adagas de Espectro Fantasma]]

#### Status Atual

Arco pessoal ligado a sangue antigo, traição, Gharok e estruturas anteriores ao presente.

#### Segredos do Mestre

- O verdadeiro motivo pelo qual o Ancião Primordial libertou Raziel permanece desconhecido.
- A heresia rúnica usada como pretexto para sua captura ainda não foi definida.
- Sua relação com o Véu Cinzento e com os Criadores ainda não foi confirmada.

#### Condições de Revelação

- Revelar por reação a ruínas antigas, sangue, máquinas, memórias fragmentadas ou antagonistas ligados a Gharok.

### Frente — Culto dos Sussurrantes

#### Entidades Ligadas

- [[Culto dos Sussurrantes]]
- [[Véu Cinzento]]
- [[Igreja das Chamas]]
- [[Coroa de Nimalia]]

#### Status Atual

Em revisão. Pode ser ameaça ativa, rumor distorcido, culto menor ou rascunho a arquivar.

#### Segredos do Mestre

- Não confirmar ainda se o culto é ameaça ativa.
- Não revelar o Arauto Sombrio sem decidir se ele será mantido.
- Evitar usar o culto como explicação fácil para todo mistério do Véu.

#### Decisões Pendentes do Sage

- Confirmar existência canônica.
- Definir relação real com o [[Véu Cinzento]].
- Decidir se o Arauto Sombrio permanece, muda ou sai.
- Definir se o culto fica como facção, religião, rumor ou arquivo.

### Frente — Itens de Vezemir

#### Entidades Ligadas

- [[O Medalhão]]
- [[Grisalma]]
- [[Muralha de Dorn]]
- [[Vezemir]]
- [[Véu Cinzento]]
- [[Guardiões do Véu Cinzento]]

#### Status Atual

Itens centrais para identidade, pistas graduais e evolução de Vezemir. As notas principais devem mostrar uso conhecido, aparência e função em mesa sem explicar a origem real.

#### Segredos do Mestre

- [[O Medalhão]] não deve ter sua função real definida publicamente como chave, selo, linhagem ou relíquia reativa.
- Reações do medalhão devem funcionar como pistas, não como explicação completa.
- [[Grisalma]] não deve liberar todas as propriedades narrativas como mecânica livre no nível 1.
- Reações de Grisalma ao [[Véu Cinzento]], ao dragão ou aos Guardiões devem ser reveladas gradualmente.
- [[Muralha de Dorn]] ainda precisa definir se “Dorn” é pessoa, lugar, tradição, título ou nome simbólico.

#### Condições de Revelação

- Revelar por reação a símbolos antigos, presença do Véu, memória dos Guardiões, conflito com o dragão ou escolhas de Vezemir em mesa.

#### Decisões Pendentes do Sage

- Propriedades finais de Grisalma.
- Natureza do Medalhão.
- Origem e significado de Dorn.
- Quando cada item pode reagir sem quebrar o nível atual do personagem.

### Frente — Itens de Raziel

#### Entidades Ligadas

- [[Adagas de Espectro Fantasma]]
- [[Manto Primordial do Ancião]]
- [[Raziel]]
- [[Sangue Antigo]]
- [[Clã Sanguinallis]]
- [[Ancião Primordial]]

#### Status Atual

Itens ligados ao passado de Raziel, ao Sangue Antigo e ao pacto/retorno que ainda não deve ser explicado de uma vez.

#### Segredos do Mestre

- Não definir ainda se as [[Adagas de Espectro Fantasma]] foram forjadas pelo clã, por Raziel ou por outro poder.
- Não revelar cedo se as adagas drenam energia vital por magia vampírica, Sangue Antigo ou técnica Sanguinallis.
- Separar as propriedades das adagas das propriedades pessoais de Raziel.
- Não revelar o [[Ancião Primordial]] por meio do [[Manto Primordial do Ancião]] antes do arco pedir.
- Manter o custo da dádiva em aberto.
- O manto é relíquia de campanha, não regra básica da classe [[Vampiro]].

#### Condições de Revelação

- Revelar por memória fragmentada, sangue derramado, ruínas de Gharok, confronto com Sanguinallis ou intervenção do Ancião.

#### Decisões Pendentes do Sage

- Origem real das adagas.
- Método de forja ou vínculo.
- Custo do manto.
- Limites entre item, classe e pacto narrativo.

### Frente — Itens de Varkh

#### Entidades Ligadas

- [[Máscara de Médico da Peste de Varkh]]
- [[Caderninho de Vozes]]
- [[Varkh Nimalis]]
- [[O Frasco Afogado]]
- [[Mestre Odran Veyl]]

#### Status Atual

Itens de identidade, presença social e investigação. Devem reforçar Varkh em cena sem virar solução automática.

#### Segredos do Mestre

- A [[Máscara de Médico da Peste de Varkh]] não tem função mágica confirmada.
- Se ganhar regra própria, deve reforçar investigação, proteção ou intimidação.
- O [[Caderninho de Vozes]] não tem função secreta confirmada.
- Se virar item mágico ou mecânico, isso deve ser decisão futura.
- A força atual do caderninho é narrativa: identidade, memória, disfarce social e improviso.

#### Condições de Revelação

- Revelar por uso social, investigação em Maré Baixa, lembranças de Odran, contato com falsificadores ou cena de improviso.

#### Decisões Pendentes do Sage

- Se a máscara terá mecânica própria.
- Se o caderninho é apenas ferramenta narrativa ou item com efeito futuro.
- Como esses itens entram no arco dos remédios falsos.

### Frente — Cosmologia, Véu e Criadores

#### Entidades Ligadas

- [[Criadores]]
- [[O Fraturamento]]
- [[Eclipse de Obsidiana]]
- [[Véu Cinzento]]
- [[Guardiões do Véu Cinzento]]
- [[Ancião Primordial]]
- [[Sangue Antigo]]
- [[Vampiro Sanguinallis]]

#### Status Atual

Frente de bastidor cosmológico. As notas principais devem apresentar mitos, fenômenos, rumores e versões conhecidas sem resolver a verdade final do mundo.

#### Segredos do Mestre

- A natureza real dos [[Criadores]] ainda está em definição.
- A cosmologia real do [[O Fraturamento]] não deve ser fechada publicamente.
- Causa, escala verdadeira e relação do [[Eclipse de Obsidiana]] com Criadores/Fraturamento permanecem em aberto.
- A natureza verdadeira do [[Véu Cinzento]] ainda está em construção.
- A função real dos [[Guardiões do Véu Cinzento]] ainda deve ser dosada.
- O [[Ancião Primordial]] pode ter objetivos próprios e planos ainda não definidos.
- Origem, custo real e consequências de longo prazo do [[Sangue Antigo]] ficam no bastidor.
- Diferenças entre vampirismo comum e [[Vampiro Sanguinallis]] devem ser reveladas gradualmente.

#### Condições de Revelação

- Revelar por ruínas antigas, reação de Raziel, sinais do Véu, registros pré-cataclísmicos, cultos, máquinas antigas ou eventos ligados ao primeiro capítulo.

#### Decisões Pendentes do Sage

- Natureza real dos Criadores.
- Papel do Véu na criação, corrupção ou proteção do mundo.
- Custo narrativo do Sangue Antigo.
- Relação entre Ancião Primordial, Sanguinallis e estruturas antigas.

### Frente — Religiões e Doutrinas

#### Entidades Ligadas

- [[RELIGION]]
- [[Igreja das Chamas]]
- [[Fé dos Antigos]]
- [[Caminho dos Errantes]]
- [[Culto dos Sussurrantes]]
- [[Clérigo]]

#### Status Atual

Frente de crenças públicas e tensões espirituais. As notas principais devem mostrar prática, imagem pública e uso em mesa sem confirmar verdades metafísicas.

#### Segredos do Mestre

- Verdades antigas, cultos perigosos e manipulações institucionais ficam no Estado da Campanha.
- Possíveis contradições doutrinárias da [[Igreja das Chamas]] ainda precisam ser confirmadas.
- A relação real da [[Fé dos Antigos]] com os Criadores está em aberto.
- O [[Caminho dos Errantes]] pode ter ligação com ciclos reais, destino ou memória, mas isso não está fechado.
- Segredos religiosos ligados à classe [[Clérigo]] ainda não estão consolidados.

#### Condições de Revelação

- Revelar por sermões, relíquias, conflitos entre crenças, milagres ambíguos, registros antigos ou contato com o Véu.

#### Decisões Pendentes do Sage

- Quais crenças são canônicas como religião ativa.
- O que é verdade, interpretação ou mentira institucional.
- Como clérigos acessam poder no cenário.

### Frente — Povos, Reinos e Classes

#### Entidades Ligadas

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

#### Status Atual

Frente de bastidores culturais, linhagens e limites mecânicos. Notas principais devem ser úteis aos jogadores sem entregar política futura, linhagens ocultas ou segredos de classe.

#### Segredos do Mestre

- Linhagens específicas de antropos, humanos e meio-elfos podem esconder tradições, pactos ou rivalidades locais.
- Obras anãs antigas podem guardar segredos de eras anteriores.
- Reino élfico, reino dragonborn e suas políticas ainda serão revelados.
- Vozes imitadas por kenkus podem virar pista ou arma social.
- Origem, limites e consequências do vampirismo/Sangue Antigo ficam no bastidor.
- Limites de alquimia perigosa, magia antiga, vínculos criminais e ajustes específicos de classe ficam pendentes até uso em mesa.

#### Condições de Revelação

- Revelar por origem de personagem, viagem a reinos raciais, ruínas, tutores, falhas de magia, contatos de classe ou consequências de uso perigoso.

#### Decisões Pendentes do Sage

- Quais reinos raciais entram primeiro em jogo.
- Quais linhagens têm segredo real.
- Quais limites mecânicos entram em Old Dragon sem quebrar nível baixo.

### Frente — Vezemir, Avenor e o Dragão

#### Entidades Ligadas

- [[Vezemir]]
- [[Mira Valen]]
- [[Padre Oric]]
- [[Elarion Vaelthor]]
- [[Dragão de Colar Dourado]]
- [[Floresta de Avenor]]
- [[Leth'valora]]

#### Status Atual

Frente pessoal de Vezemir e da destruição de Leth'valora. As notas principais devem mostrar memória, impacto e rumores sem explicar cedo demais o dragão, os Guardiões ou a origem dos sinais.

#### Segredos do Mestre

- Relação completa entre Vezemir, o dragão, o medalhão, Grisalma e os Guardiões deve ser revelada em etapas.
- Detalhes do ataque a Leth'valora e do que Elarion/Mira/Oric sabiam ainda podem ser dosados.
- O Dragão de Colar Dourado deve permanecer parcialmente misterioso enquanto o jogador descobre pistas.

#### Condições de Revelação

- Revelar por lembranças, reações de relíquias, viagem a Avenor, rumores sobre Leth'valora ou contato com símbolos dos Guardiões.

### Frente — Nimalia, Coroa e Guarda

#### Entidades Ligadas

- [[Augustus Terra Decimus]]
- [[General Cassian Valerius]]
- [[Coroa de Nimalia]]
- [[Guarda Real de Nimalia]]
- [[Nimalis]]

#### Status Atual

Frente política da capital. As notas principais devem mostrar imagem pública, função e autoridade, mantendo intrigas, corrupção e decisões de bastidor no Estado da Campanha.

#### Segredos do Mestre

- Relação real entre Coroa, Guarda, Guilda e Maré Baixa ainda pode mudar.
- Possíveis tensões entre Augustus, Cassian e outras casas nobres não devem ser resolvidas nas notas principais.

#### Condições de Revelação

- Revelar por ordens oficiais, investigação de cargas, reação da Guarda, audiência na capital ou crise pública.

### Frente — Gharok, Sanguinallis e Antagonistas Antigos

#### Entidades Ligadas

- [[Raziel]]
- [[Lorde Malakar]]
- [[Kaelen, o Flagelo]]
- [[Vandor, o Senhor das Bestas]]
- [[Clã Sanguinallis]]
- [[Fortaleza de Gharok]]

#### Status Atual

Frente ligada ao passado de Raziel, ao Clã Sanguinallis e aos antagonistas antigos. As notas principais podem apresentar reputação e história conhecida sem revelar sobrevivência, retorno, pacto ou verdade final.

#### Segredos do Mestre

- Sobrevivência atual, influência remanescente e função futura de Malakar, Kaelen e Vandor devem permanecer no bastidor.
- A relação exata entre Sanguinallis, Sangue Antigo e Raziel deve ser revelada por cenas, não por exposição.

#### Condições de Revelação

- Revelar por ruínas de Gharok, memórias de Raziel, sangue, artefatos Sanguinallis ou inimigos que reconhecem sinais antigos.

### Frente — Odran, DORN-7 e Máquinas Antigas

#### Entidades Ligadas

- [[Mestre Odran Veyl]]
- [[Unidade DORN-7]]
- [[O Frasco Afogado]]
- [[Remédios Falsos de Maré Baixa]]
- [[Criadores]]

#### Status Atual

Frente de investigação e tecnologia antiga. Odran deve permanecer ambíguo e DORN-7 deve revelar escala maior sem explicar todo o sistema.

#### Segredos do Mestre

- Paradeiro e participação real de Odran nas falsificações ficam pendentes.
- A [[Unidade DORN-7]] é parte de um sistema maior, mas isso deve ser revelado por funcionamento, falhas e pistas.
- Conexão entre remédios falsos, materiais antigos e máquinas subterrâneas deve ser dosada.

#### Condições de Revelação

- Revelar por investigação no Frasco, ativação da DORN-7, análise de frascos ou descoberta de estruturas antigas.

### Frente — Bairros e Infraestrutura de Nimalis

#### Entidades Ligadas

- [[Bairro dos Humanos]]
- [[Bairro dos Elfos]]
- [[Bairro dos Anões]]
- [[Bairro dos Dragonborns]]
- [[Bairro dos Forasteiros]]
- [[Bairro Nobre]]
- [[Mercado Central]]
- [[Distrito Comercial]]
- [[Casa da Moeda de Nimalia]]

#### Status Atual

Frente de cenário urbano. As notas principais devem funcionar como consulta de mesa: aparência, função social, pontos úteis e rumores leves.

#### Segredos do Mestre

- Famílias influentes, emissários, agentes raciais e intrigas entre casas nobres ficam em definição.
- Lojas ilegais, pactos escusos, fraudes e pistas escondidas devem ser revelados por cena, não por nota principal.
- Redes de proteção, crime ou exploração no Bairro dos Forasteiros ainda precisam ser definidas.

#### Condições de Revelação

- Revelar por investigação urbana, perseguição, audiência política, compra suspeita, documento fiscal ou contato de rua.

### Frente — Avenor, Rotas e Ruínas Próximas

#### Entidades Ligadas

- [[Antiga Estrada Esquecida]]
- [[Fortaleza Abandonada de Avenor]]
- [[Bosque Sussurrante]]
- [[Leth'valora]]
- [[Vale Dourado]]
- [[Campos de Earthropo]]
- [[Mar da Neblina]]

#### Status Atual

Frente de exploração e fronteira. As notas principais devem mostrar lugares visitáveis e sensações de cena sem fechar a função real de cada ruína, estrada ou território.

#### Segredos do Mestre

- Possíveis pistas sobre a origem de Vezemir e conexões antigas ficam no Estado da Campanha.
- Relação completa entre relíquias, Elarion, Avenor e segredos antigos deve ser dosada.
- Detalhes do ataque a Leth'valora, do dragão e das tradições internas ainda podem ser revelados gradualmente.
- A função real de Vale Dourado, Campos de Earthropo e Mar da Neblina permanece em construção.

#### Condições de Revelação

- Revelar por viagem, exploração, ruínas, marcas do dragão, rumores de fronteira, pistas ambientais ou retorno a Avenor.

### Frente — Gharok, Valthor e Sanguinallis

#### Entidades Ligadas

- [[Fortaleza de Gharok]]
- [[Ruínas de Valthor]]
- [[Clã Sanguinallis]]
- [[Raziel]]
- [[Sangue Antigo]]
- [[Ancião Primordial]]

#### Status Atual

Frente de passado antigo, sangue e queda de reinos. Notas principais devem apresentar história conhecida, reputação e riscos sem revelar sobrevivência, estrutura atual ou ligação total com Raziel.

#### Segredos do Mestre

- Relação exata de [[Fortaleza de Gharok]] com Raziel, Sanguinallis e o futuro reino anão ainda está em revisão.
- Relação das [[Ruínas de Valthor]] com Raziel, Ancião Primordial e Sangue Antigo deve ser dosada.
- Estrutura completa, sobrevivência atual e motivação real do [[Clã Sanguinallis]] ficam no bastidor.

#### Condições de Revelação

- Revelar por investigação em ruínas, sangue, relíquias, inimigos antigos, documentos perdidos ou reações de Raziel.

### Frente — Rede de Falsificadores

#### Entidades Ligadas

- [[Rede de Falsificadores de Maré Baixa]]
- [[Remédios Falsos de Maré Baixa]]
- [[O Frasco Afogado]]
- [[Mestre Odran Veyl]]
- [[Varkh Nimalis]]
- [[Guilda dos Mercadores]]

#### Status Atual

Frente de investigação urbana ligada ao arco de Varkh. A nota principal da rede deve ser rumorosa e player-safe até a identidade, escala e motivação real serem decididas.

#### Segredos do Mestre

- Identidade, escala e motivação real da rede permanecem em definição.
- O envolvimento de Odran, da Guilda ou de agentes da Coroa não deve ser confirmado sem decisão do Sage.

#### Condições de Revelação

- Revelar por frascos falsos, testemunhas de Maré Baixa, rotas comerciais, documentos adulterados ou confronto com intermediários.

---

## Dossiê do Mestre — Capítulo 01: Ecos do Mundo Perdido

#### _Crônicas de [[EARTHROPO/EARTHROPO|Earthropo]] — capítulo em preparação_

> [!NOTE|clean no-i right]+ 01 - Ecos do Mundo Perdido
> ![[zz_media/covers/banner_ecos_do_mundo_perdido.png|400]]

> [!world]- SINOPSE
> O primeiro capítulo aproxima [[Vezemir]], [[Varkh Nimalis]] e [[Raziel]] por meio de um incidente em uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]]. Uma caravana sofre um acidente depois de um tremor localizado, frascos de remédios falsificados se quebram e uma passagem artificial surge sob a terra. O que parecia contrabando comum revela sinais de tecnologia antiga, símbolos ligados ao [[Véu Cinzento]] e ecos de estruturas esquecidas sob Earthropo. Cada personagem encontra ali uma pista íntima: o dragão e os Guardiões para Vezemir, os remédios falsos de Odran para Varkh, e as marcas de sangue antigo para Raziel.

## Elenco Principal

```datacards
TABLE thumbnail, status, location, faction
FROM "Characters/Individual"
WHERE (
  contains(chapters, "01 - Ecos do Mundo Perdido")
  OR contains(tags, "capitulo01")
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
WHERE type != "index"
AND quest_status != "Concluída" AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Ativos

```dataview
TABLE status, visibility, spoiler_level
FROM "CAMPANHA/Rumors"
WHERE type != "index"
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
