# Hemomancia de Raziel — base aprovada em 17/10/2026

Apresentação revisada por pedido posterior: ativas em Habilidades, passivas em
Poderes vampíricos e armas em Hemomancia. Consulte
`RAZIEL_SHEET_SECTIONS_2026-10-18.md`; a organização inline descrita abaixo é
histórico da primeira apresentação, não o layout atual. Regras v2 preservadas.

Regra da campanha, não transcrição de Old Dragon. Substitui as alternativas
históricas dos dois documentos `*_PROPOSAL.md`. Forma da Noite não muda.

| Arma | Base / alcance | Invocar | Habilidade / custo adicional | Passiva automática |
|---|---|---:|---|---|
| Arco | 1d8 perfurante / 9 m | 1 | Tiro do Coração / 1: +2 no acerto contra Marca Rubra de Raziel | Mira Predatória: 19–20 naturais **que acertem** rolam novamente só o 1d8 base |
| Foice | 1d8 cortante / adjacente | 2 | Ceifa Rubra / 2: causando dano a um alvo com sangue, aplica 1d4 em dois inícios de turno dele | Carrasco: +1d6 se o alvo já tinha até 25% dos PV máximos; desmembramento só como finalização ao matar |
| Marreta | 1d10 contundente / adjacente | 2 | Ruptura Óssea / 1: ignora até 2 RD física, não imunidades | Trauma Profundo: causando dano, deixa Exposto para +2 no próximo ataque hemomântico contra esse alvo |
| Escudo | +2 CA / pessoal / 1 rodada | 2 total | Bastião Carmesim: não usa ataque, inclusive após o ataque do turno | Revanche Rubra: se os +2 CA evitam acerto, guarda +1d6 para o próximo ataque hemomântico; uma carga |
| Lança | 1d8 perfurante / 3 m | 1 | Estocada Transfixante / 1: +1d4 de dano | Ferroada Arterial: +1d6 contra Exposto **ou** sangrando; não dobra por ambas |

Uma arma ofensiva ativa; primeiro ataque com ela inclui invocação, ataques
básicos subsequentes são gratuitos. Trocar paga nova invocação e não concede
ataque extra. Escudo não substitui a arma ofensiva. Reaplicar sangramento renova,
não acumula. Exposto/Revanche são consumidos pelo próximo ataque, inclusive erro.

Card → seleção no grid → Sim/Não → prévia e confirmação nativas automáticas.
Escolher/cancelar não gasta. Confirmar cobra inclusive no erro. Retry recupera o
recibo, sem novos dados/custos. Alcance, mapa, visibilidade, PV, turno, efeitos e
sangue são validados no servidor; confirmação revalida posição e pré-condições.

Armas/skills/passivas são metadados de `app/hemomancy.py`, compostos dentro de
`combat.resolve_attack` / `confirm_attack_resolution`. Sangramento e escudo usam
o ciclo existente em `combat_effects`; mesmas tabelas, ledger e realtime.
Fim de combate/descanso completo limpa arma, sangramento, Exposto e Revanche.
Escudo mantém a expiração por rodada já usada por Sangue Defensivo.

Adagas de Espectro Fantasma continuam item físico; reforço +1d4/ponto permanece
nos ataques de arma equipada. Não herdar melhorias/maestria de itens físicos nas
armas conjuradas; não duplicar modificadores, passivas ou reforço em crítico.
Nenhuma progressão adicional por nível foi inventada.

RD desta primeira integração lê `damage_reduction` inteiro (0–999) e
`damage_immunities` (lista de `physical`, `piercing`, `slashing`, `bludgeoning`)
da ficha persistida do alvo; ausentes significam zero. Não interpreta descrições
livres como RD/imunidade e não reescreve a mitigação dos ataques legados.
Elegibilidade para sangrar reutiliza a regra existente `has_blood`/invocação/
personagem; cadastrar criaturas sem sangue corretamente continua necessário.

Endpoints legados são preservados para recibos/clientes antigos, mas o card
principal oferece só as cinco armas novas. Não há escalonamento novo, ataques
gratuitos, recuperação infinita de sangue nem desmembramento de chefe instantâneo.

Regressões: `backend/test_hemomancy_weapons.py` e
`frontend/tests/hemomancy-weapons.test.cjs`. Teste de código não equivale a
publicação, aceitação visual nem mesa real em redes distintas.

## Validação inicial (17/10, v1)

- 34 regressões de Hemomancia: PASS, incluindo os últimos ajustes de leitura
  imutável, escudo fora do grid, narrativa e orçamento de Velocidade. Lote afetado completo: 80 PASS, com
  ledger, laboratório e schema MCP; inclui projeção HTTP
  privada, crítico sem duplicar modificadores, concorrência, alcance e rollback.
- Frontend: 331 testes PASS, typecheck e build PASS (aviso pré-existente de bundle).
- Ensaio CLI geral isolado: 79 API PASS, 3 EXPECTED_BLOCK. Layout das quatro fichas
  PASS; o lote visual geral seguinte excedeu seu teto, portanto INCONCLUSIVE.
- Ensaio focal após corrigir o DTO: quatro API PASS; seis ativações das cinco
  armas pela UI PASS, desktop/390 px, cancelamento, custo, reload e segunda página
  local. Capturas revisadas; ícones legados ausentes na fixture não certificam mídia.
  Execução final `omnisvera-sheet-test-cyom8e11`: dois blocos fixos de três casos,
  ambos PASS (155,837 s e 211,100 s). Uma tentativa monolítica anterior excedeu
  300 s; o lote foi dividido, sem aumentar o teto nem retirar casos.
- Regressão geral: 1.054 testes OK, 1 ignorado. Depois, o lote afetado foi repetido
  nos ajustes locais finais (80 PASS). A corrida de migração do ledger encontrada
  na primeira execução foi corrigida com `BEGIN IMMEDIATE` antes de verificar colunas.
- Runtime operacional: ATIVADO em 17/10/2026. Backup de 27 tabelas, banco e
  acessos em `backend/data/backups/pre-hemomancy-20261017-181810`, sem combate
  ativo. A tentativa de reiniciar somente o backend foi rejeitada pela política
  da ferramenta antes da execução. Depois de o operador fechar o PowerShell,
  confirmou-se ausência de backend local e iniciou-se apenas o backend, em
  segundo plano, sem encerrar processos nem tocar Tailscale/OpenCode. PID servidor
  245244 (lançador 233984). Health, quatro fichas e endereço público HTTP 200;
  DTO de Raziel confirma `raziel-five-weapons-v1` e as cinco armas, bundle novo
  servido. Configurações e tokens iguais ao backup. Comparação inicial do estado:
  só timestamps `updated_at` dos mapas/workspace e `last_seen_at` da presença
  mudaram, sem linhas adicionadas/removidas nem alteração dos dados de jogo.
  Nenhuma ação de combate foi disparada no operacional. Acesso público deste
  computador não certifica mesa real em redes distintas.

## Clareza da ficha e Estocada (18/10, v2)

O prosseguimento aprovado aplica +1d4 exclusivamente ao acerto da Estocada,
sem mudar custo, alcance ou ataque básico. O d4 é registrado separadamente e
compõe a fórmula/total nativos; Ferroada continua no máximo +1d6 contra Exposto
ou sangrando, mais o bônus plano de Exposto quando existir. Erro gasta o custo
normal, sem dados de dano; preview/cancelamento não gastam e retry não rerrola.
Revisão `raziel-five-weapons-v2`: comandos novos de cliente v1 são rejeitados
pedindo atualização; recibos existentes continuam recuperáveis, sem nova cobrança.

A ficha mostra nome e efeito da habilidade e da passiva automática sem abrir
modal, inclusive quando o seletor está em ataque básico. Arma/ação ocupam duas
colunas; permanece um único comando de uso e a seleção de alvo nativa no grid.
O texto é somente informativo, sem novos botões de ativação de passivas.

Regressões focais: 39 backend e 5 frontend PASS. Suíte frontend final:
332 PASS; typecheck/build PASS (aviso pré-existente de bundle). A tentativa de
suíte geral no observer foi interrompida sem resultado final; não é PASS.
No runtime nativo, 1.057 entradas: 1.053 PASS, dois erros de dependência MCP e
dois skips. Os dois erros e o skip MCP foram repetidos no observer: 13 testes
PASS (11 do módulo que não pôde importar, um contrato de lote e um schema).
Cobertura combinada: 1.066 testes PASS; resta um skip de symlink por privilégio
do Windows. A execução nativa sozinha não é declarada PASS.

Primeiro ensaio UI `8mo76h6z`: quatro API PASS, primeiro bloco UI PASS; segundo
FAIL no alinhamento dos seletores. A ordem dos elementos foi corrigida e o build
refeito. Ensaio final `zx8o32tz`, com o produto congelado durante a execução:
quatro API PASS e dois blocos UI PASS (139,840 s / 89,704 s), seis ativações nas
cinco armas. Inclui leitura de passiva sem ativar, alinhamento dos seletores,
cancelamento/custo, fórmula da Estocada, reload e segundo cliente local.
Capturas desktop/390 px revisadas explicitamente. Alguns ícones legados de
ataques não carregam na fixture; não certifica toda mídia nem celular físico.
O assert de dano do smoke também trata erro natural sem esperar dados de dano;
o acerto com 1d4 foi observado no ensaio final e o erro é regressão de backend.

V2 ATIVADA: backup fresco `pre-activate-hemomancy-v2-20261018-222217`, combate
inativo, apenas backend reiniciado (servidor 244196, lançador 242224). Health,
quatro fichas, jogador Raziel e endereço público HTTP 200. Outro jogador não
recebe o pacote privado. Runtime confirma revisão v2 e `bonus_damage=1d4` da
Estocada; bundle novo servido. Tokens/configurações iguais ao backup. Nas 27
tabelas protegidas, apenas `updated_at` dos mapas mudou, sem alteração dos dados
de jogo ou linhas. Não houve casts operacionais nem alteração de outros serviços.

Balanceamento verificado aqui é custo/combinações/dano da regra aprovada;
não é certificação de equilíbrio entre classes numa mesa real ou redes distintas.

Arquivos alterados nesta atualização: `backend/app/hemomancy.py`, `app/combat.py`,
`backend/test_hemomancy_weapons.py`, `frontend/src/pages/SessionWorkspace.tsx`,
`components/HemomancyWeaponDetails.tsx`, `companionTheme.css`,
`frontend/tests/hemomancy-weapons.test.cjs`, `hemomancy-weapons-smoke.cjs`,
este documento e `CURRENT_COMPANION_CODE.md`. Nada de staging, commit ou push.

## Arquivos deste corte

- Backend: `app/hemomancy.py`, `combat.py`, `combat_effects.py`, `battle_mode.py`,
  `character_play.py`, `main.py`, `schemas.py`, `session_ledger.py`, `test_run_evidence.py`.
- Ferramentas: `backend/scripts/run_sheet_test.py`, `companion_test_mcp.py`, `agent_test_jobs.py`.
- UI: `frontend/src/api.ts`, `pages/SessionWorkspace.tsx`,
  `components/HemomancyCard.tsx`, `components/hemomancySelection.ts`,
  `components/HemomancyWeaponDetails.tsx`, `companionTheme.css`.
- Testes: `backend/test_hemomancy_weapons.py`, `test_session_ledger.py`,
  `test_sheet_runner_batches.py`, `test_test_run_evidence.py`;
  `frontend/tests/hemomancy-weapons.test.cjs`, `hemomancy-weapons-smoke.cjs`,
  `hemomancy-weapons-second-smoke.cjs`.
- Docs: este arquivo, `CURRENT_COMPANION_CODE.md`, `AI_TEST_TOOLS.md` e os dois
  documentos históricos `RAZIEL_*_PROPOSAL.md` (somente aviso de substituição).

Mudanças anteriores do worktree preservadas. Sem staging, commit ou push.
