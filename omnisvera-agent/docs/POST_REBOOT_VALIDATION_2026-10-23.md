# Validação após reinício — 23/10/2026

## Estado e isolamento

Validação ainda em andamento; não é certificação completa das fichas.
Branch `devin/create-omnisvera-class-standard`, HEAD inicial `1a07a84`.
O usuário reiniciou o notebook. Foram observados 871 MB livres inicialmente,
depois 1827, 2116 e 3851 MB. Não atribuir essa variação a limpeza pelo agente:
nenhum aplicativo/serviço foi encerrado para liberar memória nesta retomada.
Ollama respondeu com zero modelos carregados. Não foi iniciado modelo local.

Os encaminhamentos Tailscale estavam ativos, mas não havia servidor local em
8787 ou 4096 após o boot. Após autorização explícita, ambos foram religados:
OpenCode autenticado 200/healthy e Companion autenticado 200, inclusive pelo
endereço público habitual. Perfis de Morthak, Vezemir e Raziel: leitura 200.
Sem reinstalação, troca de credenciais ou chamada de modelo.
Backup SQLite consistente em TEMP antes da inicialização. Das 11 tabelas
protegidas comparadas, apenas `updated_at` dos mapas oficiais Earthropo e
Nimalia mudou pela inicialização existente; nenhum conteúdo/posição mudou.
Arquivo de tokens idêntico. Os ensaios não dependem desses serviços.

Todos os comandos de jogo dos ensaios usam 8871, banco/vault TEMP e tokens
CF-01. O banco operacional só é lido para backup e diagnóstico. Não houve
compra, descanso, estoque, fichas, sessões ou combate reais alterados.

## Correções localizadas

- Executor: cenários API eram irmãos do servidor mas herdavam o nome do
  Job Object dele. A associação falhava com WinError 5. O trabalhador API
  agora tem grupo próprio, vínculo pelo handle original e encerramento
  garantido. Não foram removidos proteção, limites ou requisito de RAM.
- Vezemir: a poção real `session-item:11` tem quantidade zero. O ensaio
  não pode presumir estoque. Agora verifica rejeição nativa repetida sem
  mutação, sem repor item e sem declarar cura/custo positivos executados.
  O ID estável do cenário foi preservado; não se concede cobertura de consumo.
- Cenas: a prévia tinha apenas max-height e crescia até esse limite ao
  ampliar. Altura responsiva fixa preserva viewport e rolagem interna.
- Ataque de monstro: o filtro de participantes descartava pins de personagens.
  O grid enviava o ID do pin como ID de ficha e retornava 404. O filtro agora
  conserva pins dos personagens participantes; personagens/NPCs externos
  continuam excluídos. Backend continua resolvendo pin para ficha nativamente.
- Após ataque de monstro, atualizar o snapshot autoritativo de combate antes
  do próximo comando, sem retry automático ou rewind por resposta atrasada.
- O ensaio integrado revelou uma segunda defasagem: o card de combate
  mantinha um snapshot próprio após a ficha confirmar o escudo. Agora recebe
  também o snapshot nativo do pai, com proteção de versão. Dois testes RED
  antes da correção passaram depois; não se repete comando de turno sozinho.
  Smokes observam a versão no card e a indicação de ação concluída, não só
  a conclusão HTTP, antes de enviar o próximo comando.
- Invocação: a célula à direita podia estar ocupada, sobrepondo o alvo com o
  novo pin. Reutilizada a busca de células livres dos clones; sem espaço
  adjacente, rejeita atomicamente sem gastar uso ou criar token.
- Ensaios visuais: atualizados para o clique no card, alvo no grid e card
  de combate atual, sem reintroduzir controles legados. Após reload do jogador,
  abrir Ficha antes de procurar carteira (a aba inicial é Sessão).

## Evidências já coletadas

- `test-00428a6923e24a14b3dfdf24b7a5dd49`: erro de contenção antes da API.
- `test-07837b4645314ee7b2a569489581c63a`: 91 cenários API,
  **87 PASS, 3 EXPECTED_BLOCK, 1 FAIL** (suposição da poção sem estoque).
  Interface não executada nesse recibo; não apagar/reclassificar o FAIL.
- Retestes seletivos preservam o ID observado: poção esgotada rejeitada
  nativamente, EXPECTED_BLOCK, sem mutação/restock; não é cura executada.
- Cenas: seis blocos, desktop 1440 e celular 390, imagens, diálogo,
  zoom delimitado e filtro público passaram; duas screenshots inspecionadas.
- Loja de Thoradin copiada: cancelamento, compra pela UI, carteira 105 PO /
  25 PP → 105 PO / 20 PP, estoque em segunda página local, retry e reload
  passaram. Capturas da loja e carteira inspecionadas; não é rede externa.
- Dois blocos visuais: dez ações de Vezemir/Morthak/Dorn passaram. Capturas
  de Morthak, Vezemir e Dorn em desktop/celular foram inspecionadas.
- Passivas: `test-47370cf0b11d49c6855a3fd4c77b31e6` passou nos cinco gatilhos,
  incluindo Revanche (CA +2, carga e consumo único no próximo ataque).
  Quatro screenshots desktop/celular inspecionadas. Não exercitou o caso
  simultâneo Exposto + sangramento de Ferroada; d20 controlado no transporte,
  não é prova de digitação física pela UI.
- Invocações: `test-a962694c2d4c4ff7bbd3217cbc48dfd4` passou: esqueleto,
  reanimado e clones; ataque pelo card/grid, turno do dono, bloqueio fora do
  turno, ausência de controles para outro jogador participante, dispensa sem
  reembolso, remoção ao chegar a zero PV/encerrar concentração e expiração.
  Capturas 390/1440 inspecionadas. Componentes consumíveis foram preparados
  somente na fixture; não repõe componentes operacionais.
  O teste foi corrigido para esperar o estado de ação concluída na UI e
  contar cinco rodadas ativas depois da rodada de execução da Clonagem.
  Não foram alteradas duração nem privacidade para fazê-lo passar.
- Descanso: `test-5a6f87aa9e5c4f9c9e48a1f4306c08f1` passou nos dois scripts:
  zoom horizontal/delimitado, arrasto mouse/toque e reload; descanso pela UI,
  PV restaurados, PV temporários/condições/efeitos limpos, contadores diários
  restaurados nas quatro fichas em 1440/390. Quantidades de inventário e
  efeito independente de NPC preservados. Jogador sem comando de descanso
  geral. Capturas de mapa, Status, PV e fichas inspecionadas.
- Integrado `test-91506de600354bf1aca7597ee2b0d4fa`: API **87 PASS e
  4 EXPECTED_BLOCK**, 91 cenários. Quatro blocos visuais passaram; passivas
  falharam ao passar turno logo depois do escudo. Recibo permanece FAIL.
  Após correção de sincronização frontend, repetição dos sete blocos visuais
  usa seleção API focal; não fingir que esse novo job reexecuta os 91 casos.
  Backend permaneceu igual entre essas execuções.
- Bloqueios de disponibilidade: Vezemir/Morthak sem arma no ataque ranged
  genérico; poção de Vezemir sem estoque; Clonagem sem fragmento na ficha
  copiada. Ensaio visual prepara fragmentos só em TEMP. Não houve reposição
  operacional. Bloqueio correto não é uma execução positiva de habilidade.

## Checks e limites

82 regressões backend focadas passaram após correção de contenção; incluem
um teste Windows real de grupos irmãos e preservação do servidor descartável.
23 testes de relatório/isolamento passaram após ajuste da poção.
18 testes de Cenas e 14 focados de combate/contratos frontend passaram.
Typecheck e build passaram (mantido aviso legado de bundles acima de 500 kB).
Essas contagens são etapas sobrepostas, não uma soma da suíte completa.

54 testes backend de invocações/clones passaram após correção de célula.
Uma tentativa anterior incluiu nome de módulo inexistente; execução corrigida
passou, sem tratar o erro de importação como defeito do Companion.

Regressão integral atual: backend **1259 testes, OK (1 skipped)**; frontend
**394 PASS / 0 FAIL**, typecheck e build PASS. O aviso legado de bundles
acima de 500 kB permanece. Artefatos JS/CSS: `index-CDOZL_75.js` e
`index-DXHYIG6g.css`. Sem reinstalação de dependências.

Após a última correção frontend, JS atualizado para `index-DlfD5M10.js`;
CSS preservado. A publicação estática usa o servidor existente, sem novo
restart de backend ou alteração de estado de jogo.

Reteste `test-d3d1bba64d1f45e4b99dcfc9929b6474`: **COMPLETED/PASS**,
`report.ui_smoke.status=PASS`, os sete scripts de sexta passaram em sequência
na mesma fixture. API focal: uma rejeição prevista de poção esgotada; os 91
cenários completos continuam comprovados separadamente no recibo anterior.
Capturas atuais da galeria 1440/390, loja/carteira, Revanche, controles de
esqueleto/reanimado/clone, Status e ficha descansada foram inspecionadas.
Aceitação visual do agente limitada a esses recortes; o campo automático
`pending_human_or_agent_image_review` dos smokes não foi adulterado.

Verificação final: Companion público autenticado 200, artefato novo servido,
OpenCode autenticado 200/healthy. Medição finita após encerrar o ensaio:
**2870 MB de RAM física livres**, total 8105 MB; comprometida 9166/16210 MB.
Não é garantia permanente de RAM, nem resultado de encerramento de aplicativos.

`certification_ready=false`: não é certificação de todas as ações, mídia ou
mesa em redes distintas. Ferroada com Exposto + sangramento simultâneos e
digitação física de d20 não foram comprovados nesses scripts. A fixture não
contém toda a mídia da campanha. Poção/fragmento reais continuam sem reposição.
Sem staging, commit ou push. Worktree misto anterior preservado.

## Arquivos tocados neste fechamento

- Backend: `app/summons.py`, `scripts/run_sheet_test.py`,
  `scripts/all_actions_simulation.py`; regressões em
  `test_scenario_worker_containment.py`, `test_fixture_startup_checkpoints.py`,
  `test_sheet_rehearsal.py`, `test_summon_spawn_cells.py`.
- Frontend: `src/components/CombatEncounterPanel.tsx`,
  `src/components/scenePreparation.css`, `src/pages/SessionWorkspace.tsx`;
  testes `scene-preparation.test.cjs`,
  `combat-sync-recovery.test.cjs`, `friday-readiness.test.cjs` e smokes
  `thoradin-wallet`, `hemomancy-passives`, `summon-turns`.
- Este documento. Operadores privados de execução/inicialização ficam no
  diretório ignorado `.autonomy/runtime`; backup e recibos ficam em TEMP.
  A lista indica arquivos tocados, não autoria exclusiva dos seus diffs:
  alterações anteriores de outras tarefas continuam preservadas.
