# CF-01 — revalidação com reconexão e latência

Base `5654810`, branch `devin/create-omnisvera-class-standard`, worktree misto. Este ensaio preserva as correções já descritas em `CF-01-roll-request-reliability.md`; não recria o fluxo nem modifica mais arquivos de produção do Companion.

## Ambiente

SQLite operacional copiado para diretório temporário por `scripts/cf01_probe.py prepare`. Servidores exclusivos loopback 8871/8872, credenciais públicas de fixture (nunca tokens reais), GM/Varkh/Raziel em origens separadas. Nenhuma rolagem fictícia foi gravada na campanha operacional.

Chrome desktop com viewport CSS verificado de **390×844**. Isto não é um navegador de celular real. Perda de conexão reproduzida encerrando apenas o servidor temporário do jogador e restaurando-o; mestre permaneceu conectado. Latência reproduzida com middleware exclusivo de ensaio: 3500 ms antes de responder a `/rolls` e `/roll-requests*`.

## Matriz

| Etapa | Resultado | Evidência |
|---|---|---|
| Mestre solicita | PASS | UI e HTTP, um pedido persistido por chave |
| Jogador correto recebe | PASS | Varkh vê pendência; dificuldade oculta |
| Jogador errado não recebe/conclui | PASS | Raziel sem pedido/resultado privado; conclusão 403 |
| Reload antes de responder | PASS | Pedido permanece após navegação/reabertura |
| Conexão perdida antes de responder | PASS | Erro visível, pedido continua pending |
| Reconexão | PASS | Polling recupera estado; retry conclui |
| Perda da resposta HTTP | PASS | Socket fechado após POST; resultado persistido recuperado por retry |
| Resposta/ownership/cálculo | PASS | Varkh, 1d20-2, vínculo request→roll→ledger |
| Duplo callback/clique | PASS automatizado | Dois callbacks no mesmo render enviam uma conclusão |
| Requests concorrentes/replay | PASS backend/HTTP | Uma rolagem; outra chave não conclui novamente |
| Mestre vê sem reload/Atualizar | PASS UI | Resultado e histórico chegaram com mestre aberto |
| Histórico persiste | PASS | Reload/API/SQLite reconciliados; um evento de ledger |
| Rede lenta acima do polling | PASS UI | 3500 ms por chamada; pedido e resultado chegam, sem starvation |
| Retorno de background/foco | PASS componente | Eventos visibilitychange/focus recuperam histórico/pendências |
| Celular físico/navegador mobile/4G | NÃO TESTADO | Não substituído por afirmação baseada no viewport |
| Suspensão real do navegador mobile em background | NÃO TESTADO | Somente simulação dos eventos do componente |

## Tempos (UTC, 28/08/2026)

### HTTP real com perda de resposta

Pedido 5, roll 212, um ledger:

- request_created_at: 00:15:08.805893
- player_api_visible_at: 00:15:08.916520
- player_sent_at: 00:15:09.283137
- server_completed_at: 00:15:09.319634
- gm_api_visible_at: 00:15:09.444298

Entrega pela API: 110,6 ms; envio→conclusão: 36,5 ms; conclusão→observação pela API mestre: 124,7 ms. Não são tempos de renderização.

### Interface 390×844, desconexão e retry

Pedido 6, `CF01 mobile reconnect 2120`, roll 213, total 10, um ledger:

- criado: 00:17:26.395948
- pedido observado na tela do jogador: 00:17:36.742
- clique externo de conclusão após reconexão: 00:19:31.337
- roll_created_at: 00:19:31.434865
- completed_at: 00:19:31.446951
- mestre observado com resultado: 00:19:34.826

Entrega observada ≤10,346 s; clique→roll aproximadamente 98 ms; roll→observação mestre ≤3,391 s. Os limites incluem o tempo entre comandos da automação; não são SLA nem medida exata da primeira pintura. O intervalo entre pedido e clique inclui reload e a desconexão deliberada.

### Interface com atraso de 3500 ms

Pedido 7, `CF01 slow 3500ms`, roll 214, total 16, um ledger:

- criado: 00:28:19.614161
- player_request_visible_at (observação): 00:28:32.532
- clique externo: 00:28:39.949
- server_received_completion_at (middleware): 00:28:42.526565
- roll_created_at: 00:28:46.103210
- completed_at: 00:28:46.130346
- resposta HTTP 200: 00:28:46.147415; duração do handler com atraso: 3620,85 ms
- mestre/jogador observados com resultado: 00:29:15.049; Raziel sem o rótulo privado

A última observação foi tardia por execução intercalada de ferramentas; não é evidência de atraso de 29 s do Companion. Este teste prova convergência sob latência, não uma janela máxima de entrega. O log não armazena headers, tokens ou corpo.

## Comandos e resultados

Executados na raiz, salvo frontend:

```powershell
omnisvera-agent/backend/.venv/Scripts/python.exe -m unittest discover -s omnisvera-agent/backend -p 'test_*.py'
omnisvera-agent/backend/.venv/Scripts/python.exe omnisvera-agent/backend/scripts/cf01_probe.py probe --database <fixture-temporaria> --port 8871
```

Backend **74 PASS**; probe HTTP **PASS**. No frontend:

```powershell
node --test tests/dice-tray.test.cjs
npx --no-install tsc --noEmit
npm run build
```

Frontend **13 PASS**, TypeScript **PASS**, Vite **PASS**. Primeira tentativa de build falhou por acesso negado do sandbox na leitura de diretório; repetida com permissão, passou. Aviso persistente de chunk Three.js acima de 500 kB (734,52 kB), sem alteração neste corte. Bundle `index-B5pNAGF2.js`.

`py_compile` do harness e `git diff --check`: PASS. Git avisa normalização LF→CRLF.

## Mudanças desta revalidação

- `frontend/tests/dice-tray.test.cjs`: dois testes adicionais, retorno de background e foco após falha; fixture expõe document.
- `backend/scripts/cf01_network_rehearsal.py`: servidor de ensaio somente loopback/SQLite temporário, atraso configurável e timestamps sanitizados.
- Este relatório.

Sem nova mudança de produção no Companion: polling combinado, chaves idempotentes, ownership e bloqueio de duplo clique já estavam implementados e foram preservados. O diagnóstico anterior não era ausência completa de realtime: a Mesa já tinha integração; a bandeja dependia dela para atualizar histórico.

## Checkpoint e limite

Checkpoint ignorado: `.assistant-runtime/checkpoints/reliability-2026-08-27/`, com teste antes/depois, harness, relatório e log sanitizado. O checkpoint CF-01 anterior continua preservado.

Sem commit do Companion: os arquivos de produção e os testes/harness anteriores já faziam parte do worktree misto; não foram apresentados como um commit limpo desta revalidação. A correção isolável do adapter MCP tem commit próprio.

Próxima validação única: repetir CF-01 no celular real, incluindo retorno da aba em background, antes de considerar CF-02. Nenhum Session Kernel, WebSocket novo, ataque paralelo, efeito ou economia foi implementado.
