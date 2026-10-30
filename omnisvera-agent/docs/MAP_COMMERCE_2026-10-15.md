# NPCs, locais e comércio no mapa

O pin nativo abre ofertas de um ou mais mercadores existentes. O Mestre pode
vincular o mercador a um NPC do diretório e a um local da biblioteca, configurar
estoque, preço, percentual de recompra e serviços dentro da janela do pin.
Nenhuma ficha, mapa, carteira ou inventário paralelo é criado.

## Uso

- Clique num pin de local/NPC. O Mestre encontra `Configurar ofertas` na janela.
- Escolha um mercador existente ou crie um estabelecimento para esse pin.
  NPC responsável e local são opcionais; a visibilidade deles é respeitada.
- O jogador vê Comprar, Vender e Serviços. Escolher uma oferta abre o valor
  final e Confirmar/Cancelar. Abrir/cancelar não altera moedas nem inventário.
- Venda aceita itens do catálogo guardados no inventário. Itens sem avaliação
  continuam na negociação mediada pelo Mestre. A recompra padrão existente
  é 50%, editável por estabelecimento; o item vendido entra no estoque.
- Serviços neste corte: entrega de uma quantidade configurada de um item do
  catálogo e hospedagem. Hospedagem é uma reserva paga, concluída pelo descanso
  completo que o Mestre já concede. Não restaura recursos ao comprar a reserva.
  O jogador pode ter uma reserva pendente. Retirar um serviço não cancela reservas.

## Autoridade e persistência

`merchants`/`merchant_stock` são reutilizados. O vínculo usa `token_id`, `npc_id`
e `location_id`; `enabled` permite fechar ofertas sem remover pins. Tabelas de
cotações, recibos, barganhas e reservas suportam o comércio nativo.

O backend calcula preços em unidades inteiras de cobre, troco e saldo. O jogador
não envia preço, d20 físico nem personagem de outra pessoa. Cotações duram dez
minutos e ficam vinculadas ao acesso, personagem, mercador, oferta e quantidade.
Oferta alterada, estoque insuficiente ou saldo insuficiente rejeitam a confirmação.
`BEGIN IMMEDIATE` protege estoque/carteira/inventário/recibo na mesma transação.
Retry com a mesma chave ou confirmação repetida da mesma cotação retorna o recibo,
sem cobrar novamente. Reutilizar chave para outro conteúdo é rejeitado.

Barganha reutiliza o cálculo existente de Carisma e faixas de preço. Seu resultado
é reutilizado para o mesmo personagem/mercador/item até o descanso do Mestre,
inclusive a penalidade de uma falha. Novas cotações/quantidades não rerrolam o dado.
O descanso invalida cotações anteriores. Relações/favores são preservados, mas não
modificam preços automaticamente sem uma regra específica aprovada.

Cada transação gera ledger legível, histórico do NPC vinculado e a notificação
`session_changed` pela infraestrutura existente. Outros clientes atualizam ofertas.
Moedas incrementam a versão da ficha. Itens do catálogo preservam identidade,
descrição e dano cadastrado por meio do enriquecimento nativo do inventário.

## Limites

- Jogador negocia em estabelecimento revelado no mapa ativo; não exige proximidade
  tática. Mapas de exploração podem não ter grid.
- Não interpreta texto livre de serviço/magia nem inventa dano ausente no catálogo.
- Cura, durabilidade/reparo de equipamento, reputação alterando preços e reposição
  automática de estoque não fazem parte dos dois tipos de serviço deste corte.
- Estoque, preços e serviços reais devem ser cadastrados pelo Mestre. Os ensaios
  usam apenas a cópia SQLite/vault temporária e credenciais CF-01.

## Verificação

`backend/test_map_commerce.py` cobre permissões, cálculo, concorrência, retry,
expiração, saldo, visibilidade, serviços e integração com descanso/histórico.
`frontend/tests/map-commerce-smoke.cjs` usa Nimalis da cópia da campanha,
preserva os pins existentes e testa o ciclo em Mestre desktop + jogador mobile,
com dois contextos de navegador e reload. Integra `companion-tests` com quatro
atores e `ui: true`. Resultado API/UI local não certifica celular físico ou redes externas.

## Resultados e ativação

- Suíte completa de backend: 817 testes PASS no ambiente `.venv-observer`, com
  as dependências MCP já instaladas. A primeira execução no `.venv` usual terminou
  com erro de importação de `mcp`; esse ambiente não certificou a suíte completa.
- Regressão final de comércio: 22 PASS (14 novos + 8 legados), incluindo dois
  jogadores disputando a última unidade e incremento único da versão da carteira.
- Frontend: 295 PASS; regressão final de mapas/NPCs/design: 18 PASS.
- Typecheck, build e `git diff --check`: PASS. Aviso de tamanho dos bundles permanece.
- Nimalis real da cópia: 15 pins preservados; um pin comercial adicional somente
  na fixture para verificar a mesma janela em NPC e local. Compra/cancelamento,
  barganha, venda/reposição, entrega, reserva, retry, dados privados, rejeição sem
  cobrança, histórico, segundo navegador e reload: PASS.
- Fog: pintar, persistir/recarregar, mobile e controle exclusivo GM: PASS.
  A aba Mapas agora alterna `Interagir com pins` e os pincéis; o modo de interação
  permite abrir NPCs/locais sem a fog interceptar os cliques.
- MCP `test-35c0a13e89c34cb4be5c35a7663279f5`: COMPLETED/PASS,
  quatro atores, um cenário API selecionado e 10/10 scripts UI PASS, incluindo
  `map-commerce`. Aceitação visual explícita das capturas desktop e 390 px;
  `physical_actions=false`. Não é certificação integral de todas as fichas.
- Tentativa anterior `test-815e220276b3407d834cdcd627989289`: TIMEOUT/INCONCLUSIVE
  durante UI, após o relatório parcial registrar 79 PASS e 3 EXPECTED_BLOCK de API.
  Esse job não foi declarado PASS. A execução seletiva acima concluiu a etapa visual.

Capturas finais privadas: `%TEMP%/omni-commerce-ui-k2XBWY`, incluindo
`nimalis-player-390.png`, `nimalis-gm-1440.png` e `nimalis-npc-player-390.png`.
As capturas e o banco de testes não são conteúdo operacional/publicável.

Backend operacional reiniciado de PID 147352 para 169960, backup privado
`backend/data/backups/pre-map-commerce-20261015-152045`. Tokens iguais por
comparação semântica. Dezessete tabelas duráveis idênticas ao backup; em mapas,
somente `updated_at` de Nimalis/Earthropo/Nimalia mudou pelo seed nativo do startup.
Imagens, pins, posições, fog, inventários, fichas, NPCs e combate preservados.
Nenhuma compra, descanso ou cadastro de ensaio foi aplicado à campanha operacional.
Health autenticado, frontend público e endpoint de comércio: HTTP 200.
Bundle final servido: `index-BxXB69Ka.js`; túnel PID 6196 preservado.

Arquivos deste corte:

- `backend/app/map_commerce.py`, `commerce_routes.py`, `merchant.py`, `main.py`,
  `character_play.py`, `backend/test_map_commerce.py`, `backend/scripts/run_sheet_test.py`.
- `frontend/src/components/MapCommerce.tsx`, `frontend/src/api.ts`,
  `frontend/src/pages/SessionWorkspace.tsx`, `frontend/src/companionTheme.css`.
- `frontend/tests/map-commerce-smoke.cjs`, `frontend/tests/fog-controls-smoke.cjs`.
- Este documento, `docs/CURRENT_COMPANION_CODE.md` e `docs/AI_TEST_TOOLS.md`.

Worktree misto preservado; sem staging, commit ou push. Ofertas reais permanecem
sob cadastro do Mestre, sem importar para a mesa os estoques/preços fictícios de QA.

## Loja de Thoradin — estoque operacional

A pedido do Mestre, configurada `Equipamentos de Thoradin` no pin original
`monster:6624c761ea5b4cbf8062de90dfc40521`, em `official:nimalis`.
Mercador `merc-6dde4287f7`, vinculado ao registro de Thoradin no diretório (ID 19),
com raça Anão e descrição informada pelo Mestre. Nenhum pin duplicado.

37 tipos de produto, 189 unidades/lotes, todos com estoque finito e preços do
catálogo: armas comuns, arcos/besta, lotes de flechas, armaduras, escudos e
equipamentos de aventura. Não foram adicionados itens mágicos ou as entradas
ambíguas de extração do catálogo (ex.: armadura completa cadastrada como 2 PO).
Recompra de 50%, barganha e compras já disponíveis pelo pin. Nenhum serviço
extra foi cadastrado neste pedido de estoque.

Consulta autenticada como Vezemir confirmou as 37 ofertas, todas com quantidade
positiva e preço presente. Comparação com o backup confirmou ficha, inventários,
combate, pins, posições, grids e mapas inalterados. Nenhuma compra de QA na mesa.
Backup e relação detalhada privados em
`backend/data/backups/pre-thoradin-stock-20261015-162536/`.
Somente configuração de dados; não exigiu alteração de código nem restart.

## Ajuste de apresentação — Thoradin, NPCs e header

- As 37 ofertas usam o catálogo de imagens já usado no inventário, sem gerar
  imagens novas. Quantidade agora diz `N disponíveis`, distinguindo estoque
  de preço. Falha de imagem termina em placeholder, sem ciclo de tentativas.
- Sem novos serviços: o pedido anterior abasteceu somente produtos. Reparo e
  encantamento não foram cadastrados nem simulados como serviços de entrega.
- Auditoria encontrou 17 registros de NPC, sem duplicatas de cadastro. A lista
  repetia a mesma identidade entre diretório, fichas reservadas e pins.
  A projeção agora unifica essas entradas, com acesso ao histórico e à ficha
  original do mapa. Pins distintos homônimos ficam agrupados, não excluídos.
- Header: retrato, nome, classe, barra de vida e nível ao lado da barra; sem
  números de PV nem status extras nessa área. Status continuam na ficha.

Mudanças deste ajuste: `npcLibrary.ts`, `MasterNpcLibrary.tsx`, `NpcDirectory.tsx`,
`PartyMemberSummary.tsx`, `SessionWorkspace.tsx`, `CommerceItemImage.tsx`,
`MapCommerce.tsx`, `companionIconCatalog.ts`, `companionTheme.css`; testes
`npc-library-identity`, `party-summary`, `commerce-presentation`, atualização de
`active-effect-icons` e smoke `shop-header-library` no runner nativo.

Backend: 819 testes PASS; frontend: 300 testes PASS; typecheck e build PASS (aviso já existente de chunk
grande). Ensaio específico desktop/390 px PASS e capturas inspecionadas em
`%TEMP%/omni-shop-header-g7vrMd/`: imagens reais dos 37 itens, nível alinhado,
ausência de PV numérico, Thoradin único, instâncias de Lich preservadas e acesso
diretório → ficha do pin. Não prova celular físico nem redes distintas.

MCP `test-85d3a75b693b4aa684a4444b61a2c9d7`: COMPLETED/PASS, quatro atores,
um cenário API selecionado e 11/11 scripts UI PASS, incluindo comércio, descanso,
seleção no grid e o novo smoke de loja/header/biblioteca. `physical_actions=false`;
não significa todas as habilidades certificadas. Sem alterações de regras.

Frontend público respondeu HTTP 200 com `index-uNw3Mubd.js`. Código do backend
operacional não mudou neste ajuste, portanto sem restart necessário. Sem
compras/descansos de QA no operacional, exclusão de NPCs, staging, commit ou push.
Uso auxiliar de REA e fluxo para próximos lotes: `AI_ACTION_HANDOFF_2026-10-15.md`.
