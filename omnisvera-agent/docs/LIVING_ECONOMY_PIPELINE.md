# Economia viva: blocos e saque de grupo

Decisões do Mestre em 31/10/2026: saque dividido entre o grupo, itens
indivisíveis em rodízio automático e rotina econômica por **dias reais**.
Não é uma simulação ativada no banco operacional.

## Ciclo pretendido

Dia real → produção/ofertas → demanda por suprimentos → compras/vendas →
missão/viagem → encontro → derrota → espólio → inventário → consumo/revenda.

Thoradin e os aventureiros devem participar desse mesmo ciclo. O mercado não
deve ser apenas um gerador de estoque, e a missão não deve criar recompensas
desconectadas dos contratos de loot/inventário.

## Entregue neste corte: baú do cadáver

No mapa, um cadáver de monstro com tesouro carregado oferece um botão com
ícone de baú. Um clique chama `POST /workspace/loot/collect`, com apenas
`request_id` e `token_id`; destinatários e recompensas não vêm do cliente.
O resultado compacto aparece no mapa, com auditoria no registro existente.

Quando o combate nativo retira um monstro derrotado da iniciativa, preserva no
cadáver os personagens participantes, inclusive os já retirados dos turnos.
Assim, restaurar o mapa de exploração ou começar outro combate não perde o grupo
do espólio. Para cadáveres antigos ou criados fora desse fluxo, o fallback são
os personagens com pins públicos e estado válido no mapa do cadáver.
Pins duplicados não duplicam cotas; offline não significa fora do grupo.
A composição fica congelada no recibo inicial. Não foi criado outro sistema de
grupos. Futuras expedições de NPCs precisarão de um adaptador de destinatários.
Um destinatário removido exige revisão do Mestre, sem redistribuição silenciosa.

Moedas são convertidas à unidade mínima da regra monetária vigente e divididas
sem frações/perda de valor. Sobras monetárias e itens têm cursores separados,
persistidos por composição do grupo. Itens indivisíveis alternam destinatários;
quantidades maiores são repartidas sem criar ou partir objetos.

O sorteio usa as tabelas e expansores nativos, e permanece salvo como uma
resolução privada se a entrega falhar: retry não rerrola. Revelação, distribuição,
carteiras/inventários, cursor e marca de coleta são confirmados juntos. O cadáver
permanece disponível para as interações existentes, inclusive reanimação.

Rascunhos privados anteriores exigem o Mestre. Se o Mestre editar um sorteio
automático cuja entrega falhou, o jogador também precisa aguardar revelação ou
nova confirmação do Mestre. Recibos não incluem notas privadas ou rolagens
técnicas. Tesouro de covil, invocações e corpos desintegrados/reanimados não
usam esse atalho. A distribuição manual existente continua disponível.

Não foi criada regra de alcance ou custo de ação para saquear. São decisões
de RPG separadas da transferência administrativa; o backend valida contexto,
visibilidade, grupo, fonte, propriedade e idempotência.

## Próximos blocos — projeto, ainda não executores ativos

| Bloco | Entradas necessárias | Saída verificável |
| --- | --- | --- |
| Caixa do NPC | NPC nativo, saldo inicial aprovado e moeda canônica | Débito/crédito e contrapartida no ledger da transação |
| Produção | Receita aprovada, insumos, quantidade/dia, limite e destino nativo | Consumo dos insumos/custos e acréscimo do produto ao estoque |
| Demanda | Itens/categorias, quantidade desejada, prioridade, teto de preço e orçamento | Ofertas de compra ou compras autorizadas até o limite do caixa |
| Expedição | Participantes, missão/rota, kit mínimo e resolução aprovada | Gastos, progresso e resultado ligado ao loot nativo |
| Agenda real | Fuso, data inicial e dias já processados por NPC | Um recibo por NPC/data, com política e efeitos antes/depois |

O caixa dos comerciantes ainda não é finito: os caminhos atuais debitam ou
creditam a carteira do personagem e ajustam estoque, sem a carteira oposta do
NPC. `npc_states` também não contém carteira/inventário econômico. É necessário
conectar o estado econômico ao NPC existente, reutilizando a regra monetária e
as transferências; não criar uma cópia do personagem ou uma segunda carteira
para jogadores.

Dias reais não significam recriar o estoque em cada GET ou reinício. O executor
deverá usar data/fuso explícitos, persistir o último processamento e recuperar
dias pendentes com limite de trabalho por lote. A identidade deve ser NPC +
data; trocar a revisão da política no mesmo dia não autoriza produzir duas vezes.
Todos os efeitos de um lote devem ter origem, versão, custos e recibo.
Esse calendário econômico não concede descanso aos personagens nem avança
rodadas/efeitos de combate automaticamente.

Não foram escolhidos volumes diários, receitas, salários, limites de caixa,
chances de missão ou mortes de NPCs importantes. A IA pode propor esses dados;
somente contratos aprovados podem movimentar recursos. Combates de expedições
não podem disputar o relógio/turno da mesa ativa. Não há um novo worker residente,
modelo de IA ou reposição diária automática ativada neste corte.

## Validação e arquivos

Backend: `loot.py` permite composição interna das transações nativas e serializa
as migrações; `loot_collection.py` contém o orquestrador/recibos/cursores;
`main.py`/`schemas.py` expõem o comando; `session_workspace.py` também reconhece
espólios distribuídos manualmente, com consulta limitada aos cadáveres do mapa.
`battle_mode.py` preserva apenas a referência dos destinatários no cadáver,
sem alterar regras de turnos, dano, progressão ou movimentação.
Frontend: `api.ts`, `SessionWorkspace.tsx`, `MapLootChest.tsx`, `mapLoot.css`.
Testes: `test_loot_collection.py`, `map-loot-chest.test.cjs` e regressão adicional
em `foundation-commerce-retry.test.cjs`.

- Regressões focadas iniciais: **48 aprovadas**; a suíte final inclui doze novos
  testes backend de saque. Saque/retirada de combate também passaram em
  **16 testes focados**; o caso com participante previamente derrotado está
  incluído no fechamento da suíte geral.
  Foram reproduzidas e corrigidas a corrida de migração e a possibilidade de
  publicar uma edição privada posterior a uma entrega automática frustrada.
  Outras regressões reproduziram perda de notas privadas na conversão de moeda
  e perda do vínculo do grupo após retorno à exploração. Notas ficam preservadas
  somente para o Mestre; o cadáver conserva seus destinatários.
- Frontend: **501 aprovados**, typecheck e build em TEMP aprovados; permanece
  o aviso conhecido de bundles grandes.
- Smoke CF01/Playwright, quatro atores sintéticos: um clique mobile repartiu
  1 PO em quatro cotas exatas de 25 PC, duas espadas foram alternadas entre
  destinatários, retry/reload mantiveram o resultado e o outro cliente removeu
  o baú sem refresh. O cadáver permaneceu. Quatro capturas revisadas:
  **PASS_SCOPED_GROUP_LOOT** (Mestre 1440 px/jogador 390 px).
- Smoke final repetido após retirada nativa dos dois monstros da iniciativa,
  saída dos quatro personagens do mapa dos cadáveres e substituição do encontro:
  mesmas asserções aprovadas e mais quatro capturas revisadas,
  **PASS_SCOPED_GROUP_LOOT_POSTCOMBAT**.
- A fixture final usa mapa sintético e apresentou dois 404 de mídias canônicas
  ausentes (imagem de Nimalis e ícone de dados);
  não certifica arte, todas as fichas ou uma mesa em redes diferentes. O
  conector `companion-tests` não está exposto aqui: foi usado o CF01 nativo com
  driver finito, não um `report.ui_smoke` fabricado.
- Revisão React: imports diretos, dependências existentes, ação no handler,
  comando único, resposta mínima, botão acessível e sem componentes dentro de
  componentes/efeitos adicionais de polling. Nenhuma biblioteca visual nova.
- Suíte geral backend: **1.872 casos, 1.871 aprovados, zero falhas/erros e um
  skip** (Windows sem privilégio para symlink), em 709,24 s, sobre o código final.

Artefatos `group-loot-*` no diretório de visualizações deste chat. Backend e
navegador de QA encerrados pelos próprios handles/grupo. No último wrapper,
o helper de parada do servidor excedeu 15 s e o wrapper terminou com código 1
depois do PASS do navegador; o Job Object fechou com o processo. A verificação
posterior confirmou os PIDs próprios 7404/14796 ausentes e nenhuma escuta em
8871. Essa ressalva de limpeza não é um FAIL de asserção funcional.
Ensaios somente em
SQLite e credenciais sintéticos;
nenhuma ficha, moeda, estoque real, token, Vault ou serviço operacional alterado.
Ao concluir esse checkpoint de validação, ainda não havia staging, commit, push
ou ativação. Depois, o código foi publicado para hospedagem Windows conforme
`HOSTING.md`, sem reiniciar o runtime de origem nem ativar a economia diária dos NPCs.
