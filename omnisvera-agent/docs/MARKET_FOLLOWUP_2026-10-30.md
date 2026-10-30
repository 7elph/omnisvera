# Mercado: objetos individuais, atendimento mágico e Klhauss

Complemento de `ECONOMY_COMPLETION.md`. Usa os mesmos mercadores, estoques,
inventário, carteira, ledger, realtime, tokens e turnos. Não altera o Vault.

## Oferta individual

Na loja, o Mestre abre **Avaliação individual**, escolhe um objeto da ficha
selecionada e informa a oferta final por unidade em PO. O jogador encontra
essa oferta em **Vender**. Não se aplica novamente o percentual de recompra.
A oferta vale até 24 horas, depende do estado exato do objeto e só pode ser
consumida uma vez. Mudança de cargas, condição, equipamento, quantidade ou
cadastro exige nova avaliação. Objetos com condição/cargas devem estar em
uma unidade para impedir divisão ambígua de uma pilha.

O objeto vendido fica em uma linha própria de `merchant_stock.instance_json`,
com procedência, condição e cargas preservadas. O Mestre vê **Objetos adquiridos
para avaliação**. Não se mistura ao estoque novo e não pode ser comprado como
novo pela loja ou pela API antiga. Reparo e revenda desse objeto individual
continuam exigindo um próximo corte; não foi criado um alias de inventário que
pudesse perder suas mecânicas na ficha do próximo comprador.

## Atendimento mágico

O Conclave pode oferecer as três curas de ferimentos e Remover Paralisia
individual já revisadas no catálogo. Tarifa inicial: **30 PO × círculo**, do
cadastro existente de serviço de conjuração: 30/120/150 PO para as curas e
90 PO para paralisia. Valores personalizados podem ser cadastrados pelo endpoint
de serviços do Mestre. O painel instala os padrões; não há editor inline de
preços dos serviços mágicos neste corte.

Os serviços usam os contratos revisados, `change_hp` e
`remove_reviewed_condition`, na mesma transação da cobrança. Retry não repete
efeito nem pagamento. Cura convencional respeita raça, limite de PV e
incapacitação; não atende vampiros, mortos-vivos ou constructos. Não há
atendimento durante combate. Não se cobra remoção de paralisia inexistente,
e não se remove veneno, imobilização de área ou qualquer outro status junto.
Magias sem contrato revisado continuam bloqueadas como serviço automático.

## Klhauss

Perfil aprovado: **guerreiro com magia, Rank S**. Configuração inicial editável
da campanha: nível 10, conjurador 6, PV 65, CA 20, JP 8, movimento 9 m,
espada longa +2 (BA +15, 1d8+5) e arco longo +1 (BA +12, 1d8+1, 30 m).
Esses números são escolhas de encontro, não uma conversão universal de Rank S
nem uma progressão nova para jogadores. Raça não foi inventada: mantém o
aspecto ursino e o retrato existentes.

Dardos Místicos e Toque Chocante têm três usos diários cada neste perfil.
O motor nativo calcula alcance/dano pelo nível de conjurador. Consumo,
idempotência e orçamento do turno são aplicados na transação existente.
O descanso geral com reposição de monstros limpa os contadores pelo
`monster_runtime.usage` já usado pelos demais monstros. Não há outro turno.

O Mestre abre o card de Klhauss dentro do Conclave, **Abrir ficha de Klhauss**
e **Voltar ao Conclave**. O token original permanece associado ao local.
A aplicação administrativa preserva identidade, imagem, posição e notas,
recusa combate ativo e nunca sobrescreve uma ficha já editada/reaplica cura.

## Validação

Regressões: `test_market_followup.py`, famílias nativas de mercado/cura/paralisia,
`test_spell_engine` e `test_generic_spell_retry`. O lote `inventory_summons`
acrescenta `market-followup-smoke.cjs`: oferta do Mestre e venda pelo jogador,
condição preservada, cura paga, ficha de Klhauss, uso de magia e retorno ao local.
O lote prepara o objeto usado e os serviços na própria cópia TEMP; não operar
ensaio nas fichas reais. Thoradin, Conclave e Klhauss precisam existir na cópia.
Resultados finais e ativação devem ser registrados após execução efetiva.

## Resultado e ativação — 30/10/2026

- Regressão final: **92 testes backend PASS**, mais dois checks do preparador
  TEMP. A descoberta geral anterior executou 1.747 testes, sem falhas de
  asserção, com 37 erros de permissão na trava de RAM e um skip. Os oito módulos
  afetados foram reexecutados com a permissão adequada: **134 PASS**.
- Frontend: **490/490** na rodada geral; após o último ajuste de Klhauss,
  **16/16** regressões relevantes, typecheck e build PASS.
- Ensaio nativo: quatro atores, três scripts visuais, Mestre desktop e jogador
  em viewport 390 px. Espada, arco, Dardos Místicos e Toque Chocante de Klhauss
  executados; contadores independentes 3/3 → 2/3 e volta ao Conclave conferidos.
  Capturas inspecionadas explicitamente. Isso não certifica toda a ficha nem
  uma sessão real em redes diferentes.
  Repetição final em `TEMP/omni-market-followup-v7`, copiada em modo somente
  leitura do banco já ativado, também PASS; o preparador não depende de um
  script externo ou de configurar manualmente a cópia.
- Corrigida a leitura de raça no formato raiz existente da ficha, sem regravar
  a ficha. Cura normal continua bloqueada para vampiros/mortos-vivos/constructos.
  Conjuração genérica não pode contornar um repertório explícito com usos.
- Backup `operational-backup-20261030-040259`; somente backend reiniciado,
  listener `127.0.0.1:8787`, PID 9440. Quatro serviços publicados no Conclave;
  sete serviços no total. Klhauss configurado no token original.
- Conferência dos dados protegidos antes/depois: fichas, carteira, inventário,
  notas, condições, mapas/posições/fog, sessão/combate e credenciais preservados.
  Mudanças operacionais limitadas aos serviços e à ficha NPC de Klhauss.
- Endereço público, bundle atualizado e mercado autenticado de jogador:
  **HTTP 200**. OpenCode e túnel não reiniciados. Sem staging, commit ou push.

Limites: quatro serviços mágicos revisados, não todo o catálogo; objetos usados
adquiridos permanecem separados, sem reparo/revenda individual automática;
não houve validação independente em celular físico/4G após a ativação.

Arquivos deste corte:

- Backend: `app/{catalog_spell_contracts,commerce_routes,map_commerce,merchant,spell_engine,merchant_appraisals,merchant_magic,npc_campaign_profile,npc_spell_resources}.py`.
- Ensaios: `backend/test_market_followup.py`, `backend/scripts/{run_sheet_test,market_followup_fixture}.py`, `frontend/tests/market-followup-smoke.cjs`.
- Frontend: `src/{api,commercePresentation}.ts`, `src/components/{CommerceHistory,MapCommerce,MonsterAttackPanel,IndividualAppraisal}.tsx`, `src/pages/SessionWorkspace.tsx`.
- Documentação: este arquivo, `CURRENT_COMPANION_CODE.md` e `AI_TEST_TOOLS.md`.
