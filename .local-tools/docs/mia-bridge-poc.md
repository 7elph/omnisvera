# MIA Bridge — Proof of Connection

Status: local Streamable HTTP proof of connection

The bridge is a separate launcher over the existing Omnisvera MCP Core Registry. It does not replace or modify the stdio launcher.

## Run locally

From the repository root:

```powershell
.\.omnisvera-tools\Scripts\python.exe .local-tools\mcp_http_server.py
```

Defaults:

- bind: `127.0.0.1`
- port: `8765`
- endpoint: `http://127.0.0.1:8765/mcp`
- transport: Streamable HTTP, stateless

The port may be changed with `OMNISVERA_MCP_HTTP_PORT`. The default host must remain loopback during this proof of connection.

## Remote allowlist

- `system.health`
- `get_handoff`
- `get_companion_state`

All three tools are annotated read-only. The bridge does not expose proposal creation, Vault audit, semantic search, shell access, writes, or any Companion mutation.

HTTP calls receive an internal context with:

- actor: `mia`
- client: `chatgpt-mia-bridge`
- transport: `streamable-http`

These fields are not accepted from MCP arguments and are recorded in the Core audit log.

## Local verification

```powershell
.\.omnisvera-tools\Scripts\python.exe .local-tools\tests\http_cold_start_smoke.py
```

The smoke test starts the HTTP process on a temporary loopback port, performs initialize, tools/list and tools/call, verifies that a forbidden tool is rejected, and checks the resulting audit identity.

## Security boundary

This PoC intentionally contains no public listener, tunnel, OAuth implementation, or embedded Cloudflare/ngrok configuration. Do not expose the unauthenticated localhost listener directly to the public internet. External connectivity and authentication are a separate operational step.
