# Descanso geral — quatro fichas

## Estado atual

**Lote focal V3 COMPLETED/PASS**, dois cenários API e dois scripts UI.
Capturas desktop e PV/Status dos quatro atores em 390 px revisadas.
V1/V2 FAIL preservados; não é certificação integral da interface/mesa real.
Nenhuma regra ou mutação operacional foi realizada por este corte.

## Escopo

- Reutiliza o executor/MCP nativo, com os quatro atores e `ui:true`.
- Dois scripts fixos: `map-toolbar-rest-smoke.cjs` e
  `four-sheet-rest-smoke.cjs`; full permanece com seus 12 scripts.
- Mesmos limites: 300 s por script e 1.200 s por job, fixture exclusivamente TEMP.
- Botão Mestre Descanso geral: PV, PV temporários, condições, recursos,
  ícones na área Status e reload em 1440/390 px.
- Quantidades de consumíveis não devem ser repostas; bônus permanentes de
  equipamento não são efeitos temporários. NPC alheio deve ser preservado.
- DORN-7 é a ficha `dorn7`, controlada pelo Mestre; não criar outro Dorn.

## Evidência obtida

- RED: quatro verificações falharam antes da extensão do lote/schema/leitor.
- GREEN: 48 testes no observer existente, incluindo contratos MCP, isolamento,
  idempotência do job, lotes, leitura de evidência, descanso completo, Caixão,
  escopo de mapa e ícones. Isso não é execução do novo smoke visual.
- Mesma seleção sem o teste de schema MCP: 47 testes OK no runtime nativo.
- OpenCode produziu o script visual: sintaxe Node OK, dois testes de toolbar
  e sete de integridade/retry PASS; não são aceitação visual.
- Baseline de dez tabelas operacionais capturado por leitura antes da execução.
- Nenhum commit/push, reinstalação ou reinício do Companion/OpenCode/túnel.
- Frontend completo: 354 PASS; typecheck PASS; build PASS (14,80 s), bundle
  `index-BTITC67R.js`. Local e público 200 com esse bundle. Primeiro build
  preventivamente não iniciado com 227 MB livres; nova tentativa admitida
  após recuperação de memória, sem remover o piso de 512 MB.

O lote foi adicionado também ao leitor privado de relatórios de Cenas, somente
em disco; o processo operacional ainda não foi recarregado por este corte.
Não confundir essa allowlist com publicação de novas regras de jogo.

## Tentativa V1 e diagnóstico do ensaio

`test-d870555cf673495d9c8f663d5a09ce27`: COMPLETED/FAIL, exit 1.
Map-toolbar-rest PASS (137,693 s); four-sheet-rest FAIL (128,801 s) na
asserção global de zero elementos `role=alert` (havia três). Todos os asserts
de PV, condições, recursos, quantidades e cargas anteriores a esse ponto
passaram. Isso não identifica o conteúdo/origem dos três avisos.

O diagnóstico foi ampliado sem mudar o produto: baseline antes de descansar,
quatro respostas nativas obrigatórias, rejeição de novos alertas e de erro do
workspace; em falha, captura/textos privados. Helper multiset com RED/GREEN;
12 regressões frontend PASS e sintaxe Node OK. A V2 preserva o FAIL da V1.

## V2 e correção mínima de carregamento

`test-557199136deb4e6682ddce9c567ae37d`: COMPLETED/FAIL, exit 1.
Map-toolbar-rest PASS (110,311 s); four-sheet-rest FAIL (106,465 s).
O log/captura identificou dois avisos de composição de imagens e timeout real
de atualização de combate/mapa após o descanso, com erro visível no workspace.
Não foi reclassificado como PASS porque as mutações do descanso funcionaram.

Ao abrir Mestre, o `MasterAssetPanel` era montado mesmo dentro do details fechado,
iniciando polling e consultas de referências. Três testes RED demonstraram essa
montagem indevida. Patch restrito a um estado e montagem condicional no disclosure;
abrir mantém a ferramenta disponível e fechar desmonta seu polling. Eventos de
details internos não alteram o estado externo. GREEN: 28 testes focais, depois
354 frontend completos. Ainda não prova que era a única causa do timeout.

V3 exige zero consultas de assets enquanto fechado e adiciona capturas focadas
de PV/Status mobile. Nenhum timeout foi ampliado nem erro suprimido.

## V3 — resultado terminal e aceitação focal

`test-b808a5cb5a63465f9c98c12984bb8a38`, request
`codex-friday-rest-ui-20261020-v3`: COMPLETED/PASS, exit 0.
API: `raziel:Anel Rúnico` e
`raziel:Caixão: descanso próprio, retry e recarga somente pelo Mestre`: PASS.
Map-toolbar-rest PASS (113,086 s); four-sheet-rest PASS (122,179 s).
Antes/depois do descanso: nenhum alerta; nenhum erro do workspace; nenhuma
consulta de assets com painel fechado. O timeout da V2 não reapareceu nesta
repetição; isso não garante ausência de outras causas/redes lentas.

Comprova nos quatro atores: PV restaurado, PV temporário/condições/efeitos
limpos, recursos e cargas `inn_rest` recarregados, quantidades de inventário
inalteradas, efeito de NPC alheio preservado e persistência após reload.
UI GM 1440/390 e jogador Vezemir 390 sem comando de descanso do Mestre.
Clonagem continua legitimamente bloqueada sem componente, mesmo com contador
restaurado; descanso não entrega fragmentos.

Capturas privadas em
`C:/Users/delib/AppData/Local/Temp/omni-four-sheet-rest-AVwezH`:
os quatro `*-after-1440.png` e oito recortes `*-vitals-after-390.png` /
`*-status-after-390.png` foram inspecionados. PV/Status legíveis; passivas
preservadas e contadores restaurados. Há mídias ausentes na fixture de Dorn;
esta aceitação focal não certifica a biblioteca inteira de imagens.

Fixture encerrada, porta 8871 livre; Companion 253068 e OpenCode 38768 mantidos.
Discover backend geral preventivamente não iniciado: 443 e depois 333 MB
livres, abaixo do piso de 512 MB. Não inventar novo PASS geral; o último discover
completo documentado ainda tinha erros do SDK MCP no runtime nativo.
Typecheck/build PASS e 354 frontend PASS pertencem à versão ensaiada.

## Preservação operacional

Baseline/read-only de dez tabelas: nove permaneceram iguais. A tabela de pins
mudou durante o intervalo: posição visual de um local e timestamp de um monstro;
o operacional recebeu requisições de edição/viewport nesse intervalo. Não se
atribui autoria nem se desfaz essa atividade concorrente. Nenhum descanso foi
concedido no banco real por este ensaio, que autentica somente na fixture TEMP.

## Limites

Conectividade multirrede, celular físico, todos os efeitos/cargas especiais,
estoques comerciais e certificação integral continuam inconclusivos.
`all_actions_certified:false`; UI de jogador observada neste lote é Vezemir,
não três jogadores simultâneos. Resultados anteriores não são reclassificados.

## Arquivos deste corte

- Produto: `frontend/src/pages/SessionWorkspace.tsx` (disclosure Assets).
- Ferramentas: `backend/scripts/run_sheet_test.py`, `companion_test_mcp.py`,
  `agent_test_jobs.py`; `backend/app/test_run_evidence.py` (allowlist em disco).
- Regressões backend: `backend/test_sheet_runner_batches.py`,
  `backend/test_test_run_evidence.py`.
- UI/contratos: `frontend/tests/four-sheet-rest-smoke.cjs`, `rest-alerts.cjs`,
  `rest-alerts.test.cjs`, `master-assets-lazy.test.cjs`.
- Documentação: este relatório, `AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md`,
  `FRIDAY_CLOSURE_2026-10-20.md`.

Arquivos anteriormente alterados por outros cortes continuam preservados;
não atribuir todo o diff misto a esta continuação. Sem staging/commit/push.
