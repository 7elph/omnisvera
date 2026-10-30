# Fichas — pacote aprovado em 13/10

Este corte não certifica toda a ficha nem uma mesa em redes distintas. Não houve commit,
push, troca de tokens nem descanso operacional concedido pelo ensaio.

## Entregue

- Raça e classe abrem detalhe flutuante; imagem vem do índice existente do
  Vault quando disponível. Especialização ocupa campo compacto próprio e os
  benefícios/controles ficam dentro do detalhe, sem texto expandido na ficha.
- Maestria é passiva da arma escolhida/equipada; não possui botão Usar.
- Vezemir: BA 10 = nível 5 + FOR efetiva +2 + Grisalma +2 + maestria +1.
  CA operacional 22, corrigida pela edição nativa: base 20 + melhoria +2 da
  Muralha. Não foram alterados FOR, PV, inventário de armas ou nível.
- Frenesi: +2 FOR, 1d4+1 rodadas, um uso manual diário. A ativação automática
  abaixo de metade dos PV tem contador diário separado e não gasta o manual.
  A primeira ativação diária concede sobrevivência até -9 PV enquanto ativa;
  -10 PV ou expiração derruba, retira da iniciativa e deixa o cadáver.
- Provocação: um uso diário; raio 1d4 + quantidade de inimigos em metros.
  JP normal no início do turno de cada alvo; falha restringe ataques a Vezemir.
  Cada alvo vivo afetado reduz RD em 1 (sem RD-base positiva cadastrada, essa
  penalidade aumenta o dano recebido em 1). Matar alvo provocado durante
  Frenesi restitui o uso de Provocação, sem duplicação por retry.
- Toque Sombrio: ataque adjacente 1d4; Digital confirma e aplica pelo comando
  nativo. No início dos turnos seguintes, 1–3 em 1d6 causa perda de 1 PV.
  Não drena FOR e não faz a antiga JPC. Zero PV mata; encerra com a morte ou
  fim do combate. Físico preserva d20 declarado e prévia/confirmar.
- Aterrorizar: raio 9+3/nível pelo grid; criaturas com menos de 2 DV, JPS nega.
  Duração 1d6+nível turnos individuais; -2 d20 em ataques, atributos, JP e
  perícias projetados na ficha. Não reduz atributos. Efeitos novos não são
  envelhecidos pelo relógio manual de exploração; legados preservam seu relógio.
- Ataque à distância de Morthak reaparece, sem esconder a Adaga de Osso.
  Ataque genérico sem arma equipada permanece bloqueado: não inventamos dano.
- Cinco imagens fornecidas foram copiadas para `frontend/public/companion-assets`.
- Um Fragmento de Cristal Arcano foi entregue nativamente a Morthak. A Essência
  de Mana e o cristal de Dorn não foram consumidos.

## Uso

Na ficha, clicar no nome de raça, classe ou especialização abre a descrição.
Frenesi/Provocação ficam em Habilidades. Para Toque, abrir Preparar magia,
selecionar o alvo adjacente e Conjurar. Aterrorizar seleciona alvos pelo backend,
no combate com grid; não requer informar distância/DV ou rolar JPs manualmente.
Quando o uso diário já foi gasto, o consumo extra de slot continua explícito.

Clonagem: Preparar magia → Conjurar. Exige o fragmento consumível (entregue uma
vez). No combate, conclui no próximo turno de Morthak: até duas cópias em
células livres até 10 m, com 25% dos PV máximos, movimento normal e ataque
básico sem melhorias mágicas. Clones usam a ficha do pin e a iniciativa nativa,
sem magias/itens. Duração de cinco rodadas; zero PV remove a cópia, zero PV
do conjurador ou Encerrar concentração remove o grupo. Nenhum teste de
concentração por dano foi inventado. Fora do combate, a rodada de execução é
ficcional e concluída pelo comando; a duração não é relógio real. Um grupo
por vez; esqueleto e reanimado continuam independentes. A progressão por
círculo 5–9 permite 2–6 clones; não confundir círculo com nível do personagem.

Magia da Morte: Preparar magia → Conjurar. Backend seleciona por proximidade,
rola 2d6 e JPC, mata em falha e reduz PV atuais de Morthak a 10%, arredondados
para baixo (36→3). Raio 3+nível em metros, DV≤4; exige DV/JP cadastrados e grid.
Segue literalmente "criaturas", incluindo aliados elegíveis, com aviso na
ficha. O Mestre ainda pode aprovar restringir a inimigos; isso não foi presumido.
As duas magias são exceções aprovadas ao nível 5, com um uso por descanso diário,
sem emprestar slots de primeiro círculo e sem refazer fichas/PV.

Dorn: seis magias visíveis — Mísseis, Reflexos, Teia, Força Arcana, Relâmpago,
Dissipar. Quatro novas preparações independentes, uma cada por descanso,
preservando usos gastos das antigas. Levitação/Escuridão deixam a seleção
preparada; seus recursos históricos/efeitos não são apagados. Protocolos e
Reparo permanecem. Reflexos resolve automaticamente cada acerto confirmado,
sem duplicar por retry e sem desviar dano de área. Força usa FOR original,
excluindo bônus mágicos/itens e exige toque no grid. Teia usa a célula do pin
selecionado como canto inicial do chão 3×3 m, altura 6 m: dentro, CA−2,
JP de DES−2 e cada passo custa três vezes o normal. Sair remove as penalidades.
Dissipar seleciona efeito arcano cadastrado: d20+nível contra
5+círculo+nível de origem. Reflexos/Força duram (1d6+nível)×10 min ficcionais;
Teia 1 h+10 min/nível. Rodadas avançam 10 s; exploração usa o controle de tempo
do Mestre, sem confundir turno de exploração com rodada.

Fonte de Dorn consultada/renderizada: `old-dragon-livro-basico-aprimorado-biblioteca-elfica.pdf`,
pp.103,107,122,126. Não foi copiado código externo nem alterado o PDF/Vault.

## Provas

- Fechamento desta continuação: backend completo 714 PASS; frontend 255 PASS;
  typecheck/build PASS; diff --check limpo. Vite avisou chunks acima de 500 kB.
  Testes incluem execução/expiração de clones, componente e replay, custo real
  de PV apesar de temporários, coexistência das três invocações, término de
  combate sem bloquear conjuração externa, Reflexos/Teia/Força/Dissipar.
- MCP `test-6fc7a0df440a4388b4a832679d918b7e`: 70 PASS, 2 EXPECTED_BLOCK
  (ataques ranged sem arma equipada de Vezemir/Morthak). `ui_smoke=PASS`:
  Mestre/proprietário, desktop/mobile, botões físicos e atualização multicliente
  local. Capturas das fichas inspecionadas; a fixture não tem toda a mídia do Vault.
- Teste RED adicional reproduziu mutação do payload de Aterrorizar no retry;
  corrigido usando cópias locais das declarações, sem modificar a requisição.
- Backend iniciado pelo lançador oficial depois do backup privado
  `backend/data/backups/resume-oct13-20261013-064416`. Health autenticado 200;
  fichas de Morthak/Vezemir/Raziel 200 com acessos próprios no HTTPS público.
- PV e usos existentes, JSON do combate e credenciais conferidos contra backup.
  O ensaio não concedeu cura, descanso ou reposição de recursos da sessão real.
- Ensaio completo `test-d5e3c3dc3dc84cf58451d7d128a9d011`: 70 PASS,
  2 EXPECTED_BLOCK; duas aceitações visuais PASS, mas Clonagem no novo smoke
  FALHOU porque o orçamento do combate encerrado ainda bloqueava a conjuração.
  Falha preservada no relatório, reproduzida em testes e corrigida também para
  Reflexos. Não declarar esse primeiro ensaio integralmente PASS.
- Repetição MCP `test-91e4f516c9b74570803e66463e3802b6`: quatro cenários de API
  selecionados PASS, `ui_smoke=PASS` nos três scripts. Inclui botões físicos,
  Clonagem pela ficha do proprietário, spawn/end nativos, grid, persistência
  após reload, segundo cliente local, seis cards de Dorn e Reflexos pela UI
  mobile. Capturas de Vezemir e Clonagem inspecionadas; mídia ausente na fixture
  não equivale a certificação da biblioteca inteira.
- Ativação: backup privado `backend/data/backups/activate-approved-spells-20261013-083523`;
  manutenção explícita auditada de Morthak/Dorn e restart oficial somente do
  backend 8787 (PID 39352). Health 200, build servido `index-CfJqAOiN.js`.
  HTTPS público e fichas próprias de Morthak/Vezemir/Raziel retornaram 200;
  acesso `owner` conferido sem expor tokens. CA de Vezemir 22 / BA 10.
  PV preservados: Vezemir 42/47, Morthak 7/13, Raziel 22/22, Dorn 17/35.
  Estado do combate/efeitos, inventário, credenciais e TODOS os recursos antigos
  comparados ao backup e iguais. Só seis recursos novos autorizados foram
  adicionados, com um uso cada; o fragmento não foi entregue novamente.

## Limites explícitos

- Dissipar exige círculo/nível de origem no efeito. Não supõe origem de efeitos
  antigos incompletos nem implementa supressão temporária de itens mágicos.
- Relâmpago mantém a declaração existente de área/contatos: sem paredes ou
  reflexão geométrica automática. Não foi criado motor de áreas paralelo.
- Medo é respeitado nas JPs de Provocação, Vinhas, Dorn e Necromante, além da
  projeção da ficha; outros subsistemas ainda não têm auditoria exaustiva.
- Criatura sem DV/JP não ganha valores inventados. A magia informa o cadastro
  ausente. Não há teste de concentração por dano sem regra aprovada.
- Magias novas sem imagem específica usam o ícone de fallback; não afirmamos
  ter gerado arte por IA. As cinco artes fornecidas de Vezemir estão presentes.
- Endurance de mesa real, celulares físicos e redes distintas não foi comprovada.

## Arquivos desta retomada

Backend: `app/character_play.py`, `app/data/spell_images.json`, `app/main.py`,
`app/schemas.py`, `app/battle_mode.py`, `app/combat.py`, `app/combat_effects.py`,
`app/necromancer_spells.py`, `app/vezemir_skills.py`, `app/session_workspace.py`,
`app/spatial_grid.py`, `app/level_advancement.py`.

Testes backend: `test_sheet_revision_oct13.py`, `test_approved_combat_skills.py`,
`test_necromancer_integrity.py`, `test_session8_necromancer.py`,
`test_morthak_sheet.py`, `test_vezemir_sheet.py`.

Frontend: `src/api.ts`, `src/actionReference.ts`, `src/styles.css`,
`src/components/SheetDetail.tsx`, `SpecializationSection.tsx`,
`NecromancerSpellControls.tsx`, `NecromancerEffects.tsx`,
`combatActionAvailability.ts`, `src/pages/SessionWorkspace.tsx`,
`src/pages/PlayableCharacterSheet.tsx`, cinco assets em `public/companion-assets`.

Testes frontend: `specialization.test.cjs`, `sheet-combat-readiness-smoke.cjs`,
`necromancer-spells.test.cjs`, `combat-simulation-physical-smoke.cjs`,
`sheet-standard.test.cjs`. Alterações anteriores do worktree misto preservadas.

Continuação: `backend/app/morthak_high_spells.py`, `dorn_spell_pack.py`,
`approved_spell_pack.py`, `dorn_spells.py`, `session6_rewards.py`,
`backend/test_morthak_high_spells.py`, `test_dorn_approved_pack.py`,
`backend/scripts/run_sheet_test.py`, `frontend/src/components/DornSpellControls.tsx`,
`DornSpellEffects.tsx`, `frontend/tests/dorn-spells.test.cjs`,
`necromancer-spells.test.cjs`, `approved-spells-smoke.cjs`.
