# Raziel: progressão integrada — proposta v1

Status: PROPOSTA PARA APROVAÇÃO DE SAGE. Não é regra publicada de Old Dragon, não altera o Vault, a ficha real ou o motor de progressão. Data: 2026-10-05.

## Fontes e autoridade

- Decisões atuais de Sage: reserva máxima 5, Sentido do Sangue bloqueado; Mordida e Regeneração aprovadas em `RAZIEL_VAMPIRE_POWERS_APPROVED.md`.
- `Classes/Hemomante.md`: classe autoral em revisão; tabela existente de XP, BA, JP e técnicas.
- `Races/Vampiro.md` e `Characters/Individual/Raziel.md`: referências da campanha, com divergências antigas. Não substituir decisões recentes por esses textos.
- PDF local `Downloads/old-dragon---novas-racas.pdf`, Caio Mouriz, pp. 14–16: referência racial, conferida nesta etapa. Não pressupor compatibilidade automática com OD2. O suplemento fornece a escala da Mordida, mas não uma progressão numérica de Regeneração.
- Runtime: `backend/app/level_advancement.py` só autoriza Raziel até nível 2. O bloqueio de nv3+ é correto enquanto este contrato não for aprovado.

## Um nível, quatro camadas

Hemomante determina PV, BA, JP, reserva e técnicas. Vampiro determina traços, Mordida, formas e limitações. Equipamento aplica seus modificadores separadamente. Linhagem/Sangue Antigo depende de descoberta e autorização, não de level-up.

Não existem dois níveis somados. Bônus raciais de atributos entram uma vez, não a cada avanço. Atributos, CA, dano da arma, inventário, prata/fraquezas e bônus manuais não sobem automaticamente com o nível. Não conceder ataques extras de Guerreiro ao Hemomante.

## Tabela proposta

XP, BA, JP e quantidade de técnicas seguem a tabela autoral existente, não um livro oficial. A reserva cresce mais lentamente que a tabela antiga; mantém 5 até nv3. PV após nv9 passam a +2 por nível, em vez da aceleração antiga de +1 até +6. Esses dois ajustes são propostas de balanceamento, não correções de erro.

| Nível | XP acumulado | PV ganho no avanço | BA | JP | Sangue máximo | Técnicas conhecidas | Sustentadas simultâneas |
|---:|---:|---|---:|---:|---:|---:|---:|
| 1 | 0 | baseline existente | +1 | 15 | 5 | 2 | 1 |
| 2 | 1.500 | 1d8 + mod. CON | +1 | 15 | 5 | 2 | 1 |
| 3 | 3.000 | 1d8 + mod. CON | +2 | 15 | 5 | 3 | 1 |
| 4 | 6.000 | 1d8 + mod. CON | +2 | 14 | 6 | 3 | 2 |
| 5 | 12.000 | 1d8 + mod. CON | +2 | 14 | 6 | 4 | 2 |
| 6 | 24.000 | 1d8 + mod. CON | +3 | 14 | 7 | 4 | 2 |
| 7 | 48.000 | 1d8 + mod. CON | +3 | 13 | 7 | 5 | 2 |
| 8 | 100.000 | 1d8 + mod. CON | +3 | 13 | 8 | 5 | 3 |
| 9 | 200.000 | 1d8 + mod. CON | +4 | 13 | 8 | 6 | 3 |
| 10 | 300.000 | +2, sem novo mod. CON | +4 | 12 | 9 | 6 | 3 |
| 11 | 400.000 | +2, sem novo mod. CON | +4 | 12 | 9 | 7 | 3 |
| 12 | 500.000 | +2, sem novo mod. CON | +5 | 12 | 10 | 7 | 4 |
| 13 | 600.000 | +2, sem novo mod. CON | +5 | 11 | 10 | 8 | 4 |
| 14 | 700.000 | +2, sem novo mod. CON | +5 | 11 | 11 | 8 | 4 |
| 15 | 800.000 | +2, sem novo mod. CON | +6 | 11 | 11 | 9 | 4 |
| 16 | 900.000 | +2, sem novo mod. CON | +6 | 10 | 12 | 9 | 5 |
| 17 | 1.000.000 | +2, sem novo mod. CON | +6 | 10 | 12 | 10 | 5 |
| 18 | 1.100.000 | +2, sem novo mod. CON | +7 | 10 | 13 | 10 | 5 |
| 19 | 1.200.000 | +2, sem novo mod. CON | +7 | 9 | 13 | 11 | 5 |
| 20 | 1.300.000 | +2, sem novo mod. CON | +7 | 9 | 14 | 12 | 6 |

Mínimo 1 PV por dado de vida. Nenhum recálculo retroativo dos dados já concedidos. Sustentadas são efeitos com duração que ocupam um limite; ações instantâneas não ficam ocupando vaga. O limite não é quantidade de ataques ou ações por turno.

## Progressão vampírica

| Faixa | Mordida: dano/dreno | Regeneração proposta | Custo da Regeneração |
|---|---|---|---:|
| 1–4 | 1d4 | 1d4 | 1 sangue |
| 5–7 | 1d6 | 1d6 | 1 sangue |
| 8–10 | 2d6 | 1d6 | 1 sangue |
| 11–15 | 2d6 | 2d4 | 2 sangue |
| 16 | 2d10 | 2d4 | 2 sangue |
| 17–20 | 2d10 | 2d6 | 2 sangue |

Mordida segue as faixas do suplemento; Regeneração é autoral. Mordida continua exigindo acerto, alvo vivo elegível, cura limitada ao PV drenado (sem PV temporários) e ao máximo. Não gera sangue, ataque gratuito ou cura num erro. Regeneração continua uma ação completa, sem reviver a 0 PV e sem tick passivo.

Sentido do Sangue permanece bloqueado até decisão explícita e cena de desbloqueio; nem nv2 nem nv5 o liberam sozinhos. Proposta após liberação: utilidade investigativa sem detectar identidades/segredos automaticamente; Mestre define pista disponível.

Medo: referência de 1 uso/dia, 2 a partir de nv5, sempre com resistência. Não liberar controle incondicional de personagens jogadores. Forma da Noite: Sage aprovou 3 usos diários em 2026-10-05, com escolha de corvo, coruja ou morcego. O seletor e o consumo são suportados; conversão automática de ficha animal ainda não é suportada. Nenhuma forma concede voo humanoide permanente; manter restrições de fala/ataque e transferência de dano sob adjudicação do Mestre. Fraquezas, fome, descanso no caixão e cura divina não são apagados por subir nível.

## Técnicas: catálogo proposto, não concessões automáticas

Ao ganhar uma técnica conhecida, escolher uma elegível; melhorias da mesma técnica não contam como técnica nova. Preservar as duas atuais. Não aplicar silenciosamente o texto antigo que trata Lâmina como bônus de arma: a implementação atual é ataque próprio de Nd4.

| Técnica | Nível mínimo proposto | Custo | Contrato mínimo para aprovação |
|---|---:|---:|---|
| Lâmina de Sangue | atual | N | Preservar ataque atual; N de 1 a 5, Nd4, uma resolução; máximo 5 mesmo com reserva maior. |
| Marca Rubra | atual | 1 | Alvo ferido; rastreio/identificação, sem dano grátis. Duração futura precisa ser fixada; não mudar a atual. |
| Névoa Carmesim | 3 | 1 | Ação; cobertura em torno de Raziel por 1 rodada, +2 ao teste de ocultação/fuga pertinente; sem invisibilidade ou acumulação. Minha recomendação para a terceira técnica. |
| Estancar | 3 | 1 | Ação e contato; estabiliza sangramento, não revive mortos nem cura PV; evita duplicar Regeneração. |
| Sangue Defensivo | 4 | 2 | Ação; +2 CA até o início do próximo turno; uma instância, sem empilhar consigo. |
| Técnica de Predador | 5 | 2 | Ação; +2 em um teste escolhido de perseguição/escalada/intimidação durante 1 rodada; sem ataque extra. |
| Névoa de Sangue | 7 | 3 | Ação; área de raio 3 m por 1d4 rodadas, visão obscurecida para todos; sem imunidade automática do grupo. |
| Arma Sólida de Sangue | 9 | 2 | Ação; arma temporária 1d6 por 3 rodadas, sem bônus mágico automático; ataque em turno posterior usa orçamento normal. |
| Controle de Sangue Alheio | 11 | 3 | Ação; alvo ferido visível em até 9 m, JP nega; falha dá -2 ao próximo ataque até o próximo turno. Não controla decisões do jogador. |
| Drenagem Vital | 13 | 3 | Ação; ataque próprio corpo a corpo, 2d6, cura pelo dreno real; alternativa à Mordida, nunca aplicada por cima dela. Não recupera reserva. |
| Ritual Hemático | 15 | 3 | Fora de combate, 10 min, amostra e testemunho; o Mestre entrega uma pista verificável sobre a amostra, não lore secreto inteiro. Sem revelação automática da linhagem. |
| Asas Escarlates | 17 | 4 | Ação; voo 12 m por 3 rodadas, um efeito sustentado; expiração exige pouso/queda conforme terreno. Não concede ataques extras. |

No nível 3, escolher uma, não conceder Névoa e Estancar juntas. Só técnicas escolhidas ficam utilizáveis. Técnicas ainda não implementadas aparecem como pendentes de suporte, nunca como botão que finge resolver a ação.

## Recuperação, economia e ficha inteira

- Um único recurso `reserva_de_sangue`, compartilhado por todas as técnicas e Regeneração.
- Level-up muda capacidade, não recarrega sangue, usos raciais ou consumíveis.
- Descanso aprovado no caixão com alimentação restaura reserva; alimentação fora do descanso deve ser decisão registrada do Mestre, sem ganhar sangue em todo ataque.
- Dano voluntário não compra sangue automaticamente; evita o ciclo dano → sangue → regeneração infinita.
- BA e JP vêm da classe; modificadores de atributos/equipamentos/efeitos entram depois, identificados na prévia.
- PV atuais seguem a política já escolhida no avanço (`preserve_current` ou `preserve_wounds`); 0 PV nunca é reanimado por subir nível.
- XP acumulado fica preservado. A tabela homebrew acima precisa de aprovação; nunca apresentá-la como XP oficial do livro.
- Cada desbloqueio/grant tem nível de origem e identificador único. Repetir confirmação não concede de novo; corrigir o Mestre não apaga histórico.
- Corpo, imunidades, movimento e fraquezas raciais exigem handlers reais para serem automatizados; texto na ficha não prova que o backend já os aplica.
- Recarregar/reconectar deve manter ficha, usos, efeitos e limites; sem recalcular grants antigos a partir do texto do Vault.

## Decisões para fechar o primeiro corte de implementação

1. Aprovar ou ajustar a tabela: reserva lenta 5→14 e PV fixos +2 após nv9, mantendo BA/JP/XP autorais existentes.
2. Aprovar a escala racial da Mordida e a Regeneração com custo 2 nas faixas maiores.
3. Escolher a terceira técnica no nv3: recomendo Névoa Carmesim. Forma da Noite já confirmada por Sage em 2026-10-05: 3 usos diários e seleção de corvo, coruja ou morcego. Essa aprovação não autoriza a tabela futura nem a conversão automática para fichas animais.

Após aprovação: implementar nv3–4 primeiro no mecanismo existente, com preview completo e testes de idempotência; manter os marcos seguintes documentados sem fingir suporte já implementado. Nenhum avanço operacional será concedido sem confirmação do Mestre.
