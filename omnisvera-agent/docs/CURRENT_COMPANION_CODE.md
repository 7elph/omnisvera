# Companion atual — guia de código para revisão

## Localizar a versão correta

Repositório: `7elph/omnisvera`.
Branch publicada: `devin/create-omnisvera-class-standard`.
Diretório do aplicativo: `omnisvera-agent/`.

Não presuma que `main` contém a versão operacional mais recente. Confirme
branch e SHA antes de analisar, e use os arquivos reais como autoridade.
O repositório contém o código, não o banco operacional ou os tokens da mesa.
Publicar código não concede acesso ao Companion autenticado em execução.

## Pontos de entrada

| Área | Arquivos principais |
| --- | --- |
| Backend/API e autorização | `backend/app/main.py`, `backend/app/config.py` |
| Fichas, recursos e ações | `backend/app/character_play.py` |
| Progressão | `backend/app/level_advancement.py`, `backend/app/level_routes.py` |
| Ataques e confirmação | `backend/app/combat.py` |
| Turnos, efeitos e orçamento de ações | `backend/app/combat_effects.py` |
| DORN-7 | `backend/app/dorn_protocols.py`, `frontend/src/components/DornUnitIdentity.tsx` |
| Raziel | `backend/app/vampire_powers.py`, `backend/app/data/raziel_vampire_powers.json` |
| Invocações | `backend/app/summons.py`, `frontend/src/components/SummonControls.tsx` |
| Sessão, mapa e pins | `backend/app/session_workspace.py`, `frontend/src/pages/SessionWorkspace.tsx` |
| Ledger e realtime | `backend/app/session_ledger.py`, `backend/app/session_realtime.py` |
| Loot | `backend/app/loot.py` |
| Cliente HTTP e contratos TS | `frontend/src/api.ts` |
| Visual e responsividade | `frontend/src/styles.css` |
| Inicialização | `start_companion.ps1`, `start_backend.ps1` |
| Mantenedor manual | `scripts/companion_maintainer.py`, `.autonomy/` (estado histórico, não prova de execução atual) |

O frontend usa React/Vite e o backend FastAPI/SQLite. Testes estão em
`backend/test_*.py` e `frontend/tests/*.test.cjs`.

## Contratos que devem ser preservados

- Backend é autoridade de estado, permissões, recursos e resultados.
- Controle Mestre/Jogador e visibilidade de dados privados não podem regredir.
- Confirmações devem preservar os contratos existentes de idempotência.
- DORN-7 continua controlado pelo Mestre; Guarda, Vanguarda e Diagnóstico
  não concedem aumentos permanentes de atributos, PV ou economia de ações.
- Invocações usam a infraestrutura de combate existente, com controle pelo
  proprietário e ações no card/pin correspondente.
- Descrições de habilidades são acessíveis sem inflar os cards compactos.
- No mobile, a imagem inteira define a superfície do mapa e seus overlays.
- Não modificar Vault/canon, mídias, modelos ou Godot por consequência de
  uma tarefa restrita ao Companion.

## Verificação local

Na pasta `omnisvera-agent` e com dependências disponíveis:

```powershell
python -m unittest discover -s backend -p "test_*.py"
cd frontend
node --test tests/*.test.cjs
npx --no-install tsc --noEmit
npm run build
```

Na raiz Git: `git diff --check`.
Dependência indisponível significa INCONCLUSIVE, nunca PASS.
Teste com dados descartáveis; não usar credenciais ou banco real para QA.
Suíte verde não equivale a mesa multicliente em redes distintas comprovada.

## Pedir ajuda ao ChatGPT

Informe repositório, branch e SHA, e peça que a análise comece por este guia
e `AGENTS.md`, seguida dos componentes e testes da área solicitada.
O ChatGPT precisa de acesso GitHub autorizado ou dos arquivos fornecidos;
este documento não configura nem amplia permissões de contas.
Não compartilhar tokens da mesa para obter uma análise de código.

## Exclusões deliberadas

Tokens, `.env`, SQLite operacional, logs, backups, anexos, relatórios locais
de execução da autonomia e dependências instaladas não pertencem à publicação.
O Vault e a mídia externos ao Companion continuam fora deste corte.
