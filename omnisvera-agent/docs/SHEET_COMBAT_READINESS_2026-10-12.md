# Ficha e combate — correção visual e aceitação por IA

## Defeitos reproduzidos e corrigidos

PV pendentes e Especialização estavam dentro do grid estreito do cabeçalho
de retrato. O smoke na aplicação compilada falhou com dois catálogos dentro
da identidade. Agora são seções próprias, fora daquele cabeçalho; PV usa
linhas completas, texto e botão sem sobreposição, inclusive em 360/390 px.

Necromante tinha nome e nota, mas nenhum benefício/restrição no catálogo.
O teste de proprietário falhou com `benefits=[]`. Foram expostas as regras
já existentes de Toque Sombrio, Aterrorizar e renúncia aos círculos 7º–9º;
não houve nova concessão, recarga, rolagem de PV ou alteração mecânica.
Benefícios/restrições aparecem na ficha e na descrição que abre/fecha.
Erro ao carregar especialização agora fica visível e tem retry; não some
silenciosamente. Escolher Maestria continua exigindo arma selecionada.

## Ferramentas: API não equivale a interface

O MCP existente ganhou `ui: true` em `companion_test_start`. A opção integra
os scripts fixos de aceitação ao executor e à mesma fixture descartável.
Com quatro atores, verifica layout e botões físicos de combate; com seleção
menor, verifica o layout dos atores selecionados, sem prometer o smoke completo.
O veredito guarda `report.ui_smoke`. Falha visual não é escondida por cenários
API verdes; ausência de dependência/timeout não gera PASS. O modelo não fornece
código, SQL, credenciais, endereço ou regra de campanha ao executor.
Recibos antigos sem UI mantêm seu fingerprint; solicitar UI muda o contrato
e requer um novo request_id. AGENTS e o guia de agentes indicam essa opção.

## Validação final

- Backend: **652/652**; frontend: **247/247**; typecheck, build e diff-check passaram.
- Smoke visual: Mestre/proprietário e fichas dos quatro atores; 360/390 px;
  especialização também em 1440/1024 px, sem overflow.
- MCP stdio real, retry e reconexão: **64 PASS / 1 EXPECTED_BLOCK**, em 65 cenários.
- `ui_smoke=PASS` nos dois scripts: layout e combate físico, incluindo Toque,
  Lâmina/Arma/Garras/Investida, Sangue Defensivo e expiração, Caixão, Reparo de
  Dorn consumindo kit e permitindo ataque no mesmo turno, reload e atualização
  no segundo cliente. D20 físico é entrada simulada, não dado rolado por pessoa.
- Evidência privada: `%TEMP%/omnisvera-mcp-test-smoke-7j5se3eh/mcp-evidence.json`.
- Persistem warnings antigos de SQLite/lifespan e chunk >500 kB no build.

Backend reiniciado com backup; banco, tokens, fichas, sessão, combate e
solicitações de rolagem foram comparados e preservados. Fichas dos três
jogadores, benefícios de Morthak e retratos autenticados dos quatro responderam
200 pelo endereço público. Nenhum combate/consumível foi executado na produção.
Sem commit/push; mudanças preexistentes do worktree misto foram preservadas.

## Geração: estado real, não promessa

Ollama responde, mas o runtime pede `omnisvera-local:latest`, ausente dos tags
consultados. Os modelos disponíveis são `gpt-oss:120b-cloud` e
`gpt-oss:20b-cloud`. O rótulo de conexão agora diz **serviço online**, não
confirma geração/modelo. Não instalei modelo nem troquei por cloud sem escolha.

Cenas ainda é editor/execução nativa; não tem autogerador ligado. O código de
imagens já roteia modo oficial para FLUX Klein 9B, com fallback ZeroGPU nas
falhas previstas, e modo de teste para 4B. Há jobs/imagens anteriores, mas
nenhum metadado persistido de roteamento nesses jobs; não há prova de que o
9B produziu essas imagens. Nenhuma geração paga/remota foi disparada neste corte.
Ligar autogeração de propostas exige resolver local vs cloud e manter rascunho
privado, validação e aplicação explícita; não deve publicar ou alterar canon
automaticamente.

## Limites ainda explícitos

Não certifica todas as passivas, todos os equipamentos/mídias, celular físico
ou endurance com redes distintas. A fixture tem vault isolado e não contém
todas as imagens; screenshots dela não certificam mídia operacional. Os
retratos públicos foram verificados separadamente. Forma animal completa,
passivas assistidas e fraqueza a fogo do summon continuam na fila anterior.
Nove rolagens de PV e escolha de especialização de Vezemir continuam pendentes.

## Arquivos deste corte

- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/components/PendingLevelRolls.tsx`
- `frontend/src/components/SpecializationSection.tsx`
- `frontend/src/styles.css`, `frontend/src/App.tsx`
- `frontend/tests/specialization.test.cjs`
- `frontend/tests/specialization-layout-smoke.cjs`
- `frontend/tests/sheet-combat-readiness-smoke.cjs`
- `frontend/tests/combat-simulation-physical-smoke.cjs`
- `backend/app/level_advancement.py`, `backend/test_morthak_sheet.py`
- `backend/scripts/run_sheet_test.py`, `backend/scripts/agent_test_jobs.py`
- `backend/scripts/companion_test_mcp.py`, `backend/scripts/agent_test_mcp_smoke.py`
- `backend/test_agent_test_tools.py`
- `AGENTS.md`, `docs/AI_TEST_TOOLS.md`, `docs/CURRENT_COMPANION_CODE.md`
- `docs/SHEET_COMBAT_READINESS_2026-10-12.md`
