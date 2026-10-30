# Passivas e turnos das invocações — 21/10

## Correção reproduzida

Clones eram excluídos dos pins ao perder concentração, expirar cinco rodadas ou
chegar a 0 PV, mas permaneciam na iniciativa: o ciclo ignorava tokens sem linha de
PV. Três regressões falharam antes do patch e passaram depois.

`battle_mode.retire_defeated` agora retira também participantes-token cujo pin
deixou de existir. `morthak_high_spells.cleanup` chama esse mesmo mecanismo após
excluir clones. Não há outro motor de turnos. A remoção preserva o participante
atual e o orçamento, ou avança e limpa o orçamento quando o próprio atual saiu.
O ledger não apresenta um clone dispensado como morto a 0 PV.

Uma quarta regressão HTTP cobre clone controlado: outro jogador é rejeitado,
confirmação repetida não duplica ataque, segundo ataque é bloqueado e passar
turno repetidamente com o mesmo recibo não pula outro participante.
Uma quinta cobre o último clone da iniciativa morrendo: fecha a rodada uma vez,
preservando o outro clone e entregando o turno ao sucessor correto.

## Verificações concluídas

- Backend nativo: 79 testes relacionados de hemomancia, magias altas de Morthak,
  invocações da Sessão 6 e battle mode; mais duas regressões novas: 81 PASS.
- Frontend: 354 testes PASS, executados sequencialmente. A primeira tentativa
  teve bloqueios de leitura do esbuild pelo sandbox; a repetição autorizada,
  fora dessa restrição, passou. Não foi necessário alterar produto por isso.
- Contrato dos lotes MCP e leitor de evidências: RED para lotes desconhecidos;
  após registro e revisão, 35 testes PASS no observer existente.

## Ensaio visual em preparação

O OpenCode recebeu a autoria dos scripts de gatilhos das cinco passivas de
Raziel e ataques/turnos de esqueleto, reanimado e clones. Os lotes fixos
`passives` e `summon_turns` exigem os quatro atores, `ui:true`, fixture TEMP e
os mesmos limites do executor. Não alteram o `full`.

O Mestre autorizou e foi recarregado somente `companion-tests`. Nenhum backend,
OpenCode ou túnel operacional foi reiniciado; fichas reais não foram alteradas.
Os scripts delegados ainda não haviam sido entregues no momento deste registro;
não tratar os nomes registrados nos lotes como evidência de execução.

O navegador ainda não foi executado neste corte: RAM livre medida entre 185 e
241 MB, insuficiente para iniciar ensaio pesado com segurança. Portanto a prova
visual deste lote, build/typecheck atuais e regressão backend completa NÃO estão
certificados. Resultado de API não substitui revisão das capturas; multicliente
em loopback também não prova mesa real em redes distintas.

## Ativação e limites

Correção de produto está no disco, não ativada no backend operacional por esta
etapa. Não houve staging, commit ou push. O worktree misto preexistente foi
preservado. Nenhuma regra de passiva, duração, custo ou recurso foi rebalanceada.

## Arquivos deste corte

- Produto: `backend/app/battle_mode.py`, `backend/app/morthak_high_spells.py`.
- Regressões: `backend/test_morthak_high_spells.py`.
- Executor/contratos: `backend/scripts/run_sheet_test.py`,
  `backend/scripts/agent_test_jobs.py`, `backend/scripts/companion_test_mcp.py`,
  `backend/app/test_run_evidence.py`, `backend/test_sheet_runner_batches.py`,
  `backend/test_test_run_evidence.py`.
- Documentação: este registro, `AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md`.

Vários desses arquivos já eram modificados/não rastreados antes da etapa; a
lista não atribui o conteúdo integral deles a este corte. Sem staging automático.

## Continuação: revisão leve e compatibilidade (21/10)

Os dois scripts foram entregues, mas a revisão encontrou autenticação de jogador
incorreta, crítico do arco esperando três dados em vez de dois, rolagem recebida
não controlada e possíveis corridas/seletores. A correção dos dois scripts foi
delegada ao OpenCode, sem autorização para abrir navegador ou alterar produto.
Essa entrega ainda NÃO constitui PASS de UI.

Dois testes RED adicionais reproduziram turnos de clones desaparecidos no
combate de iniciativa legado, sem `battle_mode`. O mesmo `retire_defeated` agora
remove pins ausentes nas duas interfaces. O comportamento legado para criaturas
existentes a 0 PV não foi ampliado. O orçamento do participante atual é mantido;
se o clone removido era o atual, avança uma vez e limpa apenas esse orçamento.
Um ensaio SQLite em memória confirma a limpeza real de Clonagem por 0 PV e por
fim de concentração nas duas interfaces, inclusive repetição sem novo avanço.

O leitor de resultados do executor também foi corrigido: aceita o JSON terminal
formatado em múltiplas linhas, preserva sua cobertura e distingue INCONCLUSIVE
explícito/código 2 de falha de asserção. Um processo que falhou não publica PASS
nem cobertura; FAIL declarado interrompe o lote mesmo com saída zero acidental.

Validação desta continuação: **30 testes leves PASS**, sem processos de fixture
ou navegador, pelo observer existente:

```powershell
cd backend
..\.venv-observer\Scripts\python.exe -m unittest test_summon_retirement_compatibility test_visual_result_receipts test_sheet_runner_batches.VisualBatchTests
```

Arquivos adicionais: `backend/test_summon_retirement_compatibility.py` e
`backend/test_visual_result_receipts.py`; alterações locais em `battle_mode.py`,
`run_sheet_test.py`, `test_sheet_runner_batches.py` e documentação.
Frontend leve: três regressões de contrato em
`node --test tests/necromancy-smoke-contract.test.cjs` PASS; `node --check`
nos dois novos scripts também PASS. Sintaxe não comprova execução visual.
Outro achado foi encaminhado ao OpenCode: as chaves de cobertura precisam
corresponder ao inventário nativo (`ability:hemomancia-passiva-*` e
`ability:clonagem`, por exemplo), sem criar chaves `passive:*`/`summon:*` que o
leitor não consegue relacionar às fichas. Revisão delegada ainda em andamento.
Backend integral, build/typecheck e novo ensaio visual continuam pendentes por
falta de RAM. Nenhum serviço operacional reiniciado, ficha alterada, staging,
commit ou push nesta continuação. As correções permanecem em disco, não ativadas.

## Revisão final dos scripts e redução de processos (21/10)

OpenCode gravou as revisões dos dois scripts: credencial vinculada ao ator real,
chaves `ability:*` do inventário, cobertura de UI sem atribuir checks de backend,
crítico do arco com dois dados base, filtro `hemomancy_kind`, espera de respostas
armada antes do clique e preparação do cadáver antes de iniciar combate.
A delegação foi interrompida pelo Codex após esses arquivos estarem salvos,
para encerrar o trabalhador extra e recuperar recursos; não é conclusão visual.

O Codex corrigiu ainda a calibração de Revanche: ler a CA efetiva após o escudo,
comparar com CA anterior +2 e escolher um d20 que acertaria sem o escudo, mas
erraria por margem 1–2 com ele. Nunca usar 1/20 natural como falsa prova do
gatilho. Helper de fixture `frontend/tests/shield-near-miss.cjs` com quatro
regressões em `shield-near-miss.test.cjs`; nenhuma regra do jogo foi alterada.

Checks atuais: **80 testes relacionados de backend PASS** (hemomancia, magias
altas, recompensas/invocações, battle mode e compatibilidade da iniciativa),
em 66,467 s. Houve `ResourceWarning` de conexões SQLite não fechadas em fixtures
antigas; não são omitidos nem corrigidos por refatoração neste corte.
**7 testes leves de frontend PASS**, além de `node --check` dos dois scripts.
Não equivalem a UI executada nem a toda a suíte do Companion.

Com autorização do usuário para fechar aplicativos sem uso: Ollama sem modelos
ou conexões, Vincular ao Celular, Configurações e a árvore específica de pesquisa
web do Windows foram encerrados. A própria tarefa delegada foi abortada pela
API do OpenCode; a instância Companion foi descartada pela API para fechar seus
conectores e o servidor OpenCode foi encerrado por identidade/PID verificados.
Em seguida 9router foi encerrado, sem clientes e já sem o OpenCode dependente.
Sessão/arquivos do OpenCode permanecem em disco. Ele NÃO continua trabalhando
em segundo plano. Não houve alteração de modelo, configurações ou credenciais.

Memória comprometida caiu de aproximadamente 16,5 GB para 13,4 GB; RAM física
disponível oscilou entre 353 e 666 MB após a limpeza. São medidas distintas,
não uma alegação de ter recuperado 3 GB de RAM física. Codex, Companion, túnel
e Defender preservados. Sem reiniciar Windows/Companion, staging, commit ou push.
O monitor em código permanece conservador, sem nova autorização automática
para encerrar aplicativos ou serviços; esta limpeza foi manual e específica.

Após uma espera única e limitada a 120 s, o gate ainda registrou **573 MB livres**
e 13.336 MB comprometidos. Nenhum navegador/ensaio pesado foi iniciado nem o
limite de 1.024 MB foi reduzido. Backend operacional conserva PID 253068 e
inicialização de 20/10; a rota protegida respondeu 401 sem credencial (não é
health autenticado nem certificação funcional). Não foi reiniciado o Windows.

## Controle preventivo e regressão integral (continuação)

Sem reboot, foram implementados os controles de `MEMORY_GUARD.md`: trava entre
ensaios/oficina, grupos Windows para fixture e cada driver/navegador, gate antes
do script visual e bootstrap do Python da venv. A oficina pede `keep_alive: 0`
no Ollama sem alterar seu modelo. Isso gerencia trabalhos próprios; não encerra
aplicativos existentes nem garante 1 GB disponível.

Checks executados nesta continuação:

- Backend integral: **1240 testes, OK, 1 ignorado**, 661,450 s; avisos legados
  de conexões SQLite não fechadas permanecem.
- Controle de recursos/adaptadores/executor: **128 testes focados PASS**,
  incluindo filhos Windows reais descartáveis. Contagem sobrepõe a integral;
  as últimas duas regressões foram adicionadas após a coleta integral.
- Frontend: **358 testes PASS**, em sequência, 117,734 s.
- Typecheck e build PASS; build em 14,74 s com aviso de chunks grandes.
  `git diff --check` dos caminhos deste corte PASS.
- `/health` autenticado como Mestre: **HTTP 200**, `backend=ok`; `/workspace`
  também HTTP 200. Não é prova de publicação do código novo nem de multicliente.

Ainda sem ensaio visual novo ou ativação operacional nesta continuação.
Após os checks, RAM física disponível em **293 MB**; não foi iniciada outra
espera repetitiva ou navegador abaixo do gate de 1024 MB.
OpenCode continua desligado; não afirmar que a delegação segue trabalhando.
Fichas reais não foram usadas como alvo de ensaio. Sem staging, commit ou push.

## Ativação operacional — 21/10, 18:59

O backend foi reiniciado remotamente, sem administrador e sem reiniciar
Windows, Chrome Remote Desktop, Codex, Tailscale ou outros serviços. Novo
worker **PID 252096**, lançador **249056**. Backup SQLite consistente e cópias
dos arquivos de acesso/configuração em
`backend/data/backups/pre-passives-activation-20261021-185915/`, fora de commits.

A configuração foi capturada somente do processo Companion identificado e
repassada em memória ao substituto; não foi impressa nem gravada como dump.
Não houve geração/rotação de tokens, pip install ou reconstrução do Vault.
A inspeção anterior confirmou banco correto, tokens coincidentes e combate
inativo; o comando original e o ambiente foram mantidos.

Comparação de 78 tabelas antes/depois: nenhum registro de ficha, inventário,
sessão, combate, token, posição ou fog perdido/modificado. Diferenças restritas
a `updated_at` dos mapas oficiais Nimalia/Earthropo e ao contador técnico
`sqlite_sequence.session_ledger`; os registros do ledger permaneceram iguais.
Nenhuma tabela/mapa foi adicionada ou removida. Arquivo de tokens idêntico e
configuração de modelos, banco, Vault e RAG preservada.

Após a ativação, pelo endereço público: health/characters/companions GM e
Morthak/Vezemir/Raziel com seus tokens próprios, todos **HTTP 200**. Fichas em
0,14/0,17/0,31 s nesta amostra; não é medição de estabilidade/endurance.
Antes do restart, HTML, JavaScript e CSS públicos também retornaram 200.

As correções de aposentadoria de clones/turnos e o controle da oficina estão
agora carregados no runtime. Os ensaios visuais novos de passivas/invocações
continuam pendentes: API disponível não comprova clique, interface ou mesa real.
O problema relatado de controle da área de trabalho remota é separado: o
serviço chromoting estava Running e registrou conexões/desconexões recentes;
isso não certifica captura de entrada. Sem novos pedidos UAC nesta ativação.

## Continuação — controles de invocação e criaturas

Dois defeitos reproduzidos com testes RED antes da correção:

- O botão de passar turno de uma invocação enviava outro comando após o
  primeiro ser aceito, enquanto a tela ainda mostrava a versão antiga.
  `SummonControls` agora bloqueia novo envio e ataques dessa tela até receber
  outra versão. Uma falha de leitura após confirmação mostra espera de
  sincronização, não falha da ação; resposta perdida do comando conserva o
  request ID para retry. Sem alteração do ciclo de turnos no backend.
- Magias/habilidades de criaturas no grid enviavam d20 físico vazio, e o
  seletor do grimório ficava desabilitado sem um campo visível para esse dado.
  `MonsterAttackPanel` agora segue a rolagem digital já usada nos ataques
  confirmados pelo grid. Fora do grid, o dado físico permanece preservado.

Checks desta continuação: **37 testes focados PASS**, **363 testes frontend
PASS** (90,568 s), typecheck PASS, build PASS (12,66 s, aviso já existente de
chunks acima de 500 kB), diff --check dos arquivos tocados PASS. Backend não
alterado nem novamente ensaiado neste corte; a coleta integral anterior está
registrada acima. Cobertura nova em `summon-controls.test.cjs` e
`combat-controls.test.cjs`, incluindo resposta perdida, confirmação seguida
de refresh falho, bloqueio enquanto desatualizado e liberação na nova versão.

Publicação conferida por GET no endereço público: HTML e
`/assets/index-CeP4CPHg.js` HTTP 200, SHA-256 do JavaScript servido idêntico ao
arquivo buildado. Backend permaneceu PID 252096; não precisou de restart para
servir o frontend. Sem comandos em fichas reais, staging, commit ou push.

Ensaio visual novo de passivas/turnos continua **INCONCLUSIVE**: última medição
de 440 MB livres, abaixo do gate de 1024 MB. Nenhum navegador de teste foi
iniciado. Testes de componentes e entrega do bundle não certificam cliques no
celular nem mesa com clientes em redes diferentes. OpenCode não foi iniciado.

## Continuação — respostas atrasadas após ações

Três regressões RED reproduziram o painel voltando para uma versão antiga do
combate: leitura após ação da invocação, após edição de efeitos e recuperação
de conflito 409. A proteção de versão já existente no polling não cobria essas
três leituras. `CombatEncounterPanel.tsx` agora preserva o estado mais recente
também nesses caminhos; a atualização externa continua sendo chamada. Não há
reenvio automático de comandos ou alteração do backend/turnos/regras.

Cobertura adicionada em `frontend/tests/combat-sync-recovery.test.cjs`:
resposta atrasada não substitui turno mais novo, e uma resposta realmente nova
continua sendo aplicada. **45 testes focados frontend PASS**, depois
**366 testes frontend PASS** (85,110 s), typecheck PASS e build PASS (10,12 s).
Permanece o aviso de chunks acima de 500 kB.

Regressão backend somente em bancos temporários: **64 testes PASS**, 40,219 s,
nos módulos `test_hemomancy_weapons`, `test_morthak_high_spells` e
`test_summon_retirement_compatibility`. A integral não foi repetida neste corte
somente de frontend. Permanecem avisos legados de SQLite não fechado e de
depreciação do TestClient; não foram suprimidos nem apresentados como corrigidos.

HTML e `/assets/index-D50vlsSI.js` públicos HTTP 200; SHA-256 do bundle servido
igual ao build local. Sem restart, comandos nas fichas reais, staging, commit
ou push. Alterações anteriores preservadas. O lote visual não foi executado:
322 MB livres na verificação inicial, sem reduzir o gate de 1024 MB. Não há
aceitação visual nova nem comprovação de mesa em redes distintas.
