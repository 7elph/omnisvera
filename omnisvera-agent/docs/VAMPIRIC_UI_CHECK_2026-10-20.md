# Poderes vampíricos — lote isolado

Escopo: Regeneração Vampírica, Mordida, Caixão e Forma da Noite. Não muda regras,
estoque, ficha operacional, modelo ou configuração do Companion.

## Ferramenta

Novo lote explícito `ui_suite:vampiric` no executor/MCP existente. Exige `ui:true`
e os quatro atores. Duas metades fixas, mesmo teto de 300 s por script e 1.200 s
por job; nenhuma entrada de script, SQL ou regra enviada pela IA. Outros lotes
permanecem iguais. O teste histórico `raziel-ready-smoke` continua preservado,
mas não é usado: depende de controles anteriores à reforma da Hemomancia.

- Primeiro script: Regeneração desktop/Mestre e Mordida 390 px/jogador.
- Segundo: Caixão 390 px/jogador e Forma da Noite desktop/Mestre.
- Usa cards atuais, seleção/confirmar no grid para Mordida, comandos/recibos
  nativos, gasto/recarga e reload. Ações concluídas atribuem apenas evidência UI;
  preparação da fixture não certifica ação.
- Cópia de mídia ampliada somente para os três arquivos de animais auditados;
  não copia a pasta de uploads ou conteúdo privado.
- Leitor de evidências de Cenas aceita o novo lote sem certificar propostas.
  Essa extensão do leitor não foi ativada no processo operacional neste corte.

## Regressões da implementação

RED: lote rejeitado, imagens animais ausentes na fixture e novo recibo rejeitado
pelo leitor reproduzidos antes das extensões. Isso não é defeito das regras.

- Executor/isolamento/mídia: 57 testes OK (1 skip de symlink no Windows).
- Repetição com leitor de evidências: 42 OK (inclui testes anteriores; 1 skip).
- Backend Raziel/Caixão/Forma/drenagem: 32 OK.
- Frontend seções, Hemomancia e seletor/controle animal: 14 PASS.
- Sintaxe dos dois scripts Node: PASS. Typecheck: PASS.
- Build PASS com heap Node limitado a 384 MB; somente aviso existente de chunks
  grandes. Artefatos: `index-BcL0zZrI.js` / `index-D7lSSoQI.css`.
- Avisos existentes de Starlette/httpx e conexões SQLite coletadas nos testes.

Checks gerais após o patch visual:

- Backend nativo: 1.171 entradas em 550,621 s; 1.167 PASS, dois erros de import
  do SDK MCP ausente e dois skips. Não declarar essa execução nativa PASS.
- Observer já instalado: 30 testes OK de `test_omnisvera_app`, contrato MCP do
  lote e `test_agent_test_tools`. Inclui os dois pontos de erro e o skip MCP;
  não houve instalação ou mudança de dependências. Resta o skip de symlink.
- Frontend completo, `--test-concurrency=1`: 342 PASS, nenhum skip/falha,
  49,702 s. Typecheck e build também PASS.

## Execução nativa

Recarga autorizada somente do conector `companion-tests`: disconnect/connect
HTTP 200. Companion e OpenCode preservados. Request
`codex-friday-vampiric-ui-20261020-v1`, recibo
`test-738e3fa18bae48b0a04e13de610ff876`. Seis IDs API foram selecionados do lote
combat anterior, sem inventar cenários.

V1 concluiu COMPLETED/PASS, exit 0, em 345,47 s: seis API PASS e quatro usos UI
PASS. Scripts: 119,192 s e 118,165 s. Regeneração rolou 2 e gastou 1 sangue;
Mordida acertou com 1d6, causando 2 PV e cura correspondente. Caixão confirmou
limpeza/recarga e Forma da Noite confirmou a base animal, restrições, reload e
retorno com 4 PV excedentes após dano 5. Capturas 390/1440 revisadas.

Na revisão visual apareceu recorte nos nomes dos animais do seletor aberto.
Um teste de componente em card de meia largura reproduziu RED. CSS mínimo
faz a lista aberta ocupar a largura inteira do card, movendo Ativar abaixo;
fechado conserva a apresentação compacta. Componente passou em 390/1440 e
captura mobile foi revisada. O smoke nativo passou a exigir nomes/imagens sem
overflow; V1 permanece histórico e não certifica esse patch posterior.

Repetição integrada solicitada com request novo
`codex-friday-vampiric-ui-20261020-v2-layout`, mesmos seis cenários e dois
scripts fixos. Sem recarga adicional do conector nem alteração do backend
operacional.
Recibo V2: `test-b58e9668557b41448e00f19bf2218734`; seis cenários API PASS,
quatro usos UI PASS, COMPLETED/PASS, exit 0, em 258,114 s. Scripts: 77,611 s
e 92,018 s. Fonte de aplicação congelada durante o ensaio. Novas capturas do
seletor e da forma ativa revisadas: imagens e três nomes cabem sem recorte;
habilidades humanoides ficam indisponíveis durante a transformação.

Na V2, Regeneração rolou 4; Mordida errou e confirmou zero dano/cura. O acerto
com dano/cura observado na V1 permanece evidência separada, não foi rerrolado
para forçar um resultado. O relatório V2 mantém `all_actions_certified:false`.
Fixture 8871 encerrada. PIDs operacionais preservados: Companion 253460,
OpenCode 38768. Homes local/pública HTTP 200 entregando o novo bundle/CSS.

## Arquivos deste corte

- `backend/scripts/run_sheet_test.py`, `companion_test_mcp.py`,
  `agent_test_jobs.py`, `fixture_media.py`.
- `backend/app/test_run_evidence.py` (somente allowlist de recibos).
- `backend/test_sheet_runner_batches.py`, `test_fixture_media.py`,
  `test_test_run_evidence.py`.
- `frontend/tests/raziel-vampiric-smoke.cjs` e wrapper
  `raziel-vampiric-second-smoke.cjs`.
- `frontend/tests/night-form-visual.cjs` (RED/aceitação de meia largura) e
  `frontend/src/companionTheme.css` (três regras do seletor aberto).
- `docs/AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md`, este relatório e índice
  de fechamento.

Sem staging, commit ou push. Nenhum resultado deste lote certifica toda ficha,
todos os animais, imagens completas, celular físico ou redes distintas.
Ainda não há prova integrada dos demais traços raciais, imunidades, todas as
combinações possíveis ou visual dos PV de pins durante cada transformação.
