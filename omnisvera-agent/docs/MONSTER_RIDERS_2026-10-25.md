# Condições de acerto e dano tipado — 25/10/2026

`damage_profiles.py` transporta tipo, origem e material do ataque até o HP
nativo. Bônus de acerto não implica arma mágica. O Mestre confirmou como
mágicas Hemomancia, Grisalma e Adagas de Espectro Fantasma; o cadastro derivado
está em `data/damage_profiles.json`, sem reescrever inventários.
Magias usam elemento declarado ou inferência ofensiva inequívoca. Resistências,
imunidades e vulnerabilidades elementais mapeadas passam por `monster_runtime.damage_response`.
Só a parcela inevitável do 20 natural ignora defesas; o dano real fica no registro.
Imunidade a armas comuns não bloqueia automaticamente todo dano mágico.

`monster_riders.py` preserva a descrição e só cria contrato quando há ataque
associado, JP explícita e dano/duração completos. São 15 condições em 15 criaturas
do catálogo atual: cinco paralisias, petrificação pela bicada da Cocatriz, dois
venenos com dano adicional e sete venenos com prazo até a morte. Não certifica
a ficha inteira de nenhuma criatura.

`monster_conditions.py` roda dentro da confirmação existente: acerto → imunidade
→ JP → dano/condição. Reflexos interceptados não aplicam a condição. Retry da
confirmação reaproveita o recibo; alteração da fonte exige nova resolução.
Paralisia e petrificação bloqueiam ação e movimento sem remover o participante
vivo da iniciativa. Não há segundo sistema de turnos, HP, relógio ou realtime.

As unidades seguem o relógio existente: turno de exploração = 600 s; rodada =
10 s. Não se converte a palavra “turno” da fonte em turno individual de combate.
Petrificação permanente segue até remoção. Encerrar combate/sessão não cura
essas condições; o descanso geral explícito limpa os status dos personagens,
conforme regra da campanha. Prazos de veneno usam o comando de tempo ficcional.
Jogadores recebem a condição e o contador, sem IDs técnicos do monstro de origem.
Mapas privados, fog e ocultação explícita preservam a visibilidade do ledger.

Permanecem assistidos: petrificação por olhar/gás, venenos periódicos ou com
início atrasado, drenos de atributo, sono/falsa morte, exceções complexas a armas,
imunidades genéricas a magia, repertório de magias de monstros e descrições sem parâmetros suficientes. Não
há execução universal de texto nem automação integral dos catálogos.

O OpenCode contribuiu testes adversariais do parser. Integração, revisão e ensaio
visual ficam no fluxo nativo do Companion. `oct24` inclui o novo smoke de condições
com quatro fichas descartáveis, Mestre/Jogador e larguras 1440/390. O d20 do ataque
é controlado no transporte; JP e duração são roladas pelo backend. Isso não prova
entrada de dado físico, celular físico ou redes externas.

O ensaio também encontrou e corrigiu duas colisões com o legado: `vine_turn`
tentava rolar fuga da paralisia, e o fim de combate a apagava junto com Vinhas.
Ambos têm regressão determinística. Os novos status ainda usam ícone genérico.

Arquivos deste corte: módulos acima e `data/damage_profiles.json`; integração em
`combat`, `combat_effects`, `battle_mode`, `spatial_grid`, `session6_rewards`,
`dorn_spells`, `spell_engine`, `schemas`, `main`, `monster_runtime`, `monster_rules`
e `action_cards`. Frontend: `api`, `attackOutcome`, `ActiveEffectIcons`,
`MonsterRules`, `MonsterAttackPanel`, `SummonControls`, `combatActionAvailability`
e `SessionWorkspace`. Testes: `test_damage_profiles`, `test_monster_riders`,
`test_monster_riders_adversarial`, `test_monster_conditions_runtime`,
`monster-conditions.test.cjs`, `monster-conditions-smoke.cjs` e lote `oct24`.

Validação: frontend 412 PASS; typecheck e build PASS (`index-C4uqRz2f.js`).
Ensaio isolado `bsfzq3ng`: cenário API PASS e UI `oct24` PASS em 168,771 s;
capturas 1440/390 revisadas com aceite focal em `conditions-visual-review.json`.
Os flags globais de certificação integral continuam falsos. Nenhuma ficha real
foi usada para executar ações de teste. Backend: 1.407 testes OK, um ignorado.
`git diff --check` limpo. Permanecem avisos legados de fechamento de conexões
nos testes e tamanho de bundle no build.

Ativado no backend 8787 com backup e comparação de 21 tabelas protegidas. A
sessão já marcada ativa e os ajustes reais feitos durante o trabalho foram
preservados; só timestamps dos três mapas oficiais mudaram no startup.
Contratos `native_on_hit`, schema de dano e fichas dos três jogadores/GM Dorn
confirmados por GET. HTTPS público, bundle novo e OpenCode responderam.
Sem staging, commit ou push. Isso não certifica redes externas nem toda a mesa.
