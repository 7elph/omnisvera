# Magias e contadores — 2026-10-08

- Adaga de Osso aparece em Magias, removida dos cards e da contagem visual de Ataques. Continua usando o resolvedor existente (1d4, alvo, d20 físico/virtual, confirmação e orçamento de ação). A categoria técnica do backend foi preservada para não alterar regras de combate.
- Contadores de habilidades, recursos e magias ficam na mesma linha de ícone/nome. Seletores e botões permanecem abaixo, ocupando toda a largura. Forma da Noite segue com título acima dos controles, sem texto espremido.
- Lâmina de Sangue continua sem contador próprio; usa a Reserva de Sangue.

Arquivos alterados: `frontend/src/pages/SessionWorkspace.tsx`, `frontend/src/styles.css`, `frontend/tests/sheet-standard.test.cjs`, `frontend/tests/sheet-standard-visual.cjs` e este relatório.

Validação: 163 testes frontend aprovados, TypeScript e build aprovados; suite backend completa sem mudanças de regras; fixture com renderer real e CSS em desktop/390×844 confirma contadores ao lado, diálogo e ausência de overflow. Bundle servido confirmado por HTTPS. Sem gasto de recursos da campanha, commit ou push. Validação de mesa multicliente não realizada.
