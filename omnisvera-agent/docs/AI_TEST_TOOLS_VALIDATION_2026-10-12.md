# Ferramentas de teste para outras IAs — evidência

## Implementado e conectado

- `companion_test_capabilities`: discovery de atores, suite, política e limites.
- `companion_test_start`: início assíncrono, parâmetros restritos, recibo de request_id.
- `companion_test_status`: estado/verdict/report com schema estruturado.
- `opencode mcp list`: **companion-tests connected**, sem remover os outros servidores.
- Cliente SDK real → MCP stdio → runner → API nativa em fixture TEMP.

O cliente descobriu os três schemas, iniciou um ensaio, repetiu start com o
mesmo ID (mesmo run_id) e consultou até `COMPLETED/FAIL`. Poção de Vezemir PASS
e Anel Rúnico FAIL foram transmitidos no relatório. A falha conhecida não virou
erro de conexão nem foi escondida. O serviço de produção não foi reiniciado.
Um novo cliente/servidor stdio recuperou o mesmo recibo concluído, com mesmo
run_id, created_at e relatório, sem repetir o ensaio.

Checks finais: **backend 640/640** (14 testes novos), **frontend 245/245**,
typecheck, build e diff-check passaram. Smoke MCP real com reconexão passou.
Persistem avisos antigos de conexões SQLite/lifespan em fixtures e chunks
>500 kB no build; não houve refatoração fora de escopo para removê-los.

## Garantias cobertas pelos testes

Recibo único e conflito de parâmetros; serialização de jobs/servidores;
fonte e comando fixos; parâmetros sem code/SQL/URL/token; descoberta com schemas;
recibo concluído recuperado após reconnect; timeout e shutdown só do processo
criado; erro sem relatório; contagens incompatíveis e exit code divergente
rejeitados; path traversal na consulta e ator inválido rejeitados antes do spawn.

O corte não cria propostas/cenas, não importa PDFs, não instala conector
ChatGPT remoto e não certifica uma mesa real com redes distintas. Uma sessão
OpenCode já em execução pode precisar recarregar configuração; não foi enviada
mensagem a nenhuma IA nem interrompida conversa ativa. Ensaios estão em TEMP,
logs completos privados, sem tokens operacionais.

## Arquivos alterados neste corte

- `backend/scripts/agent_test_jobs.py`
- `backend/scripts/companion_test_mcp.py`
- `backend/scripts/agent_test_mcp_smoke.py`
- `backend/scripts/run_sheet_test.py` (destino novo de evidência TEMP)
- `backend/test_agent_test_tools.py`
- `opencode.json`
- `AGENTS.md`
- `docs/AI_TEST_TOOLS.md`
- `docs/AI_TEST_TOOLS_VALIDATION_2026-10-12.md`
- `docs/CURRENT_COMPANION_CODE.md`
- `docs/SHEET_TEST_RUNNER.md`
- `docs/AI_COMPANION_FOUNDATION.md`
- `docs/AI_COMPONENT_MAP.json`

Worktree misto preservado; sem staging/commit/push e sem edição de Vault,
Godot, mídia ou banco da mesa. Não atribuir outras alterações a este corte.
