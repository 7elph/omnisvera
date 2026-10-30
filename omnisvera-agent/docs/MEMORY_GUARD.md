# Proteção local de memória

Substitui a automação por prompt `companion-prote-o-de-ram`, que está PAUSADA.
Não usa IA, MCP, navegador, polling WMI ou pacotes adicionais.

## Funcionamento

`backend/scripts/memory_guard.py` mede RAM física e memória comprometida pelas
APIs do Windows, a cada 30 segundos. Mantém apenas o estado atual e deltas em
`%LOCALAPPDATA%\Omnisvera\memory-guard\state.json`. Memória privada/comprometida
dos processos não é apresentada como se fosse toda residente em RAM.

A tarefa **OMNISVERA Memory Guard** inicia no login do usuário, sem janela e sem
elevação. Usa `IgnoreNew` e trava de arquivo: uma segunda execução sai sem criar
outro monitor. A medição operacional inicial foi aproximadamente **14,3 MB de
memória privada** para um processo `pythonw.exe` — valor observado, não limite.

O executor nativo das fichas verifica memória REAL antes do backup/servidor
(espera limitada a 120 s) e antes de cada script visual (até 30 s). Sem 1024 MB
livres ou se a medição falhar, não inicia essa etapa e retorna INCONCLUSIVE.
Os limites de 20 minutos por job e 300 s por script não foram aumentados.

## Controle preventivo de trabalhadores (continuação de 21/10)

`workload_slot` é uma trava de arquivo comum ao executor de fichas e a cada
`ai_workshop.tick`: somente um desses trabalhos pesados entra por vez. Se
ocupada, a oficina retorna `resource_busy` sem retirar proposta da fila nem
consumir tentativa; o ensaio sai antes de copiar o banco ou criar processos.
Chamadas internas do mesmo trabalho reutilizam a trava. Não é outro serviço.

No Windows, cada fixture e cada etapa visual nova possui um Job Object com
`KILL_ON_JOB_CLOSE`. Ao terminar, falhar ou perder seu controlador, seus filhos
e descendentes são encerrados pelo Windows. Isso inclui navegador deixado por
um driver já encerrado; não inclui aplicativos existentes ou o Companion real.
O Node aguarda um pipe privado antes de carregar o script; o Python real da
venv entra no grupo antes de importar a aplicação. Falha de vínculo impede a
etapa, em vez de executar um trabalhador sem contenção.

Essa prevenção complementa os recibos abaixo; não depende de o monitor
reconhecer depois um navegador órfão. Os limites de RAM e timeout continuam
iguais. Ela reduz desperdício dos trabalhos controlados, mas não promete
recuperar 1 GB quando a memória está ocupada por outros processos protegidos.
Novos ensaios carregam o código diretamente; a integração da oficina só entra
no backend operacional depois de sua próxima reinicialização validada.

A chamada de texto da oficina envia `keep_alive: 0` ao Ollama: se usar um
modelo local, solicita descarregá-lo ao concluir, sem requisição extra nem
processo de limpeza. Não muda o modelo escolhido, não transforma cloud em
local e não configura o Ollama globalmente. Timeout continua ambíguo: não há
alegação de cancelamento remoto nem retry oculto.
Referência: [API de geração Ollama](https://docs.ollama.com/api/generate).

## Recuperação por recibo

Somente filhos de ensaios MCP novos, registrados pelo executor em
`memory-owners/`, podem ser recuperados. É obrigatório ter job terminal com
horário final há pelo menos 60 s, registro dentro do período do job, lançador
original encerrado e correspondência de PID, criação e executável. A validação
e o encerramento usam o mesmo handle Windows, evitando troca por reuso de PID.

Não são encerrados processos apenas por nome, memória alta ou CPU ociosa.
Conectores antigos, aplicativos, Companion, OpenCode, Codex, túneis e serviços
não recebem registros de propriedade e não são alvos da limpeza. Processos
sem registro, descendentes não registrados e jobs sem prova terminal ficam
intactos. A limpeza é conservadora: pode deixar resíduos por falta de prova.

O monitor NÃO inicia testes, não balanceia regras, não esvazia caches/working
sets, não modifica pagefile/registro, não chama modelos e não garante 1 GB livre
se os aplicativos ativos precisarem de toda a memória. Não há alegação de que
as cópias antigas de conectores foram corrigidas ou eliminadas.

## Controle

Na pasta do Companion:

```powershell
.\memory_guard.ps1 -Action Status
.\memory_guard.ps1 -Action Check     # 0: pode iniciar; 2: falta margem
.\memory_guard.ps1 -Action Stop      # somente este monitor; até 30 s
.\memory_guard.ps1 -Action Install   # instalar/reativar a tarefa própria
.\memory_guard.ps1 -Action Uninstall
```

A remoção do agendamento preserva o registro local. O controlador recusa
sobrescrever uma tarefa homônima com outro executável ou argumentos.

## Validação inicial do monitor (21/10)

- 48 testes focados PASS: segurança/admissão, checkpoints do executor, lotes
  MCP e escolha de runtime. Os dois testes Windows usam somente filhos
  descartáveis criados pelo próprio teste, nunca processos operacionais.
- Confirmados na máquina: tarefa em execução, um único `pythonw.exe`,
  duplicação recusada e automação por prompt PAUSADA.
- O check real retornou `waiting_for_memory`/código 2 com 51 MB livres; nenhum
  ensaio pesado foi lançado. Nenhuma limpeza operacional ocorreu por falta de
  recibos antigos verificáveis; não confundir teste de segurança com RAM liberada.
- Suíte backend integral, typecheck e build não executados neste corte por
  falta da margem de RAM. Nenhum frontend ou endpoint de combate foi alterado.
  Sem restart do Companion/OpenCode, staging, commit ou push.

Referências de API: [GetProcessMemoryInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getprocessmemoryinfo),
[GetPerformanceInfo](https://learn.microsoft.com/en-us/windows/win32/api/psapi/nf-psapi-getperformanceinfo)
e [IgnoreNew](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset).

## Validação do controle preventivo (continuação de 21/10)

- **128 testes focados PASS**, em 21,818 s, no observer já instalado: monitor,
  admissão, trava entre processos/threads, oficina/adaptadores, executor e
  evidências. Incluem filhos Windows descartáveis reais: vínculo do Python
  da venv, gate do Node e encerramento do trabalhador e seu descendente,
  preservando o controlador. A opção Ollama falhou em RED antes do patch.
- Não foi iniciado modelo real para testar descarregamento; o teste verifica
  o contrato HTTP com cliente controlado. Nenhuma RAM fictícia é contabilizada.
- Suíte backend integral: **1240 testes, OK, 1 ignorado**, em 661,450 s.
  Os 128 focados incluem as últimas regressões de trava entre processos e
  opção Ollama, adicionadas após a coleta da suíte integral. Contagens se
  sobrepõem; não devem ser somadas como testes distintos. Avisos legados de
  conexões SQLite não fechadas continuam presentes. UI real ainda não executada.
  As últimas medições durante os checks ficaram abaixo de 1024 MB; não foi
  reduzida a margem nem iniciado navegador para contornar a proteção.
- Alterações adicionais: `memory_guard.py`, `run_sheet_test.py`, bootstraps
  `cf01_probe.py`/`all_actions_simulation.py`, `ai_workshop.py`,
  `ai_workshop_adapters.py`, `frontend/tests/owned-ui-preload.cjs`, testes
  `test_workload_control.py`, `test_fixture_startup_checkpoints.py`,
  `test_sheet_runner_batches.py` e `test_ai_workshop_adapters.py`.
- Frontend sequencial: **358 testes PASS**. `npx --no-install tsc --noEmit`
  e `npm run build` PASS; build em 14,74 s, com aviso de bundles acima de
  500 kB. `git diff --check` dos caminhos deste corte PASS.
- Após os checks: **293 MB físicos disponíveis / 8105 MB totais**, 13335 MB
  comprometidos. Não foi recuperada a margem de 1024 MB e não foi iniciado
  ensaio visual pesado. A tarefa do monitor permanece Running. Não atribuir
  toda a memória não explicada ao Defender nem confundir commit com RAM.
- Sem reiniciar Windows, Companion ou OpenCode nesta continuação; integração
  da oficina no processo operacional ainda não ativada. Sem staging/commit/push.

Job Objects: [documentação Microsoft](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects).

## Diagnóstico da memória não atribuída (21/10, continuação)

Foi coletado snapshot finito com RAMMap64 oficial, assinatura Microsoft
validada; exportação privada somente em TEMP. O processo de diagnóstico saiu
ao concluir. A lista física contém aproximadamente 57 mil registros de
processos, incluindo 29.357 `git.exe` e 22.438 `conhost.exe`, apesar de não
existirem milhares desses processos ativos na enumeração normal. Isso é
compatível com objetos de processos encerrados ainda retidos, não 57 mil apps
que devam receber taskkill. A categoria de tabelas de páginas soma cerca de
2.137 MB no snapshot. O contador WMI de memória residente de drivers retornou
um valor impossível para 8 GB e não é usado para atribuir consumo real.

O PID 2372, iniciado em 13/10, apresentou 57.477 handles e hospeda somente
`PcaSvc` (Auxiliar de Compatibilidade de Programas), em modo Manual e parável.
Isso aponta um proprietário concreto a investigar, sem culpar o Defender ou
os atuais processos do Codex pela memória física inteira. Uma varredura Git
observada é lançada pelo aplicativo, mas seu vínculo com os objetos retidos
não foi inferido como prova de bug do Codex.

Foi preparada em TEMP uma recuperação administrativa única via SCM: validar
PID/criação/serviço exclusivo/dependentes, parar e iniciar somente PcaSvc e
registrar RAM e handles antes/depois, sem alterar tipo de início. Não utiliza
taskkill nem encerra svchost genérico, aplicativos, Defender ou outros serviços.
Enquanto a confirmação local do Windows estiver pendente, nenhuma recuperação
é considerada executada. A autorização no chat não altera o token do Windows.

Tentativa efetiva posterior, sem presumir privilégios: o SCM negou abrir/parar
PcaSvc com o token atual (`administrator=false`); recibo privado registra
`changed=false`, `completed=false`, 57.477 handles e 347 MB livres antes.
As tentativas RunAs retornaram operação cancelada/expirada, não concessão de
administração. Nenhum serviço foi parado nem a meta de 1 GB foi confirmada.
É indispensável confirmação/autenticação local do Windows; não se tenta
contornar UAC ou permissões por tarefas agendadas, credenciais ou serviços.

Ativação posterior do Companion (21/10, 18:59): a restrição administrativa de
PcaSvc NÃO impedia controlar o backend do próprio usuário. O worker foi
substituído com backup e ambiente preservado, novo PID 252096. A integração
da trava da oficina e a opção Ollama estão carregadas; não foi executado
modelo nem navegador para provar liberação de memória. A meta de 1 GB segue
não comprovada. Ver `PASSIVES_SUMMON_TURNS_2026-10-21.md` para preservação e HTTP.
