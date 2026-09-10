# CF-01 — Confiabilidade da solicitação de rolagem

Validação: 27/08/2026. Base Git inspecionada: `5654810`, com worktree previamente modificado.

## Escopo e diagnóstico

Código executado confirmado: `omnisvera-agent/backend/.venv/Scripts/python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8787`.
Não se utilizou o `main` remoto antigo como descrição do produto em execução.

O fluxo já existia: `DiceTray` → `/gm/roll-requests` → SQLite → `/roll-requests` → `/roll-requests/{id}/complete` → evento/trigger do ledger.
`SessionWorkspace` já usa `connectSessionRealtime`; o backend observa a versão do ledger e sinaliza mudanças pelo WebSocket existente.

A hipótese de que o mestre **nunca** recebia o resultado automaticamente não se confirmou: no build anterior, o resultado chegou pela integração da Mesa. O defeito reproduzido na bandeja foi a ausência de atualização do histórico no seu próprio polling de 12 segundos, dependente de outra parte da UI para completar a sincronização.

Outros defeitos reproduzidos por regressões:

- Nova chave a cada retry de criação/conclusão, inclusive após perda da resposta.
- Dois callbacks antes do próximo render podiam enviar duas chamadas.
- Falha do refresh após conclusão bem-sucedida impedia anunciar o resultado.
- Autorização verificada somente depois dos caminhos de replay/recuperação.
- Chave de conclusão de uma rolagem livre podia vincular um resultado não relacionado ao pedido.

## Alterações

Somente dois arquivos de produção:

- `backend/app/dice_rolls.py`: autorização antes de replay/recuperação; conferência de `source/source_id` antes de vincular um evento recuperado.
- `frontend/src/components/DiceTray.tsx`: polling de pendências **e histórico** a cada 3 s, proteção contra respostas antigas e polling sobreposto em rede lenta; refresh ao retomar foco/conexão; erro de sincronização explícito; chave de conclusão estável derivada do pedido; retry de envio preservando a chave; bloqueio síncrono de cliques; resultado anunciado independentemente do refresh posterior.

O mestre continua autorizado a responder excepcionalmente. Seu botão passou a dizer **Rolar pelo jogador**, com aviso **Aguardando o jogador responder no próprio Companion**. Para o jogador permanece **Confirmar e rolar**.

Sem endpoints novos, sem migração de schema, sem alteração de regras de dados/atributos, sem Kernel ou novo transporte de realtime. O roster é carregado separadamente para sua indisponibilidade não bloquear pendências/histórico.

Arquivos novos:

- `backend/test_roll_requests.py`: 11 regressões de persistência, isolamento, cálculo, proveniência, replay, concorrência, recuperação e colisão de chaves.
- `frontend/tests/dice-tray.test.cjs`: 11 testes do componente compilado com TypeScript e hooks/API simulados, sem dependências novas. Não substituem o ensaio no navegador.
- `backend/scripts/cf01_probe.py`: reprodução por HTTP real, usando backup SQLite somente no diretório temporário e credenciais de teste somente em loopback.
- Este relatório.

## Evidência executada

1. Baseline backend antes das mudanças: **63/63**.
2. Novos testes inicialmente reproduziram **3 falhas backend** e **7 falhas frontend**. Os problemas do próprio harness encontrados durante sua criação foram corrigidos antes de usar essa reprodução como evidência.
3. Backend final: **74/74** (`backend/.venv/Scripts/python.exe -m unittest discover -s backend -p "test_*.py"`).
4. Frontend: **11/11** (`node --test tests/dice-tray.test.cjs`).
5. TypeScript: **passou** (`npx --no-install tsc --noEmit`).
6. Vite: **passou** (`npm run build`). Aviso de chunk acima de 500 kB no Three.js; não alterado neste corte.
7. `git diff --check` nos arquivos modificados: **passou**; Git avisou sobre normalização LF→CRLF no Windows.
8. HTTP real: GM/Varkh/Raziel autenticados; sem token rejeitado; jogador não cria pedido de mestre; Raziel não lista nem conclui pedido de Varkh; dificuldade oculta preservada; novo cliente recupera pendência.
9. Conexão TCP fechada imediatamente após enviar a conclusão, sem ler a resposta. Servidor concluiu; retry retornou o mesmo ID. Uma rolagem e um evento de ledger, inclusive após outra repetição. Outra chave não rolou novamente.
10. Navegador: três origens separadas, mestre/Varkh/Raziel; pedido criado pela UI, Varkh recarregou e concluiu, mestre recebeu sem atualizar manualmente, Raziel não viu pedido/resultado privado.

### Tempos

HTTP local, primeira execução (`request=5`, `roll=212`, IDs apenas do banco de ensaio):

| Marco | UTC |
|---|---|
| Criação persistida | 22:58:40.375079 |
| Visível pela API do jogador | 22:58:40.491489 |
| Envio da conclusão | 22:58:40.838437 |
| Conclusão persistida | 22:58:40.878946 |
| Visível pela API do mestre | 22:58:40.999593 |

Ensaio na interface, medido externamente pelas chamadas de automação (inclui latência da automação/observação, não é SLA nem tempo puro de rede):

- Build anterior: aviso ausente nas primeiras 25 leituras; presente na leitura seguinte, 18,172 s após o início do envio. Resultado observado no mestre em 7,034 s após o início do clique.
- Build corrigido: aviso observado em 6,066 s; resultado no mestre em 6,924 s. O intervalo configurado de polling é 3 s, mas a observação externa não comprova latência de tela de 3 s.
- Pedido UI final `id=7`, evento `214`: criado `23:02:21.760792Z`, concluído `23:03:17.156326Z` por `varkh`, fórmula `1d20-2`, dado `4`, total `2`, **um** evento de ledger. O intervalo contém a recarga e intervenções manuais do ensaio; não é atraso do servidor.

## Publicação local e segurança

Frontend servido: `index-B5pNAGF2.js`. Backend operacional reiniciado com o iniciador existente, preservando tokens/Tailscale; não havia jogadores online. O PC não foi reiniciado.
HTTPS Tailscale respondeu **200**, servindo o novo bundle. Uma checagem HTTPS dentro do sandbox falhou na autenticação TLS; repetida fora do sandbox, passou sem desabilitar validação de certificado.

Todos os pedidos fictícios ficaram na cópia temporária. Não houve escrita em notas canônicas, nem alteração de HP/inventário da campanha.

Abas e servidores do ensaio encerrados. `Stop-Process` apresentou erro interno do PowerShell; após reconferir os IDs e linhas de comando, os processos exclusivos do ensaio foram encerrados pela API de processos. Portas 8871/8872 fechadas; Companion/Tailscale na 8787 permaneceram ativos.

## Checkpoint e limites

Sem commit: os dois arquivos de produção já continham alterações anteriores não relacionadas. Elas foram preservadas, não incluídas em um commit supostamente exclusivo deste corte.
Checkpoint local ignorado pelo Git em `.assistant-runtime/checkpoints/CF-01-2026-08-27/`, com versões imediatamente **antes/depois** dos dois arquivos e cópias dos novos testes/harness/relatório. Não contém banco nem tokens. Para desfazer posteriormente, revisar o delta antes/depois e aplicar somente ele ao contrário; não sobrescrever arquivos que tenham recebido novas mudanças.

Não foi testado um celular físico nem a rede móvel fora de casa. O ensaio visual foi em navegadores desktop com identidades distintas; HTTP, perda de resposta e permissões foram testados separadamente. Queda abrupta do processo entre as etapas internas de conclusão não foi ensaiada neste corte. O caminho de recuperação com evento persistido foi testado.

Para testar como mestre: abrir uma ficha no header → **Bandeja de dados** → **Solicitar rolagem a um jogador** → selecionar Varkh/Carisma → enviar. No acesso individual de Varkh, abrir **Rolagem pedida** e **Confirmar e rolar**. Deixar o mestre aberto e conferir o resultado/registro. O atalho da bandeja no painel principal do mestre, sem abrir ficha, permanece fora deste corte.
