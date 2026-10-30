# Piloto de contrato de ação — Relâmpago

## Modelo

Contrato aditivo na habilidade existente em `app/data/dorn7_mage3.json`.
Não há catálogo paralelo, importação de código VTT ou novo motor de combate.
`action_contract.py` valida campos tipados, versão/revisão e fórmulas inteiras
limitadas (`base + per_level × nível`, com teto opcional), sem `eval`.
Somente o binding nativo `dorn_relampago` está habilitado neste corte.
Não interpreta texto de PDF como mecânica nem habilita scripts/URLs enviados por IA.

`action_library.native_action_contract` resolve o nível vigente. O mesmo
contrato alimenta a descrição da ficha, o anel e o executor `dorn_spells.command`.
`describe_action` expõe blocos/custos e o binding, mas mantém `executable=false`
para a rota genérica: execução exige o comando nativo autorizado de Dorn.
O contrato é metadado, não prova de disponibilidade, recurso ou turno disponível.

## Regra preservada

- Até três entidades vivas únicas; dois pins de um personagem não duplicam dano.
- Alcance `40 + 10 × nível` metros, usando a escala e distância do grid atual.
- Uma rolagem `min(10, nível)d6` compartilhada; uma JPD por entidade.
- Sucesso reduz à metade arredondada para baixo; falha recebe integral.
- Um recurso `dorn_relampago`, recarga nativa `inn_rest`, ação principal nativa.
- Instantânea, alvos escolhidos, sem linha/bifurcação/reflexões automáticas.

A origem continua omitida da lista de seleção do preview. A API legada já
aceita dano no próprio Dorn; isso é preservado, inclusive sem restaurar seu PV
ao salvar o consumo. Pins de outros personagens agora podem receber Relâmpago
no grid: valida-se o pin selecionado e aplica-se dano à ficha canônica.

## Fluxo e compatibilidade

Card → anel → seleção → confirmação → comando nativo → resumo existente.
Sem botão novo. Preview/cancelamento não rolam dados nem consomem recursos.
O cliente recebe limites resolvidos e envia só alvos, mapa e revisão, além de
request_id/versão do comando atual; dano/custo/alcance são recalculados no servidor.
Um binding desconhecido falha fechado no frontend.

A transação, orçamento, autorização Mestre/Jogador, ledger, realtime e recibo
continuam em `effect_command`. Retry recupera o recibo antes de recalcular nível;
intenção diferente com mesmo ID continua conflito. Revisão ou mapa desatualizados
no comando novo são rejeitados sem rolagem/gasto. Clientes legados sem esses
campos mantêm o caminho antigo; não são considerados prova do contrato novo.
Frontend novo + backend antigo também mantêm o payload anterior e o limite
legado de três alvos, em vez de entrar novamente em mira. Esse fallback foi
reproduzido em RED e coberto por teste, para permitir ativação gradual.
O comando sem grid continua assistido pelo Mestre, sem inventar posições.

## Ensaios e limites

Regressões novas cobrem contrato/nível, cap de dano, fórmula inválida, binding
desconhecido, preview sem custo, escala real, metade/integral, concorrência/retry,
registro único, persistência, revisão/mapa antigos e pins duplicados.
Suítes anteriores preservam limite 1–3, rollback de alvo inválido, turno,
recurso insuficiente, autorização e o caminho legado.

MCP ganhou lote explícito `ui_suite=lightning`, com quatro atores e `ui:true`:
readiness + smoke nativo de Relâmpago, sem lojas ou smokes omitidos silenciosamente
do lote `full`. O limite de 20 minutos e as leases não foram alterados.
O smoke usa uma segunda página renderizada para conferir convergência local,
além de seleção/cancelamento, 1/3 alvos, resposta atrasada, mobile e reload.

Backend **863/863** PASS; 48 testes focados PASS e repetição final dos 21 de
contrato/runner PASS. Frontend final, incluindo o fallback: **308/308** PASS.
Typecheck/build finais PASS (aviso conhecido de bundle >500 kB). Permanecem avisos
existentes de conexões SQLite em fixtures e depreciações do FastAPI/AnyIO.

MCP `test-945b4a41706142988003dc9f42382661`: quatro API PASS, readiness PASS,
smoke multi-alvo FAIL num clique mobile. Recibo e falha foram preservados.
Repetição sem a suíte backend concorrente e trazendo a aba interagida ao primeiro
plano, sem forçar cliques: `test-395d9169b9484758a59cea38d2da740b` **COMPLETED/PASS**,
quatro API PASS e dois scripts PASS (59,5 s + 49,6 s). Reconexão de um novo
cliente stdio recuperou o mesmo run_id/relatório, sem repetir conjurações.
Isso não identifica isoladamente a causa do primeiro timeout.

Capturas desktop/mobile de seleção/confirmação conferidas: diálogo contido e
seleção funcional. **Imagem de fundo e retratos ausentes na fixture impedem
aceitar visualmente alinhamento com a arte ou completude de mídia**. Não se
declara a interface inteira pronta a partir desse PASS lógico/funcional.
`certification_ready=false` é intencional no relatório seletivo.

Só fixtures TEMP recebem conjurações de QA. Não certifica todas as fichas, mídia, celular físico
ou redes diferentes; não implementa executor genérico nem migra outras magias.

## Ativação operacional

**PENDENTE**. Backup consistente criado em
`backend/data/backups/pre-action-contract-20261016-024211` (ignorado pelo Git),
incluindo SQLite e credenciais persistidas. A tentativa autorizada de reiniciar
somente a árvore identificada do backend foi bloqueada pelo ambiente **antes
de executar**. Não houve nova tentativa por outro meio.
Backend anterior permanece no PID 162980; túnel não foi alterado. Conferência
posterior: hashes das 27 tabelas protegidas e tokens idênticos ao backup.
Sem combate ativo no momento da verificação e sem ação de QA em produção.
O frontend compilado mantém compatibilidade com esse backend anterior; o
contrato backend novo só estará ativo depois de um reinício permitido.
Somente o MCP `companion-tests` foi recarregado depois da atualização do schema:
disconnect/connect `true`, estado `connected`; modelo e conversas intactos.
`git diff --check` sem erros. Nenhum backup/credencial entrou em staging.

## Arquivos deste corte

- `backend/app/{action_contract,action_library,action_range,dorn_spells,character_play,main}.py`
- `backend/app/data/dorn7_mage3.json`, `backend/test_lightning_contract.py`
- `backend/scripts/{run_sheet_test,agent_test_jobs,companion_test_mcp}.py`
- `backend/test_sheet_runner_batches.py`
- `frontend/src/api.ts`, `pages/SessionWorkspace.tsx`, `components/configuredGridAction.ts`
- `frontend/tests/{configured-grid-action.test,range-multitarget-smoke}.cjs`
- Este documento, `AI_TEST_TOOLS.md`, `CURRENT_COMPANION_CODE.md`

Worktree misto preservado; sem staging, commit ou push. Próximo corte seguro:
uma segunda ação simples aprovada, comprovando o contrato antes de extrair
componentes comuns de JP/dano/custo. Não migrar centenas de skills de uma vez.
