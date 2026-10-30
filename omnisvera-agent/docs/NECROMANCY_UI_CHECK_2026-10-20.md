# Morthak — necromancia e invocações

## Estado atual

- **Lote focal V6: PASS**, cinco cenários API + um bloqueio legítimo, seis usos
  UI nos três scripts. Capturas desktop/390 px revisadas.
- **Frontend corrigido e servido:** reabrir o esqueleto após gastar a ação;
  build `index-BJC6UolP.js`, home local/pública 200.
- **Backend ativado em 20/10, 17:18:** restart autorizado somente do 8787;
  invocação dispensada não volta como cadáver. Worker novo `253068`, launcher
  `255756`; health/home local e home pública 200, bundle atual confirmado.
- Nenhuma ficha/inventário real alterado, sem commit/push. Fragmento somente na
  fixture. Sem certificação integral ou mesa multirrede.
- Checks finais: 1.172 PASS backend nativo, dois erros + um skip de SDK;
  30 testes no observer OK cobrem esses pontos. Frontend: 348 PASS.
  Typecheck final PASS (41,18 s); build atual PASS (15,24 s).

As seções seguintes preservam a evolução e tentativas anteriores; estados
pendentes/FAIL históricos não substituem este resumo atual.

### Ativação operacional autorizada

Backup consistente SQLite com `integrity_check=ok` em
`.autonomy/runtime/pre-necromancy-restart-20261020-171800`, incluindo cópia dos
tokens e configuração Cloudflare. Ambiente do processo anterior preservado,
sem executar instaladores, alterar modelos ou reserializar credenciais.
Processos antigos `253460/250736` substituídos somente no backend.

Comparação das 77 tabelas: fichas, inventários, acessos, sessão, combate e demais
dados preservados. Única diferença: `updated_at` dos mapas oficiais Nimalia e
Earthropo, atualização de bootstrap já existente. Tokens idênticos byte a byte.
Fichas de Morthak, Vezemir e Raziel: GET autenticado local e público 200. Acesso sem token
e rotas GM com credencial de jogador: 401, sem exposição de dados privados.
Uma asserção inicial esperava 403 na rota GM; a resposta real é 401. Foi
reverificada sem mudar a regra de autenticação.

OpenCode `38768` e Tailscale `6196` mantidos; nenhum teste com mutação no banco
real. O snapshot do mapa ativo não continha invocação dispensada para exercitar
esse caso operacionalmente; a regressão funcional permanece comprovada pela
fixture V6 e testes, não por uma nova dispensa no jogo real.

Escopo focal: Toque Sombrio, Aterrorizar, Levantar um Esqueleto, Animar Mortos,
Clonagem e Magia da Morte. Não altera regras, recursos ou fichas operacionais.

## Falha reproduzida e correção

Dispensar uma invocação salva HP zero e `summon.dismissed`, retirando seu turno.
A projeção `_token_record` tratava esse HP zero como morte e recriava `corpse`.
O frontend inclui cadáveres separadamente, portanto a unidade dispensada podia
reaparecer no mapa como cadáver. Regressão RED reproduziu o defeito antes do patch.

A projeção agora distingue dispensa de morte: não expõe cadáver nem permite
reanimar a unidade dispensada. Preserva o registro, auditoria, recurso gasto e
cadáveres de criaturas que morreram de verdade. Não devolve uso diário.

## Ensaio nativo preparado

`ui_suite:necromancy` no MCP/executor existente, com os quatro atores e `ui:true`:

- `morthak-necromancy-smoke`: Toque por card/alvo/Sim, confirmação automática,
  dano 1d4 e tick se acertar; Aterrorizar com alcance por nível e expiração se a
  JP falhar. Não força RNG para transformar resistência/erro em sucesso.
- `morthak-summons-smoke`: criação/reuso do mesmo esqueleto sem duplicação,
  cadáver no grid, Animar Mortos simultâneo, dispensa e reload sem pin fantasma.
- `morthak-high-spells-smoke`: Clonagem com execução de uma rodada, dois clones,
  consumo e fim de concentração; Magia da Morte com confirmação inclusiva,
  seleção automática, custo e retry.

O cenário API histórico ainda se identifica como `Toque Sombrio + dano/FOR/JPC`.
Esse ID estável não muda a regra atual aprovada: dano inicial 1d4 e perda de
1 PV nos turnos em que o d6 resulte 1–3; não perda de FOR ou JPC adicionais.

Somente TEMP, banco conferido pelo health, porta separada, autenticação CF-01.
Fragmento de cristal pode ser concedido explicitamente apenas na fixture,
usando o catálogo existente. Sem fragmento real, o bloqueio operacional continua
legítimo. Scripts anteriores, lease, 300 s/script e teto de 1.200 s preservados.

## Regressões iniciais (histórico)

- Regressão de dispensa: 1 PASS após o RED.
- Projeção/cadáveres, alcance e ciclo de efeitos: 48 testes OK.
- Mecânicas/contratos Morthak, delegados ao OpenCode: 63 testes OK.
- Componentes frontend de magias/invocações/revisão nativa: 23 PASS.
- Executor/MCP/leitor/isolamento: 52 testes OK no observer já instalado.
- Novo lote visual ainda não executado; capturas ainda não aceitas.
- Discover nativo: 1.174 entradas em 715,506 s; 1.170 PASS, dois erros de
  importação do SDK MCP ausente e dois skips. A execução nativa não é PASS.
  Repetição no observer instalado: 30 testes OK, incluindo ambos os erros e
  o contrato que havia sido pulado por SDK. Resta o skip de symlink no Windows.
- Frontend completo, sequencial: 342 PASS em 100,641 s, sem falhas/skips.
- Typecheck: PASS com heap Node limitado a 384 MB. Durante o check a memória
  livre caiu a aproximadamente 70 MB; concluiu sem intervenção.
- Build desta etapa não iniciado: 507.780 KB livres, abaixo da guarda de
  512 MB. O build PASS anterior não foi reexecutado; não há edição de código
  de aplicação frontend neste corte, somente novos scripts de ensaio.
- Sintaxe dos três scripts Node e `git diff --check` dos arquivos rastreados
  tocados neste corte: PASS (avisos preexistentes de normalização CRLF).

Arquivos deste corte: projeção em `backend/app/session_workspace.py` e regressão
em `backend/test_session6_combat.py`; suite/allowlist em `run_sheet_test.py`,
`companion_test_mcp.py`, `agent_test_jobs.py`, `test_run_evidence.py`; regressões
`test_sheet_runner_batches.py`/`test_test_run_evidence.py`; três scripts de UI
acima; este documento, `AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md` e índice
`FRIDAY_CLOSURE_2026-10-20.md`. Alterações anteriores/mistas preservadas, sem
staging, commit ou push.

Correção backend ainda **não ativada** no processo operacional. Sem prova nova
de celular físico, mesa em redes distintas ou ficha inteira certificada.

## Continuação — recarga e primeira execução

Recarga autorizada apenas de `companion-tests`: disconnect/connect HTTP 200.
Companion PID 253460 e OpenCode PID 38768 preservados, sem alteração de modelo
ou permissões. O pedido inicial levou ao recibo
`test-97394f52679f48b2bdd64b0180affa76`: COMPLETED/FAIL. API: cinco PASS e um
EXPECTED_BLOCK (Clonagem sem fragmento no inventário copiado).

A falha visual era do ensaio: ele esperava um POST de confirmação separado
depois de Toque Sombrio. O comando com `mode:automatic` já resolve e confirma
atomicamente, portanto não deve enviar aquele POST adicional. Captura revisada
mostrou card/grid/Sim concluídos e ação confirmada. Não foi necessário modificar
a habilidade. Novo teste de contrato reproduziu RED e passou após ajustar apenas
o smoke; 18 testes frontend focais PASS. O FAIL original permanece preservado.

As três hipóteses anteriores da revisão estática do OpenCode não comprovaram
defeito: `activateCard` é capturado no workspace; `abilityTargetControl` tem ramo
de grid com `armPcAction`, e nesse ramo não exige alvo pré-selecionado. Não se
modificou a UI com base nas hipóteses. A execução completa ainda é necessária.

Repetição `codex-friday-necromancy-ui-20261020-v2`, recibo
`test-8a946d921a114cc6b1191dade3560e03`, em andamento no mesmo executor isolado.
Não declara PASS nem certificação. Build novamente não iniciado: 303.852 KB
livres, abaixo da guarda de 512 MB, sem aumentar paralelismo ou encerrar serviços.

## Continuação — isolamento completo do filho e falha real de acesso

V2 não avançou do início dos cenários após health pronto. O Windows negou a
parada direta do filho, portanto aquele comando não encerrou nada. A desconexão
normal do próprio conector cancelou somente seu ensaio e limpou a fixture;
recibo CANCELLED/INCONCLUSIVE, nunca falha de regra. Companion/OpenCode intactos.

O filho de cenários ainda herdava stdin. Teste RED capturou a ausência de
DEVNULL; o runner agora o aplica também ao processo não interativo de cenários.
Nove regressões de startup/runtime e 56 de executor/MCP/leitor passaram. Isso
comprova o isolamento de entrada, não determina sozinho a causa do travamento.

V3 `test-62b9e4368ba3406f94b427e93bc9d721` avançou normalmente: Toque e
Aterrorizar passaram; criação do esqueleto funcionou, mas reabrir ficou bloqueado.
V4 `test-0d56a8b5616a4549b8a39037e22d747e` substituiu a espera em ElementHandle
por Locator dinâmico e repetiu o FAIL, agora com diagnóstico explícito do DOM.
Assim, referência antiga de DOM não foi a causa comprovada desse bloqueio.

O defeito real era `canOperate`: depois de gastar a ação, o jogador perdia o
botão de consulta/reuso, embora o backend já permitisse recuperar sua invocação
sem novo custo. A disponibilidade desse card agora usa permissão da ficha,
busy e bloqueio da habilidade, não a janela de ataque. O backend continua
validando criação/turno/recurso; não concede ataque ou uso diário extra.

Novo teste avalia a expressão disabled do JSX real: RED para dono após ação
usada, GREEN após o patch; público/busy/bloqueio preservados. 21 testes frontend
focais PASS, sintaxe PASS. Build finalmente PASS em 15,24 s com heap de 384 MB;
artefato `index-BJC6UolP.js`, CSS `index-D7lSSoQI.css`. Nenhum backend reiniciado.

V5 foi solicitado ao OpenCode com os mesmos quatro atores, seis cenários e
três scripts. O conjunto ainda não é certificado até seu resultado terminal
e revisão das capturas. Os FAILs anteriores continuam preservados.

## Resultado terminal — lote focal aceito

V5 `test-a4ec4ba018e24bbb93530608a7150c5a` confirmou que reabrir a invocação
funciona com a correção, mas o fixture tentou GM_REPOSITION no cadáver depois
de iniciar o combate. O backend corretamente rejeitou. Preparação do corpo
movida para antes do start, com regressão RED/GREEN; não foi afrouxada a regra.

V6 `test-ceeb828d328f411bb24cb74904133a46`: **COMPLETED/PASS**, exit 0,
244,80 s. Cinco cenários API PASS e um EXPECTED_BLOCK (Clonagem sem componente
na cópia original). Três scripts UI PASS, seis usos efetivamente concluídos:

- Toque/Aterrorizar: 61,885 s. Toque acertou, dano 3 PV; custo, tick/ledger e
  reload conferidos. Aterrorizar executada, duração rolada 9; o alvo resistiu.
  Não se repetiu RNG para forçar efeito. Expiração por turnos coberta nas
  regressões backend; não foi exercitada visualmente nesse lançamento resistido.
- Invocações: 64,097 s. Esqueleto e Animar Mortos coexistem; reuso não duplica
  nem gasta novamente. Dispensa não reembolsa e reload não recria pin/cadáver.
- Magias maiores: 64,218 s. Clonagem consome um fragmento explicitamente
  fornecido só na fixture e um uso; dois clones de 25% dos PV surgem no próximo
  turno, persistem após reload e saem ao encerrar concentração. Magia da Morte
  confirma cancelamento/aviso inclusivo, seleção nativa, retry, custo e PV final
  1 a partir de 13. Sem conceder recurso operacional.

Capturas 390/1440 revisadas: cards, contadores, controle da criatura reanimada,
confirmações de alcance/consumo e aviso da Magia da Morte legíveis. O ensaio não
executa ataque de clone/invocação pela UI nem espera cinco rodadas de Clonagem;
não certifica esses caminhos, celular físico ou rede externa. O Mestre ainda
vê pins ocultos da fixture, portanto a captura não certifica limpeza visual
de todos os pins reais. `all_actions_certified:false` permanece correto.

Home local e pública retornaram 200 com `index-BJC6UolP.js`. Isso confirma
frontend servido, não mesa multirrede nem ativação do patch backend. Somente
o conector foi recarregado; backend operacional ainda aguardando autorização.

Checks gerais finais delegados ao OpenCode, sequenciais: discover nativo,
verificação dos pontos MCP no observer, frontend completo e typecheck. Resultados
abaixo; o código do jogo e o ambiente do SDK são verificados separadamente.
Arquivos adicionais desta continuação: `test_fixture_startup_checkpoints.py`,
`necromancy-smoke-contract.test.cjs`, `skeleton-reuse-card.test.cjs` e uma linha
do card em `SessionWorkspace.tsx`. Sem staging, commit ou push.

### Regressões finais executadas

- Discover nativo: 1.175 entradas, 614,375 s (622,58 s total). 1.172 PASS,
  dois erros `ModuleNotFoundError: mcp` e um skip. Exit 1: não declarar esse
  comando PASS. Os erros são `test_omnisvera_app` e contrato MCP do lote.
- Observer instalado, sem instalar dependências: 30 testes OK em 13,337 s
  (43,38 s total), incluindo ambos os erros e o contrato SDK pulado.
- Frontend completo sequencial: 348 PASS, sem falhas/skips, 105,689 s
  (110,08 s total), exit 0.
- Typecheck final: PASS, exit 0, 41,18 s. Build atual PASS, 15,24 s.
- `git diff --check`: PASS (avisos CRLF). Backend 8787 PID 253460 e OpenCode
  4096 PID 38768 preservados; sem listener de fixture em 8871 ao terminar.
