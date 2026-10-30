# Preparação para sexta — evidência e limites

## Retomada de 23/10 — bloqueio confirmado, sem certificação visual

- Branch `devin/create-omnisvera-class-standard`, HEAD `1a07a84`.
- Verificação nativa: 289 MB disponíveis inicialmente; limpeza por recibo
  encontrou zero resíduos elegíveis. Medições seguintes: 286–394 MB de
  8105 MB físicos. A variação não é contabilizada como memória liberada.
- Companion segue escutando em 8787 (worker 227744); acesso OpenCode via
  Tailscale segue escutando em 4096. Nenhum deles foi fechado/reiniciado.
- `PcaSvc` continua Running com 57.484 handles. É indício da investigação
  anterior, não prova nova da quantidade de RAM recuperável. O token Windows
  não é administrativo; nenhum serviço, segurança ou aplicativo foi alterado.
- Primeira tentativa `test-c6ee7c35c7e04b3cb49dc5f768ddb1e0` falhou antes
  do ensaio: sandbox negou acesso à trava existente em AppData. Foi preservado
  o erro, sem remover a trava ou criar mecanismo paralelo de execução.
- Retomada com acesso específico aprovado ao executor:
  `test-056ac371ed7c4065845769ef5a929bc7`, quatro atores, `ui:true`, lote
  `friday`. Após a espera limitada, terminal **MEMORY_UNAVAILABLE**;
  `report=null`, `certification_ready=false`. Fixture e navegador não iniciaram.
  Validação visual e ensaio integrado permanecem **INCONCLUSIVE**.
- Auditoria HTTP somente leitura reexecutada: seis cenas privadas, 18 imagens
  sem falhas, quatro perfis sem acesso aos rascunhos e 24 detalhes privados
  retornando 404. Nenhuma mutação enviada; isso não substitui screenshots.
- Não houve alteração em fichas reais, compras, descansos, combate ou tokens;
  não houve nova tentativa repetitiva, staging, commit ou push.

Os resultados abaixo são históricos de 22/10; não são novos testes completos
executados em 23/10.

## Quatro pontos pedidos

1. **Cenas:** conferidos os seis rascunhos pelo backend atual. As 18 imagens
   vinculadas a capas, mapas, atores e NPCs relevantes respondem HTTP 200.
   Quatro perfis não recebem esses rascunhos na lista; os 24 pedidos de detalhe
   privado retornam 404. Checklist continua 16/17: **aceitação visual pendente**.
2. **Percurso integrado:** acrescentado ao executor/MCP existente o lote
   explícito `friday`, obrigatório com `ui:true` e os quatro atores. Não há
   novo motor, servidor, protocolo ou credenciais operacionais no ensaio.
3. **Falhas corrigidas:** a fixture visual não incluía capas de cenas/retratos
   de NPCs; agora inclui esses campos de imagem, sem ler notas privadas. A
   admissão negada por RAM era rotulada como HARNESS_ERROR; agora fica
   MEMORY_UNAVAILABLE somente com marcador e fase comprovados, sem relatório.
   Código de saída 2 sozinho ou relatório existente não ocultam falhas reais.
4. **Arte:** capa ilustrada nova do escritório, gerada e inspecionada, ligada
   apenas à cena privada 28. O mapa esquemático, sua escala, grid, posições e
   fog permanecem iguais. Os dois papéis sem identidade definida (representante
   militar e mestre do Conclave) mantêm ícones genéricos; não se inventou um
   rosto/identidade canônica para eles.

## Lote integrado nativo

Sete scripts fixos, sequenciais na mesma fixture:

- `scene-preparation-smoke.cjs`: seis blocos, 1440/390 px, capas, diálogo,
  zoom delimitado, filtragem privada; abrir cards não publica/ativa/move.
- `thoradin-wallet-smoke.cjs`: Raziel compra a mochila de 5 PP na loja real
  de Thoradin copiada; cancelamento, ouro preservado, quantidade, retry,
  atualização de estoque numa segunda página local e reload.
- `three-sheet-actions-smoke.cjs` + `three-sheet-actions-second-smoke.cjs`:
  duas metades nativas das dez ações de combate já aprovadas.
- `hemomancy-passives-smoke.cjs` e `summon-turns-smoke.cjs`: passivas e
  permissões/turnos das invocações.
- `four-sheet-rest-smoke.cjs`: descanso geral, remoção de estados e reload.

O lote `full` continua com 12 scripts; não foram elevados timeouts, teto de
20 minutos, paralelismo ou margem de 1024 MB. Scripts novos possuem guardas de
loopback 8871, SQLite/vault TEMP e credenciais públicas CF-01, antes de mutações.
Dois clientes locais não certificam redes externas/celular físico.

## Resultado de execução

**UI e ensaio integrado: INCONCLUSIVE, não executados.**

- Primeira chamada nativa: `test-2d53bbcd68f0400db70ad2946f64e776`, lote full.
  Negada antes da fixture; erro genérico antigo motivou a correção acima.
- Após corrigir ferramentas/adicionar lote, nova chamada com intenção distinta:
  `test-61382fbfa3b44107aced9e2a096f7c48`, lote friday. Terminal
  MEMORY_UNAVAILABLE após a espera limitada. `report=null`, sem screenshots,
  `certification_ready=false`, sem fixture/navegador iniciados.
- RAM inicial: 212 MB de 8105 MB; outra medição 735 MB, abaixo da margem.
  Limpeza determinística de resíduos registrados encontrou zero elegíveis.
  Inventário do navegador não tinha abas abertas para reaproveitar.
- Não houve terceira repetição, remoção de trava ou alteração de Defender,
  conectores, serviços ou configurações do Windows para forçar aceitação.

Não marcar o último checkbox de Cenas a partir de API/unit tests. O ensaio
continua pendente de recursos, não de uma operação que o Mestre precise rodar.

## Arte aplicada e segurança

Arquivo: `frontend/public/companion-assets/preparations/friday-office-v1.png`.
Modo: built-in image_gen; prompt integral/proveniência em
`preparation/FRIDAY_ASSETS.json`. Arte de ambientação, sem texto legível,
personagens ou afirmação de autoria/conspiração. Não é mapa tático.

Atualização nativa da cena com `expected_version`; backup privado em
`TEMP/omni-friday-cover-k734fb70/before.sqlite3`. Onze tabelas protegidas
inalteradas (fichas, inventário, combate, mapas/pins/fog, estoque e sessões).
Nenhuma cena foi publicada aos jogadores, nenhum combate/sessão foi iniciado e nenhuma
compra ou recompensa foi aplicada aos personagens reais. Capa serve HTTP 200,
com hash igual ao arquivo local. Sem restart de Companion ou OpenCode: apenas
scripts de teste e conteúdo foram alterados, não handlers operacionais.

A ilustração é servida como asset estático público, sem notas/segredos do Mestre.
A cena, seus textos, elenco e elementos continuam privados.

## Checks deste corte

- Backend focal: 124 testes executados, 123 PASS e 1 skip de ambiente.
  Inclui ferramentas/MCP, contenção/recursos, mídia, moedas, comércio, saque,
  circuito de combate/saque, inventário e encaixes.
- Frontend: 386/386 PASS, sequencial (91,4 s).
- `npx --no-install tsc --noEmit`: PASS. Build Vite PASS (18,28 s), em pasta
  de staging privada. Bundles JS/CSS iguais aos já servidos: nenhuma troca de
  índice necessária. A capa nova é servida pelo mount nativo de companion-assets.
  Permanece o aviso preexistente de chunks acima de 500 kB.
- Os dois scripts novos passam em `node --check`; não confundir análise de
  sintaxe/contrato com execução real do navegador.
- Suíte backend integral tentada com a venv de observação; não concluiu e o
  runner criado nesta etapa foi encerrado por identidade verificada. Resultado
  integral INCONCLUSIVE. Não foi encerrado processo de usuário/Companion/OpenCode.
- Diff check dos arquivos deste corte: PASS. Aviso de normalização CRLF não é
  falha de teste.

## Arquivos

- `backend/scripts/agent_test_jobs.py`, `companion_test_mcp.py`,
  `run_sheet_test.py`, `fixture_media.py`: lote/diagnóstico/mídia.
- `backend/test_agent_test_tools.py`, `test_sheet_runner_batches.py`,
  `test_fixture_media.py`: regressões determinísticas RED/GREEN.
- `frontend/tests/scene-preparation-smoke.cjs`, `thoradin-wallet-smoke.cjs`,
  `friday-readiness.test.cjs`: ensaios fixos e contrato/asset de preparação.
- Arte acima, `docs/preparation/FRIDAY_BLOCKS.json`, `FRIDAY_ASSETS.json`,
  `docs/AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md` e este relatório.

Worktree anterior preservado. Helpers/relatórios privados em `.autonomy/runtime`
e TEMP não pertencem ao commit. Sem staging, commit, push ou alteração global
do MCP. OpenCode já aberto pode precisar recarregar somente o conector de
testes para reconhecer `friday`; isso não foi acionado nesta etapa.
