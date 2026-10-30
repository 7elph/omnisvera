# Fechamento do runner de combate — 16/10

## Causa verificada

O job do OpenCode `test-e28e1d9e5eb24ac2b885dc3d603676ce` chegou ao limite de
20 minutos. Os artefatos privados mostram **79 PASS + 3 EXPECTED_BLOCK** na API
em cerca de 11,5 minutos. Apenas dois dos 12 scripts visuais terminaram antes
do timeout. O relatório existia, mas o adapter não o entregava em ERROR.
Isso não certificou UI nem representou 82 habilidades quebradas.

## Alterações, sem mudar regras do Companion

- `ui_suite=full` continua padrão e preserva os 12 scripts. O novo lote explícito
  `combat` exige quatro atores + `ui:true` e executa readiness das fichas e o
  smoke de dez ativações das três fichas, sem incluir lojas/mapas. IDs seletivos
  de API vêm de relatório anterior, não de nomes inventados pelo agente.
- O limite global de 20 minutos permanece. Cada script tem duração medida,
  checkpoint e prazo próprio; timeout para somente a árvore criada pelo runner.
  Filtros locais de debug não podem estreitar silenciosamente a cobertura pedida.
- `status.progress` localiza fase/cenário/script. `partial_report` retém provas
  válidas em ERROR/CANCELLED/INTERRUPTED, sem virar resultado conclusivo,
  reativar o job antigo ou conceder certificação. Contagens inválidas são rejeitadas.
- Uma falha de API seguida de UI não executada agora continua **COMPLETED/FAIL**,
  não é escondida como erro de infraestrutura. Dois testes RED reproduziram esse
  segundo defeito antes da correção de prioridade de exit code e validação.
- Os quatro testes frontend estáticos do OpenCode foram renomeados para
  `opencode-three-sheets-gaps.test.cjs`, entrando na descoberta padrão. Não são
  prova de execução visual de habilidades.

## Provas mecânicas adicionais em fixtures nativas

- Toque Sombrio: tick só no turno do alvo; 1–3 perde PV, 4–6 não; retry não
  repete rolagem/perda; fim de combate limpa; tick letal remove efeito e pula
  o participante morto. RNG controlado apenas no teste unitário.
- Clonagem: encerramento de concentração com retry remove clones sem outro
  fragmento/uso. O fragmento é o da fixture existente, não foi entregue na campanha.
- Invocações: coexistência esqueleto/zumbi e dispensa idempotente de um sem
  remover o outro nem devolver recursos.
- Runner HTTP de Guarda ampliado para grid, ataque redirecionado e expiração
  natural de uma segunda Guarda que não foi consumida por interposição.
- Runner HTTP de Teia ampliado para passo no grid com custo triplo e retry
  sem repetir gasto. Reflexos passa também pelo card real no lote visual.

O primeiro teste do runner novo falhou por faltar `position_confirmed` no
payload de Guarda; o segundo ainda não informava `ally_token_id`. São erros
do ensaio ao adaptar o caminho legado, corrigidos para enviar o mesmo contrato
do frontend. Resultados FAIL e cópias TEMP dessas tentativas foram preservados.
Não foram alteradas regras, rotas ou cálculos do produto para fazer testes passarem.

Na terceira tentativa, os dez cenários de API concluíram (9 PASS e um bloqueio
esperado), mas o smoke visual esperava grid/diálogo para Reflexos. O fluxo real
é aplicação direta no próprio Dorn; o teste foi corrigido para esse contrato,
mantendo a verificação de efeito, um único POST, custo e reload. O FAIL visual
anterior foi preservado, não reclassificado.

## Execução e limites

Tentativa de executar o MCP atualizado: **BUSY**, outro host detinha a lease.
Nenhuma trava foi apagada nem processo desconhecido encerrado. Com autorização
do Mestre, somente `companion-tests` foi desconectado/reconectado pela API local
autenticada do OpenCode; ambas as operações retornaram `true` e o status final
foi `connected`. Companion, túnel e modelo não foram reiniciados ou alterados.
O mesmo runner nativo foi usado diretamente na porta isolada 8871, livre e sem job RUNNING
registrado; isso não será apresentado como PASS do transporte MCP.

As cópias SQLite/vault, logs e capturas ficam apenas em
`%TEMP%/omni-runner-validation-*/`. Fonte operacional só é aberta para backup
somente leitura. Nenhum ataque, magia, descanso, compra ou teste ocorreu na mesa.
Mídia ausente no vault temporário não certifica defeito na mídia operacional.

Aceitação visual parcial: inspecionadas as capturas do lote final de readiness,
Morthak Mestre desktop e jogador 390 px, Vezemir 360 px, Raziel e Dorn 390 px.
Os grupos, contadores e controles ficam contidos nas fichas, sem a sobreposição
de especialização observada anteriormente. O teste captura o painel da ficha,
não necessariamente a tela desktop inteira. Várias imagens não existem no vault
temporário; não foi aceita a completude de mídia nem certificada a UI inteira.
Capturas de página longa também registram a barra de navegação fixa no meio do
documento; não representam uma nova posição persistida da barra.

Checks já concluídos neste corte: frontend **304/304**, typecheck e build PASS;
o build mantém o aviso conhecido de bundle acima de 500 kB. Primeira rodada
backend **851/851**; repetição da fonte final **853/853**, em 599 s. Os 64
testes focados também passaram antes dessa rodada. Permanecem avisos existentes
de conexões SQLite não fechadas em fixtures e depreciação de `on_event` do FastAPI;
não houve falha nesses checks. `git diff --check` sem erros.
O lote HTTP final voltou a registrar **9 PASS + 1 EXPECTED_BLOCK**. O bloqueio
é Clonagem sem fragmento no inventário copiado; a prova unitária de concentração
usa a fixture nativa que já possui componente, sem concessão na campanha.
Lote final `omni-runner-validation-6tkej48a`: CLI nativa exit **0**, UI
**PASS** nos dois scripts (readiness 155 s; dez ativações 231 s). Há prova de
clique no card, seleção/confirmação quando aplicável, um POST, consequência,
consumo e estado mantido após reload. Inspecionadas também capturas de Reflexos,
Guarda e Aterrorizar; não são prova visual de todas as consequências posteriores.
A cena de ensaio contém cadáveres herdados/criados: este lote não certifica
limpeza da cena, biblioteca de mapas ou a legibilidade de todos os pins.

`certification_ready=false`: relatório seletivo mantém 40 entradas com checks
faltantes, **não 40 bugs confirmados**. A rodada via CLI não é evidência de um
novo job completo transportado pelo MCP do OpenCode; a reconexão foi confirmada
separadamente e o contrato MCP tem testes automatizados.
PASS seletivo não elimina as lacunas de certificação das quatro fichas;
celular físico e redes diferentes continuam INCONCLUSIVE.

## Arquivos deste corte

- `backend/scripts/{run_sheet_test,agent_test_jobs,companion_test_mcp,all_actions_simulation,sheet_rehearsal}.py`
- `backend/test_sheet_runner_batches.py`, `test_three_sheet_lifecycle_proofs.py`
- Helper de fixture em `backend/test_opencode_three_sheets_gaps.py`
- `frontend/tests/opencode-three-sheets-gaps.test.cjs` (renomeado)
- `frontend/tests/three-sheet-actions-smoke.cjs`
- `docs/AI_TEST_TOOLS.md` e este documento

Sem mudanças em `backend/app` ou `frontend/src`: não há atualização operacional
para carregar reiniciando 8787. Sem alteração de fichas, regras, tokens, Vault,
modelos ou configuração global; sem staging, commit ou push.
Próximo corte de produto, após fechar este ensaio: contrato explícito de ação
com piloto de Relâmpago, conforme `VTT_REA_STUDY_2026-10-15.md`.
