# Magias usadas nas quatro fichas — 27/10/2026

Este corte usa os cards atuais de Vezemir, Raziel, Dorn e Morthak e as menções
no ledger técnico para priorizar. Menções incluem ensaios e eventos de uma
mesma ação; não são uma estatística de sessões canônicas.

## Correções

- Dissipar Magia usa card → pin no grid → confirmação única. Se houver várias
  magias, a escolha aparece dentro dessa confirmação, sem menu adicional no card.
  Cancelar não rola nem gasta. O servidor vincula efeito, pin, revisão e posições.
- Teia é um efeito de área com ocupantes derivados. Dissipar um ocupante resolve
  o efeito raiz e remove a área/penalidades de todos, se o teste tiver sucesso.
  O alcance é medido até a parte alcançável da área, não até o próprio Dorn,
  que apenas carrega o registro. O destaque no grid segue esse mesmo cálculo.
- A dissipação registra dado, bônus, dificuldade e consequência no ledger nativo.
  Repetição de request_id recupera o recibo sem custo ou rolagem adicional.
- Toque Sombrio marca o turno da vítima em cada efeito. Reentrada do hook no
  mesmo turno não rerrola o d6, inclusive quando o primeiro resultado não causa
  dano. Novo turno continua normalmente. Os efeitos permanecem no motor atual.
- Toque respeita a sobrevivência de Frenesi entre 0 e −9 PV; em −10 encerra.
  Ticks em NPC oculto ficam no registro privado do Mestre.
- Reflexos mantém os 90% já adotados pela campanha, agora também no contrato
  v2, descrição e efeito persistido. Dano de área e crítico inevitável conservam
  as exceções existentes. Nenhuma ficha real é migrada para testar isso.

## Cobertura e limites

Mísseis, Vinhas, Relâmpago, Velocidade, Força Arcana, regeneração e os demais
handlers nativos não foram substituídos. A suíte `active_spells` usa as quatro
fichas na fixture TEMP e separa cobertura de API de execução pela interface.
Apenas a execução e inspeção das capturas confirmam aceitação visual.

A seleção nova de dissipação usa pins vivos ocupando a área. Clicar diretamente
em uma área vazia ainda exige a futura seleção de células. Não implementa
paredes, visão, altura ou conversão automática das 854 entradas de catálogo.
Magias sem metadados arcanos de círculo/nível continuam bloqueadas para
Dissipar, conforme a regra já existente; não se inventa a dificuldade.

OpenCode recebeu sete trechos de código, sem dados operacionais e com ferramentas
negadas. A chamada foi recusada por `opencode_free_limit`; não foi repetida em
outro modelo para contornar a cota. Revisão e correções foram concluídas localmente.

## Validação

- Backend completo: **1594 testes OK, 1 skip**, em 675,5 s. Uma regressão
  adicional de borda da área e uma de resistência foram adicionadas depois;
  o módulo final teve **10/10 PASS**. Não somar os conjuntos sobrepostos.
- Frontend: **429/429 PASS**; typecheck e build finais PASS. O aviso de bundle
  maior que 500 kB permanece. CSS final limita os rádios a 18 px, com linha
  clicável de 40 px; o smoke verifica dimensões reais em ambas as larguras.
- Primeiro ensaio `test-7c0a93b0d18b45acb5d66cc55793df1d`: PASS funcional;
  revisão das capturas identificou seletores grandes. A correção visual foi
  compilada e o ensaio repetido, sem aumentar limites ou retirar cenários.
- Final `test-88fab4e1dc58444395c32d3d4d33799e`: **PASS**, quatro atores,
  `ui:true`, `ui_suite:active_spells`. Capturas 1440/390 inspecionadas e aceitas.
  Evidência TEMP: `omni-active-spells-tpzgEr/active-spell-effects-result.json`.
- No ensaio final, Dissipar rolou d20 12 (+5 =17) e d20 8 (+5 =13), contra
  dificuldade12: ambos removeram Teia e todos os ocupantes derivados. Falha
  legítima foi comprovada com RNG controlado no teste backend, preservando área,
  consumindo ação/uso e recuperando o mesmo recibo no retry.
- API de Velocidade (Vezemir), Regeneração (Raziel) e Mísseis (Morthak) passou
  com efeitos, dano/cura, custo e retry. As quatro identidades foram capturadas;
  isso não certifica todos os seus cards pela UI. Toque/Frenesi/privacidade são
  regressões backend determinísticas, não casos desta navegação visual.
- Ativado em27/10 às23:54 (São Paulo), backup
  `OmnisveraBackups/active-spells-activation-20261027-235441`.
  21 tabelas protegidas e tokens preservados; apenas timestamps de mapas
  mudaram, com todos os demais campos iguais. As cinco tabelas de fichas,
  inventário e notas também passaram na comparação por hash com o início
  desta tarefa. Nenhuma ação de teste usou as fichas operacionais.
- Verificação posterior: HTML/JS/CSS públicos HTTP200; contrato Reflexosv2/90%;
  Vezemir/Raziel/Morthak acessam a própria ficha como owner nível5. Dorn segue
  controlado pelo Mestre. OpenCode saudável e companion-tests conectado; os
  demais conectores não mudaram. Sem sessão ou combate ativos.
- Celular físico e jogadores em redes distintas continuam sem comprovação.
  Sem staging, commit ou push; branch/worktree misto preservados.


Arquivos principais: `spell_effect_runtime.py`, `dorn_spell_pack.py`,
`necromancer_spells.py`, `combat_effects.py`, `action_range.py`, `main.py`, contrato
em `data/dorn7_mage3.json`; `dispelTargetSelection.ts`, `DispelEffectOptions.tsx`,
`SessionWorkspace.tsx`, `api.ts` e descrição legada em `DornSpellControls.tsx`.

Registro de testes: `test_active_spell_effects.py`, `test_spell_dot_integrity.py`,
`dispel-target-selection.test.cjs` e `active-spell-effects-smoke.cjs`. O lote
foi registrado em `run_sheet_test.py`, `companion_test_mcp.py` e seu teste de
contrato. Integração visual usa o CSS compartilhado, sem alterar outros controles.
