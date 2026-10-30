# Reparos de combate — 13/10/2026

## Regras aprovadas e implementadas

- **Pulseira de Vinhas:** utiliza o orçamento existente de um consumível por turno, não a ação de ataque. Pode ser usada antes ou depois do ataque; dois consumíveis no mesmo turno continuam proibidos.
- **Escuridão:** regra de campanha substitui cegueira por imobilização. Reutiliza o motor das vinhas: JP ao entrar no turno do alvo, falha passa o turno, sucesso libera a ação, máximo de três turnos individuais. Encerrar combate/sessão limpa a imobilização. Efeitos antigos de Escuridão são convertidos uma vez, sem gastar recurso ou alterar PV.
- **Cadáver:** pin derrotado continua visível como ☠, sem retrato original e fora do circuito de turnos. Animar Mortos exige um cadáver válido e não consumido, usa o orçamento nativo e cria um pin separado. Constructos, mortos-vivos e summons não são cadáveres elegíveis automaticamente; veto explícito do Mestre permanece válido.
- **Diagonal:** dois aliados adjacentes na diagonal OU flanqueamento em diagonais opostas do alvo concedem +2 no ataque, nunca +4. Apenas participantes vivos, com posição lógica e tamanho 1×1. Não concede bônus a magia de acerto automático. Movimento/morte retira o bônus; confirmação rejeita prévia espacial desatualizada.
- **1 natural:** sempre falha; 20 natural acerta. Correção localizada de acerto, sem mudar dano crítico. Referência: [SRD oficial de Old Dragon — combate](https://olddragon.com.br/livros/srd/capitulos/combate).
- **Vezemir:** Visão no escuro, Detecção de portas escondidas e Descanso élfico aparecem como passivas, sem alterar atributos ou trocar a raça persistida.
- **Morthak:** Necromante restaurado pela rota nativa do Mestre, mediante autorização expressa; PV preservados.

## Uso na mesa

1. Inicie um combate no mapa com grid e selecione os participantes.
2. Vezemir equipa a pulseira, escolhe o alvo e usa; o ataque continua disponível.
3. Ao passar para o turno de um alvo imobilizado, a JP e suas consequências entram no registro.
4. Morthak escolhe o cadáver em **Animar Mortos** e usa. O corpo não pode ser reutilizado por outro clique/retry.
5. Posicione aliados nas diagonais: o pin mostra +2 e o cálculo de ataque inclui o bônus.

## Limites explícitos

- Visão no escuro não remove o fog do Mestre automaticamente. Portas secretas ainda exigem adjudicação/teste; não existe sistema espacial de portas/visão neste corte.
- Descanso élfico registra metade da duração. O descanso atual é um comando do Mestre, sem cronômetro de horas ficcionais novo.
- Sem paredes, linha de visão, iluminação ou obstáculos novos.
- Ensaio isolado de navegador não comprova estabilidade numa mesa real com jogadores em redes distintas.
- Relatórios anteriores que falharam permanecem evidência histórica, não são apagados nem tratados como PASS.

## Validação

Evidência gerada somente em TEMP; nenhum banco, token, log ou captura deve entrar em commit.

- Backend: **678 testes, OK** no ambiente `.venv-observer` já existente. A tentativa pelo venv do backend falhou ao importar o teste do adapter externo por falta de MCP; não foi ocultada nem corrigida instalando dependências em produção.
- Frontend: **251 testes, PASS**; typecheck e build passaram. Avisos preexistentes de bundle grande e conexões SQLite não fechadas nos testes permanecem.
- MCP `test-a821af10262c4607adad9e140ad47f8d`: **72 PASS, 1 EXPECTED_BLOCK**, sem FAIL; `report.ui_smoke.status=PASS`, com fichas desktop/mobile e botões físicos dos quatro atores.
- Smoke adicional de navegador: Vinhas seguido de ataque, cadáver sem retrato, pin novo ao reanimar, +2 diagonal, passivas e reload passaram. Capturas inspecionadas; imagens ausentes na fixture não certificam mídia operacional.
- Ensaio anterior encontrou erro de 1 natural, expectativa desatualizada do bônus Faro e Necromante ausente. Esses pontos foram corrigidos antes do novo ensaio; o relatório antigo permanece no TEMP.
- Backend 8787 reiniciado pelo lançador oficial após backup. Fichas, PV/recursos, inventário, posições lógicas e encontro preservados. Mapas tiveram apenas timestamps atualizados; presença/scroll mudaram com os clientes conectados.
- A Escuridão antiga cujo alvo não era mais válido foi desativada; versão do relógio e auditoria foram atualizadas pela migração idempotente.
- Tokens e configuração Cloudflare permaneceram equivalentes ao backup. Sem commit nem push.
- Funnel 443 reativado com autorização específica, mesmo endereço e demais portas intactas. Houve falha TLS inicial, inclusive após reativação; posteriormente ambos os relays públicos responderam **200 com TLS padrão**, e as fichas de Morthak, Vezemir e Raziel responderam **200 com seus acessos próprios pela rota pública**, certificado validado. Isso comprova a rota naquele momento, não estabilidade de uma mesa com celulares/redes distintas.

## Arquivos deste corte

Backend: `app/battle_mode.py`, `app/session6_rewards.py`, `app/session_workspace.py`, `app/summons.py`, `app/dorn_spells.py`, `app/combat_effects.py`, `app/spatial_grid.py`, `app/combat.py`, `app/character_play.py`, `app/main.py`, `app/data/dorn7_mage3.json`.

Ensaios backend: `scripts/all_actions_simulation.py`, `scripts/run_sheet_test.py`, `test_session6_rewards.py`, `test_battlefield_extensions.py`, `test_dorn_spells.py`, `test_dorn_sheet.py`, `test_session6_combat.py`.

Frontend: `src/api.ts`, `src/pages/SessionWorkspace.tsx`, `src/components/VineBraceletControl.tsx`, `src/components/DornSpellControls.tsx`, `src/components/DornSpellEffects.tsx`, `src/components/mapManagement.css`, `tests/battlefield-extensions.test.cjs`, `tests/battlefield-smoke.cjs`.

Documentação: este arquivo. Alterações anteriores no worktree misto preservadas.
