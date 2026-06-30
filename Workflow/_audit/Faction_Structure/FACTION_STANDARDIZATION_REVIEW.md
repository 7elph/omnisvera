# Pente Fino — Facções Operacionais de Omnisvera

## Objetivo

Padronizar a pasta `Factions/` para que cada facção tenha função clara no jogo e não se sobreponha às demais.

Esta etapa não criou novas facções e não fechou decisões narrativas profundas. O foco foi:

- completar `info` e `description`;
- adicionar sinopses operacionais;
- separar poder político, econômico, militar, criminoso e antigo;
- preservar segredos de personagem;
- usar imagens existentes;
- manter facções em revisão como rascunho quando necessário.

## Facções revisadas

| facção | função operacional | visibilidade | estado |
|---|---|---|---|
| `Coroa de Nimalia` | poder político central | Jogadores | Ativa |
| `Nobreza de Nimalia` | casas nobres e intriga de corte | Jogadores | Ativa |
| `Guarda Real de Nimalia` | força militar oficial | Jogadores | Em revisão |
| `Guilda dos Mercadores` | economia, rotas, contratos e comércio | Jogadores | Ativa |
| `Conclave dos Errantes` | aventureiros, contratos e exploração | Jogadores | Ativa |
| `Rede de Falsificadores de Maré Baixa` | antagonismo investigativo de Varkh | Mestre | Em revisão |
| `Guardiões do Véu Cinzento` | ordem antiga/desaparecida | Jogadores | Cânone de trabalho |
| `Sentinelas de Leth'valora` | guarda local destruída | Jogadores | Cânone de trabalho |
| `Clã Sanguinallis` | facção vampírica ligada a Raziel | Mestre | Em revisão |
| `Culto dos Sussurrantes` | culto/facção em revisão | Mestre | Precisa decisão |

## Separações importantes

### Poder de Nimalia

| facção | não confundir com |
|---|---|
| [[Coroa de Nimalia]] | governo central, não toda a nobreza |
| [[Nobreza de Nimalia]] | casas nobres, não a Coroa inteira |
| [[Guarda Real de Nimalia]] | braço militar, não todo o governo |
| [[Guilda dos Mercadores]] | economia, não autoridade política soberana |

### Facções de aventura e investigação

| facção | função |
|---|---|
| [[Conclave dos Errantes]] | rede de aventureiros e contratos |
| [[Rede de Falsificadores de Maré Baixa]] | ameaça investigativa do arco de Varkh |

### Facções antigas e de personagem

| facção | função |
|---|---|
| [[Guardiões do Véu Cinzento]] | ordem antiga ligada ao Véu e a Vezemir |
| [[Sentinelas de Leth'valora]] | guarda de vila destruída, ligada a Leth'valora |
| [[Clã Sanguinallis]] | origem e vingança de Raziel |
| [[Culto dos Sussurrantes]] | rascunho de culto/ameaça ligada ao Véu |

## Decisões aplicadas

- `Rede de Falsificadores de Maré Baixa` recebeu `thumbnail` e `cover` usando `zz_media/remedios-falsos.png`.
- `draft` foi removido como tag operacional de facções onde funcionava apenas como resíduo.
- `Guarda Real de Nimalia` foi normalizada no título, sem gritar em caixa alta.
- `Nobreza de Nimalia` ganhou entrada visual e função política.
- `Guardiões do Véu Cinzento` foi separado explicitamente da nota de lore e do item [[O Medalhão]].
- `Sentinelas de Leth'valora` foi separado explicitamente dos Guardiões do Véu Cinzento.
- `Clã Sanguinallis` foi separado do [[Sangue Antigo]].

## Pendências do Sage

1. Definir casas nobres principais de Nimalia.
2. Confirmar liderança da Guarda Real.
3. Confirmar números e estrutura militar de Nimalia.
4. Definir liderança da Guilda dos Mercadores.
5. Definir liderança/sede do Conclave dos Errantes.
6. Decidir se a Rede de Falsificadores age sozinha ou serve a facção maior.
7. Definir se Odran é culpado, vítima ou isca no arco dos remédios falsos.
8. Confirmar se o Clã Sanguinallis ainda existe após trezentos anos.
9. Decidir se o Culto dos Sussurrantes existe como ameaça ativa, rumor falso ou rascunho arquivável.
10. Definir diferença final entre Guardiões do Véu Cinzento e Sentinelas de Leth'valora em linguagem de jogador.

## Próxima etapa recomendada

Padronizar `Items/`, porque muitos itens já servem como ponte entre personagens, facções e lore:

1. `O Medalhão`;
2. `Grisalma`;
3. `Muralha de Dorn`;
4. `O Frasco Afogado`;
5. `Manto Primordial do Ancião`;
6. itens de Varkh;
7. índice de itens.

Objetivo:

- separar item comum, artefato, loja/local e equipamento;
- ligar cada item aos personagens corretos;
- corrigir imagens vazias;
- evitar que item revele segredo demais em nota pública.
