# Controles compactos nos cards — 2026-10-08

Seleção de alvo e Usar/Atacar ficam lado a lado em habilidades, Mísseis Mágicos, ataques e Guarda. Select ocupa o espaço restante; botão tem largura de conteúdo com mínimo 44px. Campos adicionais (lâminas, modo, d20 físico) mantêm linhas próprias quando necessários. Ataques usam o texto curto “Atacar”, preservando handler, dica, d20 e validações.

Cards continuam com altura natural, sem altura fixa que corte descrições/controles. Cards com campos extras podem ser mais altos. Contadores permanecem na linha dos ícones; seleção nunca executa automaticamente uma ação.

Arquivos: `frontend/src/styles.css`, `frontend/src/pages/SessionWorkspace.tsx`, `frontend/src/components/DornProtocolControls.tsx`; testes de combate/layout e fixtures visuais de alvos, magias e Dorn. Checks frontend completos, TypeScript e build; QA React real/CSS em desktop e 390×844, junto aos checks backend já aprovados neste turno. Nenhuma regra ou dado operacional alterado.
