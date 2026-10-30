# OpenCode — provas de lacunas de Vezemir, Morthak e Dorn (testes/evidencias)

Tarefa de testes/evedencias, NAO de mecanica. Nenhuma regra, ficha real,
balanceamento, catalogo, runtime, imagem/Vault/CAMPANHA/zz_media/modelo/Godot
foi alterado neste lote. Raziel foi apenas regressao (suite cheia); sem
alteracao de regras ou ficha dele.

## Base

- Branch: `devin/create-omnisvera-class-standard` (nao foi usada `main` como referencia).
- SHA: `1a07a84d3f753b277b8b3542baeb27a3df411077` (curto `1a07a84`).
- Worktree misto pre-existente preservado; sem `git add`, commit ou push.
- Leitura previa completa: AGENTS.md, CURRENT_COMPANION_CODE.md, AI_TEST_TOOLS.md,
  AI_ACTION_HANDOFF_2026-10-15.md, THREE_SHEETS_AUDIT_2026-10-15.md,
  SHEET_CERTIFICATION_2026-10-15.md.
- Diretorio exclusivo: `C:/Users/delib/Desktop/OMNISVERA/omnisvera-agent`.
- Modelo: Muse Spark 1.3 Free, sem mudanca de configuracao global ou de modelo.

## Ensaio MCP `companion-tests` (fixture TEMP nativa)

- `companion_test_capabilities`: suite `native_sheet_actions`, atores
  `raziel/morthak/vezemir/dorn7`, isolamento SQLite/vault TEMP, sem tokens reais.
- `companion_test_start`: request_id `opencode-three-sheets-20261016-001`,
  actors `[vezemir,morthak,raziel,dorn7]`, `ui: true`.
- run_id `test-e28e1d9e5eb24ac2b885dc3d603676ce`, `production_modified: false`.
- Resultado: estado terminal `ERROR`, `verdict: INCONCLUSIVE`,
  erro `TIMEOUT: owned test process tree stopped` apos ~20 min (limite do ensaio).
  Repeticao com o MESMO request_id/parametros devolveu o mesmo job terminal,
  sem relatorio. Nenhum job duplicado foi lancado; nenhum servico foi
  reiniciado ou morto para liberar lease.
- Conclusao legitima: INCONCLUSIVE de harness (timeout/fixture), NAO falha de
  regra. `certification_ready` permanece `false`; PASS seletivo anterior nao
  certifica ficha inteira. UI (`report.ui_smoke`) sem aceitacao visual neste
  corte; celular fisico/redes distintas seguem INCONCLUSIVE.

## Arquivos novos (unicos alterados/criados neste lote)

1. `backend/test_opencode_three_sheets_gaps.py` — 8 testes isolados, fixtures
   descartaveis TEMP, sem 8787/8788, sem banco/token real:
   - Toque Sombrio: dot persiste apos reload, custo 1, retry idempotente.
   - Animar Mortos + Levantar Esqueleto: coexistem como tokens distintos e vivos.
   - Clonagem sem fragmento: `ValueError: fragmento`, recurso preservado,
     nenhum token (EXPECTED_BLOCK, sem concessao de item).
   - Guarda: expira no turno de Dorn; aliado sem posicao no grid e rejeitado
     sem gastar acao/estado.
   - Teia: area ambiental aplicada e expirada apos avanco do relogio.
   - Reflexos: area ignora interceptacao; acerto unico e interceptado e
     consome 1 imagem.
   - Contrato: PASS seletivo + layout PASS nao certificam acoes nao executadas.
2. `frontend/tests/opencode-three-sheets-gaps.cjs` — 4 testes estaticos
   (`node --test`), sem servidor: multi-selecao/confirmacao sem duplicar pin,
   delegacao unica do card, superficie `data-grid-token`/overlay/dialogo
   `Confirmar alvo`, ausencia de 8787/8788.
3. Este relatorio.

Nao foram editados: `backend/app/*`, `frontend/src/*`, catalogos,
`opencode.json`, AGENTS.md, harness/scripts existentes.

## Acao x checks comprovados (pelos testes novos isolados)

| Acao | execucao | persistencia/reload | idempotencia | custo | alcance/grid | expiracao | UI |
|---|---|---|---|---|---|---|---|
| Toque Sombrio (Morthak) | x | x (re-read) | x (retry) | x (0/1) | — (alvo token proximo, sem grid novo) | parcial (dot presente; perda por turno segue no runner nativo) | pendente (script visual) |
| Animar + Esqueleto | x (2 tokens) | x | — | — | — | pendente (dispensa dedicada) | pendente |
| Clonagem | bloqueio previsto | — | — | x (sem gasto) | — | pendente (concentracao/5 rodadas no runner) | pendente |
| Guarda (Dorn) | x | x | x (padrao do protocolo) | — (sem recurso; orcamento de turno nativo) | x (grid exigido) | x (turno de Dorn) | pendente |
| Teia (Dorn) | x | x | — | pendente (movimento 3x no runner) | x (mapa do combate) | x | pendente |
| Reflexos (Dorn) | x | — | x (replay nativo) | x (imagens) | — | — | pendente |
| Contrato geral | — | — | x | x | x | x | x (layout nao certifica uso) |

`x` = comprovado pelo teste novo; `pendente` = segue lacuna para o runner/MCP.

## RED reproduzidos (sem esconder defeito)

1. Backend com `python` do sistema: 4 ERRORs `ModuleNotFoundError: fastapi`
   (ambiente errado, nao defeito do produto). Reexecutado com
   `.venv-observer/Scripts/python.exe`: 8/8 PASS.
2. Frontend `three-sheet cards...`: RED `pins precisam de data-grid-token` —
   expectativa errada do teste (atributo vive em `SessionWorkspace.tsx`, nao em
   `TargetingOverlay.tsx`). Teste corrigido; produto intacto.
3. Frontend, passo seguinte: RED `fluxo Sim/Nao precisa existir` — dialogo
   `Confirmar alvo` vive em `TargetConfirmation.tsx`, nao no workspace.
   Teste corrigido para checar o componente real + uso no workspace.
   Ambos os REDs eram defeitos do proprio ensaio, nao das regras; o registro
   e preservado aqui em vez de reescrever historia.

Nenhum RED de regra nova foi encontrado nestas familias; nenhum FAIL foi
pintado de verde.

## Checks executados

- Backend novo: 8/8 PASS (`.venv-observer`, ~26 s).
- Backend completo: **838 testes OK** (~591 s; 830 pre-existentes + 8 novos).
  Avisos pre-existentes (SQLite nao fechado, chunks >500 kB, `on_event`
  depreciado) permanecem, fora deste corte.
- Frontend novo: 4/4 PASS (`node --test`).
- Frontend `tsc --noEmit`: PASS. `npm run build`: PASS (11,78 s).
- `git diff --check`: PASS (apenas avisos CRLF pre-existentes do worktree).
- MCP: INCONCLUSIVE por timeout (acima). Nao reiniciado backend/tunel/servicos;
  nenhum ataque/conjuracao/descanso/transacao em mesa operacional.

## Limites do proprio ensaio

- Fixture TEMP com vault isolado; midia ausente nao e defeito operacional.
- Sem prova em celular fisico, redes distintas ou rolagem humana:
  `real_table_validation = INCONCLUSIVE`.
- Dispensa individual esqueleto/zumbi, concentracao da Clonagem, custo de
  movimento 3x da Teia no grid e UI por acao (custo/consequencia/reload
  visuais) continuam pendentes de runner/MCP.
- Ambiguidade registrada: Vezemir (Provocacao/Velocidade/Frenesi/Pulseira)
  tem cobertura parcial nos nove casos estendidos do smoke; quais entradas
  contam como `READY` por acao depende de `report.certification.gaps` do
  proximo MCP verde — nao inventado aqui.

## Bloqueios legitimos

- Lease/timeout do MCP: 1 job por checkout, 20 min; TIMEOUT apos o teto.
  Nao matar processos nem forcar porta.
- Sem `scenario_id` exato de relatorio anterior disponivel (sem report),
  entao sem repeticao seletiva — apenas o lote integral ja autorizado.
- Sem integracao no runner neste lote (proibido editar harness); proposta
  abaixo para o Codex revisar.

## Proximo patch recomendado ao Codex (revisao, nao aplicado)

1. Registrar no runner nativo (`run_sheet_test.py` + adaptadores, sem motor
   paralelo): cenarios de expiracao por turno do Toque Sombrio, dispensa
   esqueleto/zumbi, concentracao/fim da Clonagem, custo de movimento 3x da
   Teia e prova UI por acao (Guarda/Teia/Reflexos/Dissipar alem das tres
   atuais), com `verified_checks` por cenario (execution/persistence/
   idempotency/cost/range/expiration/ui).
2. Reexecutar MCP com NOVO request_id, quatro atores e `ui: true`, quando a
   lease estiver livre; ler `report.certification.gaps`/`missing_checks` e
   `report.ui_smoke` (incl. capturas e custos) antes de declarar qualquer
   acao `READY`.
3. Integrar `backend/test_opencode_three_sheets_gaps.py` e
   `frontend/tests/opencode-three-sheets-gaps.cjs` a documentacao de
   certificacao quando os cenarios nativos correspondentes existirem.
