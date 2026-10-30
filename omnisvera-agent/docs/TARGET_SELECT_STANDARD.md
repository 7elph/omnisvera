# Seleção de alvos padronizada — 2026-10-08

Mísseis Mágicos, ataques de personagens, habilidades direcionadas, ataques de monstros/invocações/NPCs e Guarda reutilizam `TargetSelect`, um dropdown nativo junto à ação. Não existe mais o painel separado `workspace-attack-target-popover` na ficha. O navegador posiciona a lista em relação ao seletor (inclusive no mobile), não em outro ponto do workspace.

Selecionar ou limpar apenas muda a escolha local: executar ainda exige Usar/Atacar. Escolhas são independentes por ação. Alvos ausentes não continuam selecionados visualmente; não há execução sem alvo. Preservados modo/dados físicos, lâminas declaradas, bloqueios, orçamento de combate, filtros de alvo e autorização de cadáveres. Alvos múltiplos de magias de área continuam selecionados no próprio painel, sem converter a regra para alvo único. Nenhuma regra backend alterada.

Arquivos desta etapa:

- `frontend/src/components/TargetSelect.tsx`
- `frontend/src/components/SpellTargetControl.tsx`
- `frontend/src/components/MonsterAttackPanel.tsx`
- `frontend/src/components/DornProtocolControls.tsx`
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/styles.css`
- `frontend/tests/target-select.test.cjs`
- `frontend/tests/target-select-visual.cjs`
- `frontend/tests/combat-controls.test.cjs`
- `frontend/tests/summon-controls.test.cjs`
- `frontend/tests/raziel-vampire-powers.test.cjs`
- `frontend/tests/shared-attack-target.test.cjs`
- `frontend/tests/sheet-standard-visual.cjs`
- Este relatório.

Checks nesta execução: backend 392/392; frontend 161/161; TypeScript sem erros; builds isolado e servido concluídos, com aviso de tamanho de chunks; `git diff --check` sem erros. QA hidratado com renderizadores reais extraídos do workspace em desktop 1440×900 e mobile 390×844: seletores no card, escolhas independentes, seleção sem execução, d20 físico, cadáver autorizado/bloqueado, limpeza de alvo e nenhum overflow. Fixture de Dorn e renderizador de habilidades também passaram. Não equivale a prova de sessão multicliente em redes distintas.

Aplicado no frontend servido pelo Companion atual. Trabalho anterior preservado; sem commit, push, reset ou reinício do backend.
