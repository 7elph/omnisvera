# CA e moedas — ajuste visual

- Removido “Detalhar CA” e o ícone junto à armadura. CA total preservada, bônus numérico verde ao lado; componente compartilhado entre as fichas e a visualização do personagem no mapa.
- Moedas começam recolhidas abaixo do inventário, tanto na Mesa quanto na aba Inventário da Ficha de jogo. Saldos e permissões não foram alterados.
- Arquivos: `src/pages/SessionWorkspace.tsx`, `src/pages/PlayableCharacterSheet.tsx`, `src/components/CurrencyCounters.tsx`, novo `src/components/ArmorClassValue.tsx`, novo `tests/sheet-presentation.test.cjs` (todos em frontend).
- Validação: 106 testes backend, 32 frontend, TypeScript e build aprovados. Diff sem erros de whitespace. Avisos existentes de httpx/Starlette, bundle Three.js grande e LF/CRLF permanecem.
- Inspeção visual em cópia isolada: Morthak com CA 14 e +2 verde, sem botão; moedas fechadas imediatamente após inventário.
- Link público HTTP 200 servindo `index-UgEriqxd.js`. CSS compartilhado preservado. Sem alteração de backend/banco ou reinício do serviço principal.
- Checkpoint de arquivos antes/depois: `.assistant-runtime/checkpoints/ca-currency-layout-2026-08-28/`. Trabalho preexistente preservado; sem commit misturado ou push.
