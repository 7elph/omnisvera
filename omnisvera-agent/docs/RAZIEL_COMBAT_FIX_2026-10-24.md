# Ajustes de combate aprovados — 24/10

## Regras

- Reserva de Sangue: máximo 20, preservando pontos já gastos ao migrar.
- Invocar/trocar arma ou usar habilidade hemomântica custa 1; o primeiro uso
  da habilidade não soma outro custo de invocação. Ataque básico com a arma
  já ativa continua gratuito. Escudo: custo total 1, +2 CA/uma rodada.
- BA base de Raziel: mínimo +6; equipamentos/efeitos continuam separados.
  Isso não concede seis ataques nem aumenta o orçamento de ações.
- Carrasco: +1d6 somente se o alvo já estiver com até 25% dos PV máximos.
- Ceifa: acerto que causa dano em alvo com sangue aplica sangramento de 1d4
  antes de cada um dos próximos dois turnos do alvo, sem acumular.
- Jogadores: 20 natural acerta independentemente da CA; seu dano não é
  desviado por Reflexos nem mitigado pelas resistências hemomânticas.
- Crítico multiplica apenas os dados base: Grisalma x3, Arco de Sangue x2
  em 19–20 que acertem; demais armas usam sua tabela local, padrão x2 no 20.
  Não multiplica bônus fixos, dados de reforço de sangue ou passivas.
- No 1 natural, o jogador recebe o dano da fórmula da própria arma/ataque,
  sem aplicar procs de acerto. Só ocorre na confirmação nativa; retry não repete.

## Interface e mapa

Hemomancia dividida em seleção e ícone da arma ativa; projeção da arma no
ataque corpo a corpo/à distância correspondente. Painel compacto de combate
recolhido por padrão. Resultado longo de Relâmpago fica no registro.

Reflexos desenha cópias translúcidas de Dorn, derivadas da quantidade de
imagens ativa. Não são novas criaturas, não ocupam células nem recebem turnos.
Teia desenha a área usando grid/escala atuais; ocupação usa PV vivos da ficha
em vez do PV antigo do pin. Efeitos públicos são projeções mínimas, restritas
ao mapa e pins visíveis, sem dados privados do Mestre.

## Código principal

Backend: `critical_rules.py`, `combat.py`, `hemomancy.py`, `character_play.py`,
`dorn_spell_pack.py`, `action_cards.py`, `main.py`, `raziel_action_contracts.py`,
`sheet_action_inventory.py`, `approved_resource_limits.py` e catálogos JSON.

Frontend: `HemomancyCard`, `HemomancyWeaponIcon`, `hemomancySelection`,
`CombatEncounterPanel`, `MapSpellEffects`, `SessionWorkspace`, `api`,
`attackOutcome` e `companionTheme.css`.

Regressões novas em `test_table_balance_oct24.py`, `test_effect_map_scope.py`,
`test_active_effect_visibility.py` e `table-balance-oct24.test.cjs`.
Fixtures antigas foram atualizadas para os custos/críticos aprovados.

Ensaio focal nativo: `ui_suite=oct24`, quatro atores, um script fixo em
TEMP/8871. Usa o executor/isolamento/limites existentes, não cria outro serviço.
Um 15 físico controlado é injetado no transporte da Ceifa para observar o
gatilho de 25%; isso não certifica entrada de dado físico pela interface.

## Validação / ativação

- Backend completo: 1270 testes, OK, um ignorado. Mais nove testes focais
  após acrescentar as provas de imunidade/retry e limite 25%/26%.
- Frontend: 403 testes completos passaram; dez testes focais de resultado/cards
  passaram após acrescentar a identificação legível de crítico. Typecheck e
  build finais OK; permanece o aviso de chunks grandes do Vite.
- Ensaio nativo: quatro fichas, API 1/1, `ui_smoke=PASS`, 49,6 segundos no
  navegador. Duas capturas revisadas: card de Raziel a 390 px e mapa de
  Reflexos/Teia a 1440 px. Evidência privada em
  `TEMP/omnisvera-sheet-test-lfqel5r3`; não é recibo MCP anexável nem certificação
  de todas as ações. O armazenamento MCP existente não foi apagado/ampliado.
- Backend ativado com backup `TEMP/omni-oct24-activation-2v9scse8/before.sqlite3`.
  Verificação de 21 tabelas: somente a reserva aprovada de Raziel e timestamps
  dos mapas oficiais mudaram. Nenhuma ficha foi usada para combate de teste.
- HTTP público: página e fichas de Vezemir/Raziel/Morthak 200; os quatro perfis
  ativos (incluindo convidado) autenticam. Raziel: reserva 20/20, pacote v3,
  BA base +6 e BA equipado +8. Frontend público corresponde ao build final.
- OpenCode: health autenticado saudável, versão 1.18.32. Não foi reiniciado,
  reconfigurado nem recebeu nova tarefa neste corte.

Não há comprovação de mesa em redes distintas ou celular físico neste corte.
Reflexos são imagens derivadas, não pins independentes selecionáveis.
Sem staging, commit ou push; alterações preexistentes do checkout preservadas.
