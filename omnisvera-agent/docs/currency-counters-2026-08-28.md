# Contadores de moedas

Adicionados cobre, prata, ouro e platina às fichas Mesa e Ficha de jogo, usando os controles existentes de vida. Jogador só reduz o próprio saldo; mestre reduz ou aumenta. Digitação permite ajustes maiores e Aplicar persiste.

Ouro reutiliza `character_states.state_json.coins`. Os demais campos são `copper_coins`, `silver_coins`, `platinum_coins`, com leitura padrão zero para fichas antigas. Sem conversão automática de moedas, migração de itens do inventário ou alteração do sistema de loot. Nenhum saldo da campanha foi alterado.

Reutilizado `POST /characters/{id}/actions`, ação `set_currency`. Validação de permissão, inteiro não negativo, saldo anterior e transação SQLite impedem aumento pelo jogador, sobrescrita de saldo desatualizado e desconto repetido. Aplicação repetida do mesmo saldo é no-op, sem duplicar o evento. Histórico existente registra antes/depois.

## Arquivos

- Backend: `app/character_play.py`, `app/main.py`, `app/schemas.py`; novo `test_currency_counters.py`.
- Frontend: `src/api.ts`, `src/pages/SessionWorkspace.tsx`, `src/pages/PlayableCharacterSheet.tsx`; novos `src/components/CurrencyCounters.tsx` e `tests/currency-counters.test.cjs`.
- CSS existente preservado. Um ajuste de largura local impede que os quatro controles sejam comprimidos na grade de cards.

## Validação

- `.venv/Scripts/python.exe -m unittest discover -s . -p 'test_*.py' -q`: 106 aprovados (6 novos).
- `node --test tests/*.test.cjs`: 30 aprovados (4 novos).
- `npx --no-install tsc --noEmit`: aprovado.
- `npm run build`: aprovado; `index-C8hAH5qC.js`.
- Na cópia isolada: mestre alterou prata 0 → 10; jogador reduziu 10 → 9; mestre viu 9; tentativa de digitar 11 pelo jogador bloqueou Aplicar. Interface inspecionada no navegador.
- Um teste inicial falhou por usar Error de outro contexto JavaScript no mock; corrigido o ambiente do teste, sem enfraquecer a asserção. Todos passaram após correção.
- Warnings preservados: depreciação httpx/Starlette; bundle Three.js acima de 500 kB; Git LF/CRLF.
- Após reinício somente do Companion: saúde e ficha HTTP 200, os quatro campos presentes, link público HTTP 200 com build atual. Estados persistidos dos personagens idênticos ao backup.

## Recuperação

Worktree preexistente preservado; sem commit misturado ou push. Checkpoint antes/depois: `.assistant-runtime/checkpoints/currency-counters-2026-08-28/`. Backup SQLite íntegro: `.assistant-runtime/backups/companion-before-currency-20260828T194245.sqlite3`. Não sobrescrever trabalho posterior sem comparar.
