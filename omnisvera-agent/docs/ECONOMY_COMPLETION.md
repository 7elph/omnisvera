# Mercado nativo — compra, venda e serviços

Usa `merchants`, `merchant_stock`, `merchant_services`, inventário nativo,
carteira da ficha, comandos idempotentes e `session_ledger`. Não há uma
segunda carteira. Valores são inteiros em cobre; PC=1, PP=10, PO=100,
PL=10000. O recibo preserva as denominações e informa saldo antes/depois.

- Thoradin negocia equipamentos, suprimentos e poções comuns. A poção de HP
  da campanha custa 5 PO, antes da barganha.
- O Conclave negocia itens arcanos. Klhauss aparece no card do estabelecimento;
  o pin antigo permanece cadastrado e pode participar de combate, mas não
  intercepta o local fora de combate. Notas privadas não entram no card público.
- Recompra usa o percentual do estabelecimento. A base é o menor valor entre
  o cadastro e uma oferta local equivalente: um item vendido por 10 PO não
  pode ser recomprado por 100 PO por causa de um preço diferente no livro.
- A barganha permanece na compra, com a rolagem e o multiplicador no recibo.
  Não foi inventada uma regra nova de barganha para venda ou serviços.
- Serviços executáveis: avaliação do inventário, reserva de hospedagem e
  entrega de item identificado. Entrega vinculada ao estoque consome esse
  estoque; hospedagem não concede descanso instantâneo. Avaliação informa
  preços desconhecidos e restrições, sem presumir preços de itens únicos.
- O Mestre pode definir valor e grupo comercial de um item no catálogo
  unificado. Itens equipados, sem preço, parcialmente carregados ou
  modificados não são revendidos automaticamente como novos; a UI explica.

Compra, venda, entrega e confirmação usam o fluxo de orçamento → confirmação.
Cancelamento não altera saldo ou estoque. Repetir a confirmação devolve o
mesmo recibo. Novos recibos contêm estoque, inventário, carteira e identidade
dos objetos. O histórico é restrito ao dono da ficha/Mestre; recibos antigos
sem saldo anterior são identificados como históricos parciais.

## Manutenção aprovada

`app/approved_market_setup.py` é uma operação administrativa explícita, nunca
executada no carregamento da página. Verifica os dois recibos de Raziel de
13,5 PO, recalcula duas poções de 5 PO com desconto de 10% e credita somente
os 18 PO aprovados. A origem é única e um retry não duplica o crédito.
Organiza os estoques existentes sem destruir itens, configura três serviços,
registra as alterações no ledger e permite reposição finita explícita do pó.
Não reconcilia quantidades históricas ambíguas por suposição.

## Validação e limites

Testes: `test_economy_completion`, `test_approved_market_setup`, suites nativas
de mercado/registro/poções e `economy-presentation.test.cjs`.
O lote visual `inventory_summons` inclui `potion-skeleton-smoke.cjs` e
`economy-market-smoke.cjs`. Este último usa uma cópia TEMP previamente
configurada dos estabelecimentos de Nimalis, quatro fichas copiadas, cliente
Mestre desktop e Raziel mobile; imagens exigem aceitação visual do agente.

Negociação individual de objetos danificados, conjuração genérica como serviço
e execução automática de todos os gaps do catálogo continuam fora deste corte.
Ensaio em localhost não prova estabilidade em redes externas diferentes.
Klhauss recebeu identidade pública e associação ao estabelecimento; sua ficha
de combate Rank S não foi inventada. Arte ausente, como a do pó, usa ícone
genérico; nenhuma nova imagem foi gerada nesta manutenção.

## Evidência de ativação — 29/10/2026

- Backup: `OmnisveraBackups/economy-20261029-231754`.
- Reembolso real: 18 PO, uma vez. Poção a 5 PO. Thoradin com 38 linhas de
  estoque; o pó foi transferido ao Conclave e reposto em cinco unidades.
- Dois serviços de avaliação e uma reserva de hospedagem configurados.
- Backend reiniciado; health, página HTTPS pública e loja com acesso de
  jogador responderam 200. Histórico de outro personagem respondeu 403.
- Conteúdo protegido de 25 tabelas conferido contra o backup. Fora das
  alterações aprovadas, o startup só atualizou datas de Earthropo/Nimalia.
- Backend: 1.734 testes na suíte geral; 17 falhas e um erro decorreram da
  sobreposição do ensaio visual com a trava de recursos. Os 43 testes das
  duas suítes afetadas passaram isoladamente. Os 76 testes finais de mercado,
  poções e cópia de mídia passaram (um skip).
- Frontend: 490/490; typecheck e build aprovados. O aviso de tamanho dos
  bundles permanece. Diff check aprovado; sem staging, commit ou push.
- Ensaio TEMP final: quatro atores, dois scripts visuais, Mestre desktop e
  jogador 390 px; compra/venda/barganha/serviços, retry, estoque entre clientes,
  poção única em Recursos, substituição da invocação antiga e reload passaram.
  Oito capturas foram revisadas e aceitas pelo agente. A cópia de mídia do
  ensaio agora inclui os ícones dos itens efetivamente ofertados.

Arquivos deste corte: `backend/app/{approved_market_setup,commerce_routes,
item_registry,map_commerce}.py`; `backend/scripts/{fixture_media,run_sheet_test}.py`;
`backend/test_{approved_market_setup,economy_completion,fixture_media,
item_offer_readiness}.py`; `frontend/src/{api,commercePresentation}.ts`;
`frontend/src/companionTheme.css`; `frontend/src/components/{CommerceHistory,
CommerceItemImage,MapCommerce}.tsx`; `frontend/src/pages/SessionWorkspace.tsx`;
`frontend/tests/{economy-market-smoke.cjs,economy-presentation.test.cjs}`;
este documento, `CURRENT_COMPANION_CODE.md` e `AI_TEST_TOOLS.md`.
