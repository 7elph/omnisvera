# NPCs restritos ao painel do Mestre — 2026-10-08

Removida a ocorrência duplicada de `npcLibraryToggle` acima das fichas em `frontend/src/pages/SessionWorkspace.tsx`. O acesso continua exclusivamente em `renderGmWorkspaceTools`, na seção `master`, protegido pelo modo GM e pelo estado de abertura do painel.

Navegação das fichas continua fechando biblioteca de NPCs e ferramentas. Cadastro, inventário, histórico, permissões e fichas reservadas não foram alterados.

Cobertura em `frontend/tests/master-tools.test.cjs`: entrada única no painel, ausência sobre fichas, proteção Mestre/seção e fechamento ao selecionar ficha. Checks: suite backend completa, suite frontend, TypeScript e build. Sem commit, push ou reinício do backend; apenas atualização do frontend servido.

Em `frontend/src/styles.css`, apenas reordenadas propriedades dos controles de magia para manter compatibilidade com os testes existentes, sem mudança de layout ou valores.
