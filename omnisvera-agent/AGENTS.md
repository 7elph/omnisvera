# OpenCode instructions — OMNISVERA Companion

## Escopo

Este diretório é o Companion web da campanha. O projeto é dividido em:

- `backend/`: FastAPI, SQLite, autenticação por token, fichas, sessão, ledger e realtime.
- `frontend/`: React/Vite, UI do Companion, ficha, mapa, dados 3D e runtime Godot embutido.
- `start_companion.ps1`: inicialização local do backend, frontend/runtime e túnel.

Não altere `CAMPANHA/`, `zz_media/`, `omnisvera-model/` ou o projeto Godot fora deste diretório sem pedido explícito. Não inclua tokens, bancos locais, logs, backups ou anexos em commits.

## Regras de implementação

1. Preserve a autenticação por token e a separação Mestre/Jogador.
2. Preserve a privacidade: dados privados do Mestre, objetivos ocultos e recompensas privadas não podem aparecer para jogadores.
3. O `session_ledger` mantém auditoria técnica; a interface deve mostrar narrativa legível, sem despejar JSON interno.
4. Prefira alterações pequenas, reversíveis e compatíveis com a UI atual.
5. Antes de mudar comportamento, procure testes existentes e adicione cobertura para a regra nova.
6. Não faça `git push` sem solicitação explícita.

## Checks obrigatórios

Backend:

```powershell
python -m unittest discover -s backend -p "test_*.py"
```

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

## Próxima fila aprovada

- Centralizar as ferramentas do Mestre em um único painel lateral.
- Criar o espaço de resumo da campanha com texto completo, resumo e mídia adicional.
- Adicionar camada de fog of war editável no mapa, com marcadores e persistência.
- Depois, adicionar grade tática configurável e snap opcional para personagens e inimigos.

Ao terminar uma tarefa, informe arquivos alterados, checks executados e riscos restantes.
