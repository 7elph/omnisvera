# Controles de mesa — 11/10/2026

Relatório histórico. Atualizações posteriores do OpenCode e correções de
12/10 estão em [OPENCODE_RECONCILIATION_2026-10-12.md](OPENCODE_RECONCILIATION_2026-10-12.md).

## Entrega deste corte

- Sessão → Ver sessão: Iniciar sessão / Finalizar sessão, usando o status nativo.
- Menu esquerdo → NPCs: controles de criaturas/pins e fichas dos aliados.
- Participante a 0 PV: sai da iniciativa e da renderização do mapa; ficha,
  loot e corpo continuam persistidos (inclusive para Animar Mortos).
- Se o participante atual cai, passa ao próximo apto. Fechamento de rodada
  continua reduzindo duração dos efeitos. Sem participantes, o Mestre encerra.
- Pins com posição lógica usam largura/altura do footprint do grid. Para 1×1,
  retrato ocupa uma célula; indicadores podem aparecer fora dela. Sem posição
  lógica, preserva apresentação legada.
- Cenas arquiváveis reversivelmente; nenhuma ficha/cena foi deletada.

## Banco operacional

Última cena usada, segundo scene_events: 14, **01 — Retorno e reunião**.
Arquivadas: 4–13 e 15–22. A filtragem da lista exige carregar o novo backend.
Recuperação GM: GET `/gm/scenes/archived`, depois POST
`/gm/scenes/{id}/archive?archived=false`, com autenticação normal.

Backup anterior: pasta temporária `omnisvera-before-table-controls-owskrjga`.
Comparação confirmou preservação de character_states, character_sheets,
character_definition_overrides, character_notes, combat_effects,
combat_effect_clock, session_workspace_tokens, game_sessions e credenciais.

**Reinício não executado:** ferramenta bloqueou o comando antes da execução.
Backend antigo PID 16012 permaneceu em 8787; combate inativo. Frontend foi
compilado, mas código de backend novo ainda não está ativado no processo vivo.
Não há commit ou push deste corte.

## Validação

- Backend completo: 511 testes PASS.
- Frontend: 221 testes PASS; typecheck PASS; build PASS (aviso de bundle >500kB).
- `table-controls-smoke.cjs`: interface compilada em 8871, SQLite descartável;
  aba NPCs, iniciar/finalizar sessão, reload e tamanho dos tokens em desktop,
  zoom e viewport 390×844: PASS.
- A primeira execução do smoke encontrou sessão já ativa na fixture; ajustada
  a preparação. A segunda encontrou mídia ausente no Vault descartável;
  copiada apenas a imagem do Conclave para a fixture. Não era falha de produção.
  A fixture não copia toda a mídia: houve erros ASGI `Imagem indisponível`
  para os demais assets ausentes. O smoke não certifica todas as imagens.
  Servidor descartável 8871 encerrado após os testes.
- Testes incluem morte por ataque, alteração de PV, passagem automática,
  expiração ao fechar rodada e compatibilidade com reanimação.
- Isso não comprova estabilidade de mesa em redes/dispositivos diferentes.
- `table-recovery-smoke.cjs`: PASS em quatro contextos de navegador
  (Mestre + Vezemir/Raziel/Morthak); fichas mobile, reconexão sem reload,
  recuperação de registro perdido e passagem de turno sincronizada.

## Pendências explícitas

- Nível 5 não aplicado: faltam escopo dos personagens e decisão dos PV.
  A progressão atual também tem limites de tabelas e escolhas de habilidades;
  não basta trocar o número do nível.
- Notas de Morthak identificam **Toque Sombrio** e **Aterrorizar**. Não foram
  implementadas neste corte: faltam usos por descanso e a interpretação de
  “testes difíceis” na campanha, que mistura regras revisadas de edições.
  Pergunta enviada ao Mestre; nenhum contador foi inventado.
- Referência consultada para conferir as notas (sem mudar regras da mesa):
  [Toque Sombrio](https://olddragon.com.br/magias/toque-sombrio) e
  [Aterrorizar](https://olddragon.com.br/magias/aterrorizar).
  A duração em turnos de exploração não deve ser convertida silenciosamente
  em rodadas de combate.
- Não declarar todas as habilidades automatizadas: ainda existem riders e
  adjudicações manuais, como a fraqueza a fogo anotada no esqueleto.

## Arquivos deste corte

Backend: `app/battle_mode.py`, `app/character_play.py`, `app/combat.py`,
`app/combat_effects.py`, `app/main.py`, `app/scene_play.py`,
`app/session_workspace.py`, `test_table_cleanup.py`.

Frontend: `src/App.tsx`, `src/api.ts`, `src/pages/CampaignMemoryPage.tsx`,
`src/pages/SessionWorkspace.tsx`, `src/styles.css`,
`tests/campaign-memory.test.cjs`, `tests/table-controls-smoke.cjs`.

Esses arquivos já incluem alterações anteriores no worktree; não atribuir o
diff inteiro a este corte nem fazer staging indiscriminado.
