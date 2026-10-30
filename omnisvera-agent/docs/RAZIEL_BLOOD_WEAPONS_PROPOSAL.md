# Armas de sangue de Raziel — PROPOSTA, NÃO APROVADA

Histórico: valores atuais na [base aprovada em 17/10](RAZIEL_HEMOMANCY_APPROVED.md), não nas alternativas abaixo.

Discussão mais recente: [pipeline 5 armas + 5 habilidades + 5 passivas](RAZIEL_HEMOMANCY_PIPELINE_PROPOSAL.md).
As alternativas numéricas deste documento são históricas, não cumulativas.

Atualização: o Mestre aprovou os valores já existentes de Arma de Sangue
(1d8/custo 2), Garras (1d6/custo 1), Investida (+2, 2d4/custo 2) e Sangue
Defensivo (+2 CA por 1 rodada/custo 2). Esses controles foram conectados e
testados; ver `ACTION_COMPLETION_2026-10-12.md`. A alternativa abaixo de
espada/lança/escudo com outros custos continua não aprovada e não aplicada.

Pedido: armas com regras diferentes, para o Mestre aprovar. Nenhuma destas
mudanças foi aplicada ao personagem real ou ao catálogo neste corte.

## Ponto de partida observado

Raziel nv5: reserva 10; adagas à distância 1d4 com recuperação de PV;
Lâmina de Sangue custa 1–5 pontos para 1–5d4. O ataque corpo a corpo comum
está sem dano configurado. Há no worktree outras técnicas existentes com
valores descritos como proposta; preservadas, não tratadas como aprovação.

Abaixo, alternativa coesa para escolher forma por função sem transformar
troca visual em bônus gratuito. Valores são proposta de campanha, não regra
atribuída a Old Dragon.

| Forma proposta | Custo | Regra no nv5 | Papel |
|---|---|---|---|
| Espada de Sangue | 1 sangue por ataque confirmado | BA corpo a corpo da ficha; 1d8 | Dano sustentado: média 4,5 antes de mitigação, contra 2,5 da Lâmina 1d4 |
| Lança de Sangue | 1 sangue por ataque confirmado | BA corpo a corpo; 1d6; alcance 3 m | Menos dano, maior alcance; sem reação/ataque de oportunidade |
| Escudo de Sangue | 2 sangue; ação principal | +2 CA até início do próximo turno de Raziel | Defesa, não ataque; não acumula outro escudo nem outra instância deste efeito |

Espada/lança são um ataque único. Formar e atacar ocorre na mesma ação;
não fornece um ataque adicional nem exige gastar um turno só para formar.
Custos são aplicados na confirmação mesmo no erro, como outros ataques de
recurso. Sem roubo de vida nessas formas: Mordida/adagas conservam seu papel.

Estas formas NÃO substituem silenciosamente a Lâmina de Sangue de explosão
1–5d4. Se o Mestre quiser substituição em vez de coexistência, aprovar isso
explicitamente. Equipamento/especialização não acrescenta bônus de uma arma
física a uma forma de sangue sem regra aprovada.

Faro: também precisa confirmar se +1 contra alvo ferido vale para todas as
formas, só certas técnicas ou inclusive adagas. O backend existente aplica
um bônus em alguns ataques; a proposta não amplia esse escopo por conta própria.

## Antes de implementar

- Aprovar custos, dados, alcance, duração e coexistência com Lâmina.
- Aprovar se sangue consumido pode ser recuperado por esses novos ataques
  (proposta: não; cura e reserva não são o mesmo recurso).
- Aprovar tabela de evolução além do nv5, sem inventar progressão automática.
- Reutilizar preview/confirm, recibos, orçamento de ação, efeitos, grid,
  ledger e mesma ficha Mestre/jogador. Sem novo sistema de armas.
- Testar erro/acerto, reserva insuficiente, troca de alvo, retry concorrente,
  expiração, alcance da lança e acúmulo indevido de escudos.

Enquanto não houver aprovação, qualquer card com valores “propostos” deve
ser considerado pendente, não evidência de que o poder está pronto em mesa.
