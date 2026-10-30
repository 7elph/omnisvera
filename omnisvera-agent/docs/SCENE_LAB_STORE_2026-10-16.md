# Laboratório de Cenas — armazenamento privado de propostas versionadas

Módulo de armazenamento puro, sem rotas, sem UI e sem execução. Conteúdo
privado nunca é aplicado: `draft`/`approved`/`rejected` é estado de revisão,
não publicação, combate ou alteração de ficha. A integração (rotas,
autorização, frontend, runners) pertence ao Codex.

## Arquivos deste corte (únicos tocados)

- `backend/app/scene_lab_store.py` — implementação.
- `backend/test_scene_lab_store.py` — 14 testes isolados, fixtures TEMP.
- Este documento.

Não foram tocados: `main.py`, `schemas.py`, `scene_play.py`, frontend,
contrato de ações, runners, fichas, mapas ou produção. Sem restart, kill,
`git add`, commit ou push. Sem suíte inteira nem MCP neste lote.

## Funções públicas (SQLite `Path` como primeiro argumento)

- `init_lab(database_path)` — cria somente as 4 tabelas do laboratório
  (`scene_lab_proposals`, `scene_lab_revisions`, `scene_lab_receipts`,
  `scene_lab_history`) + ledger nativo. Cenas continuam de `scene_play`.
- `create_proposal(database_path, *, scene_id, title, kind, content,
  created_by, request_id)` — versão 1, `draft`, sem evidência.
- `update_proposal(database_path, proposal_id, *, expected_version, content,
  title, request_id)` — nova revisão imutável; volta a `draft` e invalida
  aprovação/evidência atual sem apagar o histórico.
- `list_proposals(database_path, *, scene_id=None)` — resumos com `id`,
  `scene_id`, `title`, `kind`, `version`, `status`, `updated_at`.
- `get_proposal(database_path, proposal_id)` — DTO completo + `history` +
  `revisions` (`[{version, title, content, created_at}]`, só no detalhe).
- `attach_evidence(database_path, proposal_id, *, expected_version, run_id,
  summary, request_id)` — vincula `run_id` estrito `test-<32hex>` à revisão
  atual com snapshot do conteúdo; não incrementa a revisão.
- `set_decision(database_path, proposal_id, *, expected_version, decision,
  reason, request_id)` — `approved`/`rejected` com motivo obrigatório;
  sempre explícita e manual; não incrementa a revisão.

DTO de mutação: `id`, `scene_id`, `title`, `kind`, `version`, `status`,
`content`, `created_by`, `created_at`, `updated_at`, `evidence`,
`decision_reason`, `history`. Evidência atual: `run_id`, `summary`,
`version`, `content_snapshot`, `created_at`.

## Regras aplicadas

- Proposta só para `scene_id` existente na tabela `scenes`; `kind` restrito a
  `action`/`scene_bundle`; título até 180; autor até 180; motivo de decisão
  obrigatório até 2000; JSON de `content` e `summary` até 50000 caracteres;
  `request_id` 8–120 `[A-Za-z0-9._:-]` (mesma regra de `scene_play`).
- JSON estrito: `allow_nan=False` rejeita NaN/Infinity em `content`/`summary`;
  profundidade máxima 64; `summary` fora de objeto é rejeitado.
- `expected_version` protege update/evidência/decisão; revisão antiga é
  rejeitada sem alterar nada. O fingerprint inclui `expected_version`:
  repetir a mesma intenção (versão antiga) devolve o recibo original, mas o
  mesmo `request_id` com `expected_version` diferente é outra intenção e
  conflita.
- Recibo primeiro (`BEGIN IMMEDIATE` + tabela de recibos antes da validação
  de revisão): retry com o mesmo `request_id` e mesma intenção devolve
  exatamente o DTO original mesmo após a versão avançar; intenção diferente
  com o mesmo ID conflita (`request_id já utilizado com outro conteúdo`).
- PASS enviado pelo cliente nunca aprova sozinho: evidência guarda apenas o
  resumo já verificado pelo caller; aprovação exige `set_decision` manual.
- Ledger nativo em todas as mutações, `visibility='gm'`, títulos narrativos
  sem despejo de conteúdo (`source_type='scene_lab_proposal'`).

## Testes (RED primeiro, TEMP apenas)

RED inicial: módulo inexistente (`ImportError`). REDs de integração durante o
corte, preservados como evidência: o ledger nativo exige as tabelas-fonte do
workspace/fichas/dados, então a fixture compõe `init_session_workspace` +
`init_character_play` + `init_dice_rolls` antes do ledger — mesma convenção de
`test_session_coherence`. Nenhum RED de regra; nenhuma expectativa foi
relaxada para esconder defeito.

Cobertura (18 testes): criação mínima e `scene_bundle`; cena inexistente/sem
tabela; limites de kind/título/conteúdo/tamanho/request; NaN/Infinity,
ninho profundo e autor >180 rejeitados; revisão imutável com reset de
aprovação/evidência e histórico retido; versões antigas rejeitadas nas três
mutações; retry após avanço retorna o recibo original; `expected_version`
como parte da intenção nas três mutações (repetição devolve recibo, mudança
conflita); conflito de intenção; concorrência com mesmo ID executa uma vez;
`run_id` estrito + snapshot; `summary` com NaN/tamanho rejeitado; motivo
>2000 rejeitado; segunda evidência substitui a atual e mantém a antiga no
histórico; decisão validada sem auto-aprovação por PASS; ledger `gm`
narrativo; resumos de lista + histórico + `revisions` no get (conteúdo de
versões anteriores; lista não carrega conteúdo); cenas/pins/fichas/
`scene_actions` intactos.

## Resultado

`python -m unittest test_scene_lab_store`: **18/18 PASS** (`.venv-observer`).
`git diff --check`: sem erros.

## Limites e pendências para o Codex

- Chamadores precisam das tabelas nativas de workspace/fichas/dados presentes
  (sempre verdade na base operacional); em base parcial, o ledger falha em
  vez de operar sem auditoria — comportamento intencional.
- `active_game_session_id` pode associar entradas ao `game_session` vigente;
  sem sessão ativa, grava nulo como outros eventos fora de sessão.
- Concorrência além de 2 threads e `run_id` de outros formatos continuam
  rejeitados por desenho; recibos crescem sem TTL (mesmo padrão de
  `combat_effect_commands`).
- Contrato estável para integração; nenhum ajuste de contrato necessário antes
  de sair do escopo: rotas devem exigir Mestre, nunca expor `content` a
  jogadores e nunca executar/aplicar proposta aprovada sem comando nativo
  separado.
