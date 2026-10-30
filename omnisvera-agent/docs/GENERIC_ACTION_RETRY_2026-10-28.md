# Retry de magias e ações genéricas — 28/10/2026

As duas rotas GM de conjuração do compêndio e ações usáveis de tokens aceitam
`request_id` opcional (1–120 caracteres: letras, números, ponto, sublinhado,
dois-pontos e hífen). Reenviar a mesma intenção com a mesma chave devolve o
resultado original, sem novos dados, dano, consumo de ação ou ledger.
Reutilizar a chave para outra intenção é rejeitado com HTTP 400. A autorização
GM continua sendo verificada antes do replay; entrada inválida recebe 422.

`spell_command_receipts.py` reutiliza `combat_effect_commands`, com namespace
próprio e intenção serializada estável. Não cria tabela, turno ou motor paralelo.
Há leitura antecipada antes de resolver ficha/nível/alvos e nova leitura após
`BEGIN IMMEDIATE` para serializar chamadas concorrentes. Dano, turno, ledger e
recibo são gravados na mesma transação. Erro desfaz o conjunto. Os recibos não
são apagados depois da confirmação.

No frontend, `writeJson` limita a espera a 30 s, sem reenviar automaticamente.
`commandRetry.ts` bloqueia clique simultâneo e mantém a chave após erro de
confirmação ou atualização da tela. Os fluxos cobertos são o compêndio, a
conjuração pelo grid, a ação usável e o seletor de grimório do monstro. Somente
depois de confirmar e sincronizar a tela uma nova ação recebe nova chave.

## Limites

- Clientes antigos sem chave mantêm o comportamento anterior; não ganham a
  garantia de replay. A rota agregadora `/gm/actions/execute` permanece legada.
- A atualização em `RECOVERY_DORN_CATALOG_2026-10-28.md` preserva a chave no
  reload da mesma aba. Fechar a aba ou mudar a intenção não é retry; não há
  outbox universal nem reenvio automático.
- Não muda regras, repertórios, recursos, efeitos ou condições de RPG. Magias
  ainda assistidas continuam assistidas; não é automação de todo o catálogo.
- Testes usam SQLite descartável e transporte simulado/in-process. Não provam
  aceitação visual nem estabilidade de mesa em redes diferentes.

## Validação

`test_generic_spell_retry.py` cobre replay, concorrência, colisão, mudança de
nível, remoção de entidades, rollback e orçamento do turno.
`test_generic_spell_retry_api.py` cobre as duas rotas HTTP, autorização e schema.
`generic-spell-retry.test.cjs` exercita os handlers reais com confirmação perdida,
clique duplo, falha de refresh e passagem da chave ao transporte limitado.
O harness de `combat-controls.test.cjs` carrega o helper real.

O OpenCode (`ollama/gpt-oss:120b-cloud`) analisou fontes sem ferramentas ou
acesso às fichas. A recomendação de apagar recibos foi rejeitada, assim como
ler somente antes do bloqueio: isso fragilizaria replay e concorrência.
Checks e situação da ativação ficam no recibo de entrega deste corte.

## Entrega validada

- Backend completo: 1.619 testes, OK, 1 skip; 46 testes focados também passaram.
- Frontend: 444/444; typecheck e build aprovados. O aviso de chunks grandes
  permanece. A primeira cópia de validação teve limitações de mídia/permissão
  e mocks antigos; o resultado acima é da suíte completa no projeto real.
- MCP `test-ac42644c346a456585ec8442ce79c187`: PASS, 89 cenários aprovados e
  2 bloqueios esperados (ataque à distância sem arma de Vezemir/Morthak).
  Os três scripts do lote `combat` passaram, com dez ações verificadas pela UI.
  Foram inspecionadas capturas das quatro fichas e amostras de efeitos.
  Há ícones quebrados de Dorn na fixture (Relâmpago/Adaga); mídia completa não
  foi certificada. Não é prova de celulares físicos nem de redes distintas.
- OpenCode: revisão de fontes concluída com `ollama/gpt-oss:120b-cloud`,
  32,34 s. Sua tentativa inicial de iniciar o ensaio respondeu apenas texto;
  foi rejeitada como evidência. O operador nativo realizou o ensaio, e depois
  o OpenCode consultou o recibo real via `companion-tests_companion_test_status`.
- Ativado: health e endereço público HTTP 200; schema com `request_id` ativo.
  JS `index-B-qrcn90.js`, CSS `index-D0RhnyB9.css`; chunks antigos preservados.
  Reinício somente do par verificado do backend 8787, com ambiente preservado.
- Backup: `C:\Users\delib\OmnisveraBackups\generic-action-retry-20261028-060516`.
  Comparação de 25 tabelas: fichas, inventários, acessos, sessão, combate,
  recibos e ledger preservados; somente timestamps de mapas variaram.
  OpenCode e demais conectores preservados; conector de testes reconectado.
- `certification_ready=false`: não certifica todas as ações ou o catálogo.
  Não houve staging, commit ou push; alterações anteriores foram preservadas.

## Arquivos deste corte

- Backend: `app/spell_engine.py`, `app/spell_command_receipts.py`,
  `app/schemas.py`, `app/main.py`, `test_generic_spell_retry.py`,
  `test_generic_spell_retry_api.py`.
- Frontend: `src/api.ts`, `src/commandRetry.ts`,
  `src/components/MonsterAttackPanel.tsx`, `src/components/CompendiumPanel.tsx`,
  `tests/generic-spell-retry.test.cjs`, `tests/combat-controls.test.cjs`.
- Documentação: este documento e `CURRENT_COMPANION_CODE.md`.
