# Corte de combate e preparação — 24/10

## Regras aprovadas

- Raziel: reserva máxima 10, preservando gasto existente. Reforço x2/x3 custa
  2/3 de sangue, multiplica BA e dano (não d20, PV, CA ou atributos) durante
  dois turnos próprios. x1 cancela sem reembolso. Velocidade usa a base já
  existente da campanha: 1d4 + nível rodadas, +1 ataque, movimento x2, +2 CA,
  um uso por descanso diário.
- Marca Rubra: alcance 9 m, centro em inimigo vivo com sangue, inclusive com
  PV cheios; cruz com centro + quatro células cardinais. Custa 1 pela área
  inteira. Mantém fog, mapa e posições lógicas autoritativos. A cruz tem três
  células em cada eixo; corresponde a 4,5 m com escala de 1,5 m/célula.
- Feridas: Marreta aplica Exposto; Ceifa aplica sangramento por dois turnos
  do alvo; Lança recebe +1d6 por condição (+2d6 com ambas) e consome Exposto.
  Carrasco continua exigindo alvo com até 25% dos PV antes do acerto.
- Marca: Tiro contra marcado prepara Revanche ao ativar Escudo. Completar os
  dois blocos libera Convergência uma vez por combate: +2 BA e +1d6 no próximo
  ataque confirmado, consumida mesmo se errar. As passivas usam efeitos e o
  relógio de combate existentes, sem sistema paralelo de turnos.
- Vezemir: a resistência condicional é consumida somente ao alcançar zero PV
  durante Frenesi. Continua apto com PV negativos enquanto ela está ativa;
  em −10 fica incapacitado. Um uso diário. Provocação aplica −2 à JP e garante
  ao menos o primeiro turno obrigatório após falha.
- Dorn: Guarda sem seleção individual protege aliados a até 9 m no mapa do
  combate. Ataques são redirecionados para Dorn, que recebe metade do dano,
  arredondada para baixo. Expira no próximo turno de Dorn. Efeitos/recibos
  legados de Guarda individual continuam legíveis e o payload antigo é aceito.
- Guarda e Relâmpago começam disponíveis em cada combate. Um d6 no início do
  turno de Dorn recarrega os recursos esgotados com 5–6, sem rerrolar em retry.
  Relâmpago divide a rolagem entre 1–3 alvos **antes** da JP; restos vão aos
  primeiros alvos selecionados e uma resistência divide sua parte por dois.
- Reflexos intercepta 90% dos ataques elegíveis; cada interceptação consome
  uma imagem. Área e 20 natural inevitável de jogadores mantêm as exceções.
  As imagens no mapa derivam do efeito, sem turnos independentes.

## Interface e infraestrutura

Status com duração conhecida mostram turnos no canto inferior direito. Não
há conversão inventada de segundos fictícios em rodadas. PV têm ajuste ao
lado da barra. Reforço tem x1/x2/x3 e as passivas estão em dois grupos.

Cenas permite selecionar mapa, pins e elementos nativos e confirmar o envio
à Mesa, numa transação com recibo e ledger. Cancelar não publica. A seleção
não publica descrições privadas, notas ou objetivos do Mestre. Capa/abertura
continuam disponíveis pela publicação integral já existente. Fog é preservada.

Movimentos do bestiário são separados em caminhada, voo, natação, escalada e
escavação. O modo escolhido usa um único orçamento; não pode ser trocado após
gastar movimento no turno. Sem altura, paredes, cobertura ou pathfinding.
Notação V/N/E/C: [SRD oficial OD2](https://olddragon.com.br/livros/srd/capitulos/monstros-a-d).

## Evidência da mesa e limites

O ledger consultado registra Ceifa seguida de dois ticks de sangramento e
Provocação que foi resistida no turno seguinte. A ausência de uma ação no
ledger não prova qual erro HTTP ou interação ocorreu no cliente.

O inventário determinístico cobre 255 monstros, 854 magias e 326 itens; ver
`CATALOG_READINESS_2026-10-24.md`. Isso **não certifica automação integral**.
O Dragão Dourado tem baforada 11d10, cone de 27 m e três usos diários na fonte;
a geometria/custos completos ainda exigem adaptador próprio. Conjurar como
Mago 7 não informa repertório: não foram inventadas magias conhecidas.
Estoque ampliado de outros comerciantes, todos os ícones ausentes e execução
de todas as famílias de magia permanecem trabalhos separados.

Três fundos reutilizáveis foram cadastrados privados, sem trocar o mapa ativo;
ver `BATTLE_LIBRARY_ART_2026-10-24.md`. Nenhum push ou commit neste corte.

## Validação

- Backend: 1.322 testes executados, sem falhas, um ignorado; regressões focadas
  de movimento, pipeline, seleção de cenas e Relâmpago também passaram após os
  últimos ajustes. Frontend: 406 testes; mais 19 checks de cenas após a correção
  de privacidade; typecheck, build e `diff --check` aprovados.
- Ensaio nativo: 91 cenários inicialmente (73 PASS, 16 FAIL, dois bloqueios
  esperados). Foram corrigidos o parser de gerúndios de movimento e as expectativas
  antigas de custos/drenagem/Guarda do ensaio. Os 16 casos repetidos passaram.
  A bateria final teve um cenário API e UI com os quatro atores, a 390/1440 px:
  PASS. d20 15 foi injetado no transporte; não houve dado humano.
- Capturas revisadas: Hemomancia, multiplicador, PV lateral, Reflexos/Teia e
  seleção/cancelamento de cena. Recibo explícito de revisão em TEMP:
  `omni-oct24-ui-yHyLAq/codex-visual-review.json`. O relatório bruto mantém o
  marcador antigo de revisão pendente e o agregador antigo `grid_actions=false`;
  o recibo e o log do script registram a interação efetivamente exercitada.
- O MCP do OpenCode respondeu ao start, mas atingiu o limite de histórico de
  jobs. Histórico preservado; foi usado o mesmo runner nativo pela CLI. Não
  alteramos o conector nem seus limites para contornar a proteção.
- Backend ativado com backup em `omni-oct24-activation-zzlgqptv/before.sqlite3`
  (TEMP). Autenticação inalterada e 21 tabelas protegidas comparadas. Mudanças
  operacionais limitadas à reserva 10/10, Velocidade diária e timestamps dos
  mapas oficiais na inicialização. PV, itens, sessão e combate preservados.
- Página pública e fichas autenticadas de Vezemir/Raziel/Morthak: HTTP 200.
  OpenCode autenticado saudável. Três imagens da biblioteca: HTTP 200.
  Nenhuma prova de mesa humana em redes distintas; não é certificação integral
  de fichas, catálogos ou estabilidade prolongada.

## Arquivos do corte

- Combate: `raziel_pipeline.py`, `hemomancy.py`, `combat.py`, `combat_effects.py`,
  `vezemir_skills.py`, `dorn_protocols.py`, `dorn_recharge.py`, `dorn_spells.py`,
  `dorn_spell_pack.py`, `action_contract.py`, `action_library.py`.
- API/dados: `main.py`, `schemas.py`, `character_play.py`, `native_action_manifest.py`,
  `approved_resource_limits.py`, `data/session_abilities.json`,
  `data/raziel_vampire_powers.json`, `session_workspace.py`, `spatial_grid.py`,
  `spatial_routes.py`, `monster_movement.py`, `catalog_readiness.py`, `scene_play.py`,
  `scene_selection.py` (todos em `backend/app/`).
- Frontend: `api.ts`, `pages/SessionWorkspace.tsx`, `pages/ScenePanel.tsx`,
  `scenePreparation.ts`, `companionTheme.css`; componentes `BloodReinforcement`,
  `TargetingOverlay`, `DornProtocolControls`, `MonsterAttackPanel`,
  `ActiveEffectIcons`, `ScenePreparationGallery`, `hemomancySelection` e CSS da galeria.
- Cobertura: testes focados novos `test_raziel_pipeline_oct24`, `test_guard_area_oct24`,
  `test_movement_modes_oct24`, `test_scene_selection_oct24`, `test_dorn_campaign_oct24`,
  `test_frenzy_oct24`, catálogos/movimentos, testes existentes ajustados às regras
  aprovadas e `backend/scripts/all_actions_simulation.py`. UI em
  `frontend/tests/table-balance-oct24-smoke.cjs` e regressões correspondentes.
- Arte/documentação: três PNGs da biblioteca e os três documentos deste corte.
  Helpers e recibos privados ficam em `.autonomy/runtime/` e TEMP; sem staging,
  commit ou push e sem incluir bancos, tokens ou logs em Git.
