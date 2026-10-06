# Estado observado — 2026-09-21

Canônico: `C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent`.
Monorepo: `C:\Users\delib\Desktop\OMNISVERA`.
Branch: `devin/create-omnisvera-class-standard`.
HEAD observado: `e0487839518ba9fc2ac23bb62ec7622beecc3aa1`.
Worktree dirty, incluindo trabalho anterior de App/observer, contest-replay,
Vault e mídia. Não incorporar, apagar ou commitar esses arquivos neste corte.

Backend FastAPI/SQLite: `backend/app`, testes `backend/test_*.py`.
Frontend React/Vite: `frontend/src`, testes Node `frontend/tests/*.test.cjs`.
Não há npm test; executar os arquivos por `node --test`.
TypeScript: `frontend/node_modules/typescript/bin/tsc --noEmit` via Node.
Build: `npm run build`; inspector verify usa outDir temporário para não alterar
o dist servido. Vite atual já tem publicDir=false para evitar copiar Godot.
Python disponível nesta inspeção: `.venv-observer/Scripts/python.exe`.
Dependências podem mudar: conferir inspection.json, não assumir este arquivo atual.

Existe `start_opencode.ps1`, mas inicia servidor web no checkout original e
carrega configuração local. Não é isolamento de ciclo e não será executado aqui.
AGENTS.md continua sendo autoridade para privacidade e checks do Companion.

Primeiro ciclo bloqueado até baseline limpa/versionada aprovada por Sage.
Não resolver esse bloqueio com commit automático nesta tarefa.

## Validação deste preparo

2026-09-21: 6 testes do mecanismo aprovados; verify confirmou backend 160/160,
frontend (9 arquivos Node), TypeScript e build PASS. Build em pasta temporária.
Fingerprint de código/configs principais preservado durante verify.
Sem ciclo OpenCode, commit, push, PR remoto, merge ou agendamento.
Resultados gerados em runtime/verification.json; reinspecionar antes de uso.
