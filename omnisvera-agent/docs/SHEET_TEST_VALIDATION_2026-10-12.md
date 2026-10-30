# Validação do primeiro executor por ficha

Nota posterior: o FAIL do Anel Rúnico descrito abaixo foi corrigido e o backend
ativado. Ensaio posterior: 64 PASS / 0 FAIL / 1 EXPECTED_BLOCK em 65 cenários.
Consulte `RUNIC_RING_AND_SESSION7_CLOSURE_2026-10-12.md`. O texto abaixo registra
o primeiro resultado histórico, não o estado atual do anel.

## Resultado operacional isolado

**65 cenários distintos: 63 PASS, 1 FAIL, 1 EXPECTED_BLOCK**, considerando a
execução dos quatro personagens e a repetição dos dois casos afetados.

- Ensaio completo: `omnisvera-sheet-test-zo8qelfi`, 62 PASS / 2 FAIL / 1 bloqueio.
- Repetição após correção do ensaio: `omnisvera-sheet-test-gsvnn6xx`, poção de
  Vezemir PASS; Anel Rúnico de Raziel FAIL confirmado.
- A primeira execução, `omnisvera-sheet-test-xplnb919`, encontrou um campo
  indevido no DTO de ataque do teste de Mísseis sem usos; corrigido e repetido
  com PASS no ensaio completo. Não foi tratado como defeito do produto.

Artefatos ficam nas pastas acima em TEMP, não neste repositório. A consolidação
usa o resultado mais recente de cada scenario_id; não apaga evidência histórica
nem soma repetições como cenários novos. Os relatórios originais conservam o
resultado do momento da execução (o completo ainda mostra a falha antiga da poção).

## Falha real encontrada, não corrigida silenciosamente

**Anel Rúnico:** descrição persistida “1 vez por dia recupera 4 de vida”; estoque
com uma carga e recarga `inn_rest`, mas mecânica `consume_mode=none`.
O comando aplica a cura sem diminuir a carga. O teste marca FAIL e encerra
com código 1; não reclassifica essa inconsistência como automação certificada.
A correção do cadastro/contrato nativo será o próximo ajuste mecânico. Nenhum
item foi alterado na produção como consequência de executar QA.

**Morthak / ranged genérico:** rejeitado por ausência de dano configurado;
EXPECTED_BLOCK. Adaga de Osso é a opção funcional, testada separadamente.

## Correções do próprio ensaio

- Payload de ataque não inclui `position_confirmed`, campo específico de técnica.
- Consumir a última poção remove a pilha do DTO; isso não é falha do consumível.
- Erros sem mensagem agora guardam tipo/traceback na evidência privada.
- Cobertura vem de cenário executado, não de lista fixa de habilidades “prontas”.
- Fingerprint transacional verifica idempotência no SQLite sem repetir dezenas
  de leituras de fichas; cada caso ainda verifica nova leitura HTTP e paridade.
- Repetição seletiva por `--scenarios` não certifica entradas não executadas.

## Escopo comprovado e limites

Checks finais: backend **626/626**, incluindo 15 testes novos do executor;
frontend **245/245**; TypeScript, build e `git diff --check` passaram.
Persistem ResourceWarnings de conexões SQLite em fixtures antigas, aviso de
lifespan depreciado e aviso de chunks >500 kB no build. Não foram ocultados
nem corrigidos por refatoração fora de escopo.

Ataques/acerto/erro, preview/confirm, custos aprovados de sangue, PV/drenagem,
recurso insuficiente, restrição de proprietário, limite de ataque no turno,
consumíveis, efeitos/expiração, invocações, Caixão, grid/movimento e ações de
Dorn nos cenários descritos. Todos usam a API nativa e banco descartável.

Entradas restantes aparecem como PENDING, ASSISTED ou RULE_BLOCKED. Não há
certificação geral de passivas, toda propriedade de equipamento, novos círculos
ou todas as magias possíveis. Sem smoke visual novo ou endurance multirrede;
paridade deste corte é de DTOs por clientes HTTP distintos.

Túnel e backend operacional 8787 não foram reiniciados ou encerrados. Ao fim,
8871 sem listener e 8787 com os processos operacionais anteriores. Credenciais
operacionais não foram carregadas. Sem alteração de banco/cenas/fichas da mesa,
sem staging, commit ou push. Este corte só muda ferramentas de teste e docs.

## Arquivos deste corte

- `test_sheet.ps1`
- `backend/scripts/run_sheet_test.py`
- `backend/scripts/sheet_rehearsal.py`
- `backend/scripts/all_actions_simulation.py` (extensão do executor existente)
- `backend/test_sheet_rehearsal.py`
- `docs/SHEET_TEST_RUNNER.md`
- `docs/SHEET_TEST_VALIDATION_2026-10-12.md`
- `docs/CURRENT_COMPANION_CODE.md`
- `docs/AI_COMPANION_FOUNDATION.md`
- `docs/AI_COMPONENT_MAP.json`

Demais alterações do worktree misto foram preservadas, não atribuídas a este corte.
