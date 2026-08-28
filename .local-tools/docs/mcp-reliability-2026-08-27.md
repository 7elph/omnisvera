# MCP — validação operacional de 27/08/2026

Base: branch `devin/create-omnisvera-class-standard`, commit `5654810142b125ece6f4701b255eca812cb0b506`, worktree misto previamente modificado. Nenhuma nota canônica, chave ou permissão alterada. MCP permanece read-only para o Companion. Horários abaixo em UTC (28/08; noite de 27/08 em São Paulo).

## Caminho observado

ChatGPT → plugin **Omnisvera MCP** (`asdk_app_6a8fedb4daf081918ec19171f3cd7653`) → serviço Secure MCP Tunnel da OpenAI → cliente local `tunnel-client-v0.0.13`, perfil `omnisvera-mia` → `http://127.0.0.1:8765/mcp` → Registry/Policy/handler → auditoria SQLite → resposta.

- Túnel do perfil: `tunnel_6a8fe7e703b08191b816cad825a6268d`; upstream local único, canal `main`. Metadados do túnel associam organização e workspace.
- Configuração local: `%APPDATA%/tunnel-client/omnisvera-mia.yaml`. Credencial carregada pelo iniciador de arquivo DPAPI ignorado pelo Git; seu valor não foi copiado para este relatório.
- `.local-tools/mcp_http_server.py`: FastMCP stateless, loopback, `/mcp`. O código local não exige `OpenAI-Organization`.
- Companion é outro serviço, porta 8787, exposto via Tailscale. Não é o túnel OpenAI do MCP.
- Stdio/OpenCode são outros clientes/transportes do Core; não foi encontrada uma segunda instância pública do bridge.
- A UI do ChatGPT também oferece uma integração antiga **OMNISVERA / teste de intgr**. A seleção explícita nesta validação foi sempre **Omnisvera MCP**. Não removemos a integração antiga.

## 401 e FORBIDDEN: resultados distintos

O erro informado `tunnel_active_organization_required` **não foi reproduzido**. Não há correção de 401 comprovada nesta entrega.

A conversa **Laboratório Pessoal**, mesmo com o plugin correto explicitamente selecionado, retornou para `system.health` e `memory.get(D-001)`:

`FORBIDDEN: This conversation does not support developer MCPs`

Essas tentativas não produziram novas entradas no audit local. A conversa **Recuperar memória D001** executou as mesmas ferramentas. Isso localiza o FORBIDDEN observado na autorização/disponibilidade do ChatGPT por conversa, antes do Core, não em uma rejeição do handler ou do Companion.

Não tivemos acesso aos headers de entrada do serviço OpenAI nem ao request original com 401. Portanto não é possível afirmar qual header/contexto mudou ou que refresh corrigiu definitivamente a organização. A documentação do [Secure MCP Tunnel](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) coloca o endpoint externo e sua associação organização/workspace na camada OpenAI; o processo loopback não consegue corrigir um pedido recusado antes de ser encaminhado.

Foi solicitado o link da conversa que retorna especificamente o 401. Não houve rotação de chave, header inventado, ampliação de permissões ou tentativa de contornar o bloqueio da conversa.

## Aceitação no ChatGPT

| Teste | Resultado/evidência |
|---|---|
| A: system.health repetido | PASS na conversa de controle; resposta e audit success |
| B: memory.get D-001 | PASS; conteúdo da decisão e duas fontes presentes |
| C: discovery | PASS; sete ferramentas na UI e no SDK |
| D: refresh do plugin e repetir A/B | PASS; observação 00:16:44Z; audit 00:16:47–51Z |
| E: reiniciar só túnel e repetir A/B | PASS; observação 00:12:52Z; audit 00:12:54/56Z |
| F: reiniciar só MCP e repetir A/B | PASS; observação 00:14:31Z; audit 00:14:33/35Z |
| Mesmos testes na conversa bloqueada | FAIL; FORBIDDEN explícito antes do túnel |
| Reproduzir e eliminar o 401 original | NÃO COMPROVADO |

Ferramentas: `system.health`, `get_handoff`, `get_companion_state`, `memory.get`, `memory.list`, `memory.search`, `memory.recent`. Discovery não significa chamada funcional de cada uma pelo ChatGPT; os testes de contratos cobrem os transportes separadamente.

Auditoria das chamadas reais: actor `mia`, client `chatgpt-mia-bridge`, transport `streamable-http`, resultado `success`. O smoke também produz intencionalmente um `memory.search` com `limit=0`, auditado como erro: não é falha de autenticação.

## CompanionAdapter: causa comprovada e correção mínima

O cliente tinha timeout de 1,5 s. `backend/app/main.py` aguarda até 1,5 s a sondagem opcional do Ollama antes de devolver `/health`. Com Ollama indisponível, o cliente desistia antes da resposta válida do Companion.

Medição com `.local-tools/diagnostics/companion_http_probe.py`, sem imprimir headers, corpo ou token:

| Endpoint | Medição |
|---|---|
| /health, limite 1,5 s | TCP 5,94 ms; timeout esperando headers em 1513,17 ms |
| /health, sonda independente limite 5 s | TCP 0,71 ms; headers 1530,50 ms; primeiro byte do corpo 1530,54 ms; total 1530,62 ms; 200 |
| /workspace | 26–57 ms; 200 |
| /gm/sessions | 26–30 ms; 200 |
| /scenes/active | 29–31 ms; 200 |

As duas sondas são medições independentes, não retry do adapter. O tempo era consumido antes dos headers, não no estabelecimento da conexão nem na leitura do corpo.

Mudança: apenas `get_health()` usa `max(timeout_configurado, 3.0)`. Demais leituras continuam com 1,5 s. Sem retry. Resultado real após a mudança: healthy em aproximadamente 1540 ms; pelo ChatGPT, `get_companion_state` respondeu healthy/fresh às 00:14:37Z. Ollama offline não é tratado como Companion offline.

## Testes e arquivos

- `.omnisvera-tools/Scripts/python.exe -m unittest discover -s .local-tools/tests -p 'test_*.py'`: **71 PASS**.
- Novos testes `test_companion_health_timeout.py`: antes da correção, 2 FAIL/1 PASS; depois, 3 PASS dentro da suíte. Cobre orçamento de health, outros endpoints inalterados, ausência de retry e sanitização de erro.
- `.omnisvera-tools/Scripts/python.exe .local-tools/tests/smoke_memory_recall.py`: cold-start stdio 11 tools, HTTP 7 tools, Policy/contratos, memória/fontes/estados inalterados, 8 eventos esperados: **PASS**. A primeira execução falhou na contagem do audit porque chamadas reais do ChatGPT ocorreram simultaneamente; repetição sem essas chamadas passou. Não foi alterado o teste para esconder a interferência.
- `tunnel-client doctor --profile omnisvera-mia --explain`: **PASS**; integração opcional do plugin Codex não instalada (SKIP). GET com 406 durante reachability não equivale a falha de tools/call.
- `py_compile` dos novos arquivos Python: **PASS**.
- `git diff --check`: **PASS**; avisos LF→CRLF do Git no Windows.

Arquivos deste corte: adapter `omnisvera_mcp/adapters/companion.py`, diagnóstico `diagnostics/companion_http_probe.py`, teste `tests/test_companion_health_timeout.py`, este relatório. Não houve alteração no bridge, no túnel, na chave ou nos contratos públicos.

Serviços reais foram mantidos online após reinícios seletivos. PC não reiniciado. O problema restante é obter/reproduzir o request exato com 401; não há evidência para alterar a autenticação local por tentativa.
