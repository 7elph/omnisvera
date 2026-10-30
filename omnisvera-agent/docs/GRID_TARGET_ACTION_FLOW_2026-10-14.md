# Ações pelo mapa — 14/10/2026

Fluxo principal: **Usar → alcance/alvos no mapa → clicar no pin → Sim/Não → dados e resultado aplicado**.
Não consome recursos ao mirar ou cancelar. Ataques usam os recibos de resolve/confirm existentes;
não executam comandos dentro de atualizadores React. No grid, este fluxo rola dados digitais,
sem alterar o modo físico global da mesa. Sem grid, os controles legados permanecem assistidos.

## Implementado

- Rota de alcance acessível ao dono da ficha e ao Mestre; jogadores não recebem pins ocultos
  nem podem declarar alcance arbitrário. Invocações controladas usam as mesmas permissões.
- Ataques da ficha, Mísseis, poderes ofensivos de sangue e Toque seguem o alvo do pin,
  sem dropdown de alvo ou segunda confirmação de dano. Quantidade/modo de sangue permanecem escolhas.
- Aterrorizar, Clonagem e Magia da Morte dispensam “Preparar magia”; a área/custo é confirmada antes da execução.
- Dorn: Reflexos direto; Teia/Força pelo pin; Dissipar direto quando há um efeito elegível.
  Havendo vários efeitos no mesmo alvo, ainda é necessário escolher qual magia dissipar.
- Vinhas e Animar Mortos recebem seleção pelo pin. Corpo já utilizado/não autorizado é rejeitado.
- Alcance aprovado pelo Mestre: Vinhas, Adaga de Osso e Lâmina de Sangue à distância = 9 m,
  tanto na mira quanto na validação do backend. Lâmina corpo a corpo continua adjacente.
- “Usar” do esqueleto recupera a invocação viva existente, inclusive em outro mapa, sem duplicar ou cobrar.
  “Dispensar” arquiva sua participação no mapa/turnos. Não devolve uso diário; mantém auditoria e idempotência.

## Limites explícitos

- Animar mantém a seleção de cadáver no mesmo mapa; distância máxima não foi inventada.
- Relâmpago ainda exige declaração de área/contatos; não há paredes/reflexões/LOS automáticos.
- Passivas narrativas ou habilidades sem regras aprovadas não ganham efeito por um botão genérico.
- Clonagem continua exigindo cristal consumível. O estoque operacional encontrado foi zero;
  componentes entregues no ensaio pertencem somente à fixture TEMP.

## Validação e ferramentas

`companion-tests` continua usando os quatro atores e `ui:true`. O ensaio visual vigente é
`grid-action-flow-smoke.cjs`; o antigo ensaio de dropdown físico permanece como referência legada,
não certifica o fluxo novo. API física continua coberta pelos adaptadores nativos.

Regressão completa intermediária: 773 backend / 268 frontend; checks finais e publicação devem
ser registrados na entrega. Ensaios isolados provaram Sim/Não, cancelamento sem gasto, aplicação,
reload dos quatro atores (390/1440 px), Clonagem/encerramento e Reflexos, incluindo segundo cliente local.
Primeiro MCP: INCONCLUSIVE por reset em mapa errado (corrigido na fixture). Segundo: API 70 PASS +
2 EXPECTED_BLOCK, FAIL visual por cadáver sobreposto (separado sem force-click). Essas tentativas
não foram apagadas. Mídia do mapa real foi copiada apenas ao vault TEMP para a repetição visual.

Não certifica celular físico ou estabilidade entre redes distintas; não houve combate, descanso,
dispensa ou entrega de loot no banco operacional durante os ensaios.

## Arquivos deste corte (worktree misto preservado)

Backend: `app/action_range.py`, `app/main.py`, `app/schemas.py`, `app/summons.py`,
`app/combat.py`, `app/spatial_grid.py`, `app/session6_rewards.py`;
`scripts/all_actions_simulation.py`, `scripts/run_sheet_test.py`;
`test_action_range.py`, `test_attack_range.py`, `test_session6_combat.py`, `test_session6_rewards.py`.

Frontend: `src/api.ts`, `src/pages/SessionWorkspace.tsx`;
`src/components/TargetConfirmation.tsx`, `SpellTargetControl.tsx`, `SpellResolution.tsx`,
`MonsterAttackPanel.tsx`, `SummonControls.tsx`, `VineBraceletControl.tsx`;
`tests/target-confirmation.test.cjs`, `grid-action-flow-smoke.cjs`, `approved-spells-smoke.cjs`,
`summon-controls.test.cjs`, `blood-technique-physical.test.cjs`, `necromancer-spells.test.cjs`,
`raziel-vampire-powers.test.cjs`.

Documentação: este arquivo e `AI_TEST_TOOLS.md`. Alterações anteriores nos mesmos arquivos
não foram removidas ou incluídas em commit por este corte.

## Fechamento desta execução

- Backend completo: 777/777 no `.venv-observer`. Frontend: 270/270; typecheck e build PASS.
- MCP `test-6d992b51938447d5a574cce0cdb1010b`: PASS, API 70 PASS + 2 EXPECTED_BLOCK;
  os seis ensaios visuais passaram. Aceitação visual local conferida nas capturas do mapa/resultado.
- A primeira repetição usou `backend/.venv` sem `mcp` e uma fixture importada antes da correção;
  falhou (766 testes, 2 erros, 1 skip). A repetição final acima usou o ambiente de ensaio completo.
- Backup: `C:\Users\delib\OmnisveraBackups\pre-grid-actions-20261014-040026`.
- **Ativação pendente**: a ferramenta bloqueou o comando de reinício do 8787. Não se tentou contornar
  o bloqueio. Backend anterior permanece ativo; `/gm/grid/range` ainda retornou 404 para os jogadores.
  O build frontend foi gerado, mas não deve ser considerado operacional sem atualizar o backend.
- Comparação read-only de fichas, inventário, relógio/efeitos, pins, posições e credenciais:
  hashes idênticos antes/depois dos ensaios. Nenhum commit/push realizado.

### Ativação posterior — 14/10, 04:25

Após pedido explícito de reinício, somente o Python do 8787 foi encerrado.
O lançador oficial `start_backend.ps1 -Port 8787` iniciou o backend atualizado (PID 61688).
Health autenticado e fichas dos três jogadores: 200. Mira nos pins visíveis dos mapas corretos:
200, `gridded=true`, alcance 9 m nas três habilidades aprovadas. Raiz local e pública: 200.

Backup novo: `C:\Users\delib\OmnisveraBackups\pre-backend-restart-20261014-042455`.
Hashes de fichas, inventário, combate/efeitos, pins e posições permaneceram iguais.
O lançador reserializou o JSON de credenciais; comparação dos valores confirma nenhum token alterado.
Tailscale não foi reiniciado. Nenhuma ação de combate/rest/loot foi executada no banco operacional.
Esses checks são locais/HTTP pelo domínio público, não uma nova prova de redes distintas.
